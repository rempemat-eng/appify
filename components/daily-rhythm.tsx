import { useCallback, useEffect, useRef, useState } from 'react';
import {
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Switch,
  TextInput,
  View,
  useWindowDimensions,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Moon, Sun, Sprout } from 'lucide-react-native';
import { CozyPanel, CozySheet } from '@/components/cozy-ui';
import { PixelButton } from '@/components/game-ui';
import { BodyText } from '@/components/pixel-feedback';
import { cozy as c } from '@/lib/cozy';
import { gameLayout } from '@/lib/layout';
import {
  RHYTHM_STORAGE_KEY,
  deviceTimezone,
  durationLabel,
  freshRhythm,
  groupLabels,
  nextTimeLabel,
  ownTimeMinutes,
  periodLabels,
  plannedMinutes,
  restoreRhythm,
  rhythmGroups,
  rhythmPeriods,
  rhythmStatus,
  validateRhythm,
  type DailyRhythm,
  type PlannedPeriod,
  type RhythmGroup,
  type RhythmPeriod,
  type RhythmWindow,
} from '@/lib/daily-rhythm';

const periodColors: Record<RhythmPeriod, string> = { rest: c.rest, focus: c.focus, own: c.sage };

function RhythmIcon({ period, size = 18 }: { period: RhythmPeriod; size?: number }) {
  const Icon = period === 'rest' ? Moon : period === 'focus' ? Sun : Sprout;
  return <Icon size={size} color={c.ink} strokeWidth={2} />;
}

export function DailyRhythmCard({
  active,
  open,
  onOpenChange,
  showCard = true,
}: {
  active: boolean;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** The game menu opens the planner without showing the summary card. */
  showCard?: boolean;
}) {
  const [plan, setPlan] = useState(freshRhythm);
  const [loaded, setLoaded] = useState(false);
  const [loadError, setLoadError] = useState(false);
  const [now, setNow] = useState(Date.now);
  const mounted = useRef(false);
  const load = useCallback(async () => {
    try {
      const raw = await AsyncStorage.getItem(RHYTHM_STORAGE_KEY);
      const saved = raw === null ? freshRhythm() : restoreRhythm(JSON.parse(raw));
      if (!saved) throw new Error('Invalid rhythm');
      if (mounted.current) {
        setPlan(saved);
        setLoaded(true);
      }
    } catch {
      if (mounted.current) setLoadError(true);
    }
  }, []);
  useEffect(() => {
    mounted.current = true;
    // Begin hydration after mounting; all UI updates follow the storage result.
    void Promise.resolve().then(load);
    return () => {
      mounted.current = false;
    };
  }, [load]);
  useEffect(() => {
    if (!active || open || !loaded || !plan.enabled) return undefined;
    // Refresh on return before resuming the visible planner's clock.
    const refresh = setTimeout(() => setNow(Date.now()), 0);
    const timer = setInterval(() => setNow(Date.now()), 30000);
    return () => {
      clearTimeout(refresh);
      clearInterval(timer);
    };
  }, [active, open, loaded, plan.enabled]);

  const status = rhythmStatus(plan, now);
  const period = status.current ?? 'own';
  return (
    <>
      {showCard && (
        <CozyPanel style={{ padding: 12, gap: 7 }}>
          <View style={styles.cardRow}>
            <View style={[styles.icon, { backgroundColor: periodColors[period] }]}>
              <RhythmIcon period={period} />
            </View>
            <View style={{ flex: 1, gap: 2 }}>
              <BodyText style={styles.bold}>Your rhythm</BodyText>
              <BodyText style={styles.caption}>
                {loadError
                  ? 'Your saved planner could not load.'
                  : !loaded
                    ? 'Loading your local plan…'
                    : plan.enabled && status.current
                      ? `${periodLabels[status.current]} now${status.next ? ` · ${periodLabels[status.next.period]} ${nextTimeLabel(status.next.at, now)}` : ''}`
                      : 'An optional plan for rest, focus and your own time.'}
              </BodyText>
            </View>
            {loaded && (
              <Pressable
                accessibilityRole="button"
                accessibilityLabel={
                  plan.enabled ? 'Edit your daily rhythm' : 'Set up your daily rhythm'
                }
                disabled={!active}
                onPress={() => onOpenChange(true)}
                style={styles.edit}
              >
                <BodyText style={[styles.bold, { color: c.moss }]}>
                  {plan.enabled ? 'Edit' : 'Set up'}
                </BodyText>
              </Pressable>
            )}
          </View>
          {loaded && plan.enabled && (
            <BodyText style={styles.caption}>
              Planning only · follows your device’s local time
            </BodyText>
          )}
          {loadError && (
            <>
              <BodyText style={styles.caption}>
                Your garden is safe. Retry loading, or start a new planner and save it to replace
                only your rhythm settings.
              </BodyText>
              <View style={styles.actions}>
                <View style={styles.action}>
                  <PixelButton
                    label="RETRY"
                    small
                    light
                    onPress={() => {
                      setLoadError(false);
                      void load();
                    }}
                  />
                </View>
                <View style={styles.action}>
                  <PixelButton
                    label="NEW PLAN"
                    small
                    light
                    onPress={() => {
                      setPlan(freshRhythm());
                      onOpenChange(true);
                    }}
                  />
                </View>
              </View>
            </>
          )}
        </CozyPanel>
      )}
      {open && (
        <RhythmEditor
          initial={plan}
          replacing={loadError}
          onClose={() => onOpenChange(false)}
          onSaved={(saved) => {
            setPlan(saved);
            setLoaded(true);
            setLoadError(false);
            setNow(Date.now());
            onOpenChange(false);
          }}
        />
      )}
    </>
  );
}

function RhythmEditor({
  initial,
  replacing,
  onClose,
  onSaved,
}: {
  initial: DailyRhythm;
  replacing: boolean;
  onClose: () => void;
  onSaved: (plan: DailyRhythm) => void;
}) {
  const [draft, setDraft] = useState(initial);
  const [group, setGroup] = useState<RhythmGroup>('weekdays');
  const [submitted, setSubmitted] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(false);
  const insets = useSafeAreaInsets();
  const { height } = useWindowDimensions();
  const issues = validateRhythm(draft);
  const update = (period: PlannedPeriod, patch: Partial<RhythmWindow>) => {
    setSaveError(false);
    setDraft((value) => ({
      ...value,
      [group]: { ...value[group], [period]: { ...value[group][period], ...patch } },
    }));
  };
  const save = async () => {
    setSubmitted(true);
    setSaveError(false);
    if (issues.length || saving) return;
    setSaving(true);
    try {
      await AsyncStorage.setItem(RHYTHM_STORAGE_KEY, JSON.stringify(draft));
      onSaved(draft);
    } catch {
      setSaveError(true);
      setSaving(false);
    }
  };

  return (
    <Modal
      visible
      transparent
      animationType="none"
      onRequestClose={() => {
        if (!saving) onClose();
      }}
    >
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={[
          styles.backdrop,
          {
            paddingTop: insets.top + gameLayout.gutter,
            paddingBottom: insets.bottom + gameLayout.gutter,
          },
        ]}
      >
        <CozySheet
          style={{
            width: '100%',
            maxWidth: gameLayout.maxWidth - gameLayout.gutter * 2,
            maxHeight: height - insets.top - insets.bottom - gameLayout.gutter * 2,
            padding: gameLayout.gutter,
            gap: 12,
          }}
        >
          <View style={styles.cardRow}>
            <View style={{ flex: 1, gap: 3 }}>
              <BodyText accessibilityRole="header" style={[styles.bold, { fontSize: 20 }]}>
                Your daily rhythm
              </BodyText>
              <BodyText style={styles.caption}>Make room for the life outside your phone.</BodyText>
            </View>
            <Switch
              value={draft.enabled}
              disabled={saving}
              accessibilityLabel="Enable daily rhythm planning"
              onValueChange={(enabled) => setDraft((value) => ({ ...value, enabled }))}
              trackColor={{ false: c.faded, true: c.positive }}
              thumbColor={c.highlight}
            />
          </View>
          <ScrollView
            keyboardShouldPersistTaps="handled"
            contentContainerStyle={{ gap: 12, paddingBottom: 4 }}
          >
            <BodyText style={styles.caption}>
              {draft.enabled ? 'Planning is on.' : 'Planning is off until you enable it and save.'}{' '}
              This does not block apps, measure sleep or phone use, or change demo rewards. You can
              still play and take a break whenever you like.
            </BodyText>
            {replacing && (
              <BodyText style={[styles.caption, { color: c.danger }]}>
                Saving replaces the unreadable rhythm settings only. Your garden progress is
                unchanged.
              </BodyText>
            )}
            <View accessibilityRole="tablist" style={styles.segments}>
              {rhythmGroups.map((key) => (
                <Pressable
                  key={key}
                  accessibilityRole="tab"
                  accessibilityState={{ selected: group === key }}
                  aria-selected={group === key}
                  disabled={saving}
                  onPress={() => setGroup(key)}
                  style={[
                    styles.segment,
                    group === key && { backgroundColor: c.sage, borderColor: c.moss },
                  ]}
                >
                  <BodyText style={styles.bold}>{groupLabels[key]}</BodyText>
                </Pressable>
              ))}
            </View>
            <BodyText style={styles.caption}>
              {group === 'weekdays' ? 'Monday–Friday' : 'Saturday–Sunday'} · use 24-hour HH:MM.
              Overnight windows belong to the day they start.
            </BodyText>
            {rhythmPeriods.map((period) => {
              const window = draft[group][period];
              return (
                <View
                  key={period}
                  style={[
                    styles.window,
                    { backgroundColor: period === 'rest' ? '#F0EAF7' : '#FBF0D8' },
                  ]}
                >
                  <View style={styles.cardRow}>
                    <RhythmIcon period={period} />
                    <View style={{ flex: 1, gap: 2 }}>
                      <BodyText style={styles.bold}>{periodLabels[period]}</BodyText>
                      <BodyText style={styles.caption}>
                        {period === 'rest'
                          ? 'Space to wind down and rest.'
                          : 'For work, study or whatever needs your attention.'}
                      </BodyText>
                    </View>
                    <Switch
                      value={window.enabled}
                      disabled={saving}
                      accessibilityLabel={`${groupLabels[group]} ${periodLabels[period]} window`}
                      onValueChange={(enabled) => update(period, { enabled })}
                      trackColor={{ false: c.faded, true: c.positive }}
                      thumbColor={c.highlight}
                    />
                  </View>
                  {window.enabled ? (
                    <>
                      <View style={styles.times}>
                        {(['start', 'end'] as const).map((field) => (
                          <View key={field} style={{ flex: 1, gap: 5 }}>
                            <BodyText style={styles.caption}>
                              {field === 'start' ? 'From' : 'Until'}
                            </BodyText>
                            <TextInput
                              value={window[field]}
                              editable={!saving}
                              onChangeText={(value) => update(period, { [field]: value })}
                              accessibilityLabel={`${groupLabels[group]} ${periodLabels[period]} ${field} time, HH:MM`}
                              placeholder={field === 'start' ? '23:00' : '07:00'}
                              placeholderTextColor={c.shade}
                              autoCorrect={false}
                              autoCapitalize="none"
                              maxLength={5}
                              selectTextOnFocus
                              style={styles.input}
                            />
                          </View>
                        ))}
                      </View>
                      <BodyText style={styles.caption}>
                        {durationLabel(plannedMinutes(window))} planned
                        {window.end < window.start ? ' · ends the following day' : ''}
                      </BodyText>
                    </>
                  ) : (
                    <BodyText style={styles.caption}>
                      No {periodLabels[period].toLowerCase()} window on these days.
                    </BodyText>
                  )}
                </View>
              );
            })}
            <View style={[styles.window, { backgroundColor: c.sage }]}>
              <View style={styles.cardRow}>
                <RhythmIcon period="own" />
                <BodyText style={[styles.bold, { flex: 1 }]}>Own time</BodyText>
                <BodyText style={styles.bold}>
                  {durationLabel(ownTimeMinutes(draft[group]))}
                </BodyText>
              </View>
              <BodyText style={styles.caption}>
                Everything outside Rest and Focus. Adjust either window to make more room for your
                own time.
              </BodyText>
            </View>
            <BodyText style={styles.caption}>
              Saved on this device only · {deviceTimezone().replace(/_/g, ' ')}. Your plan follows
              local time when you travel or the clocks change. These are planned hours, not measured
              sleep.
            </BodyText>
            {submitted &&
              issues.map((issue) => (
                <BodyText key={issue} accessibilityLiveRegion="polite" style={{ color: c.danger }}>
                  {issue}
                </BodyText>
              ))}
            {saveError && (
              <BodyText accessibilityLiveRegion="polite" style={{ color: c.danger }}>
                Could not save your rhythm. Your previous plan is unchanged. Keep this open and try
                Save again, or cancel to leave it unchanged.
              </BodyText>
            )}
          </ScrollView>
          <View style={styles.actions}>
            <View style={styles.action}>
              <PixelButton label="CANCEL" light disabled={saving} onPress={onClose} />
            </View>
            <View style={styles.action}>
              <PixelButton
                label={saving ? 'SAVING…' : 'SAVE PLAN'}
                disabled={saving}
                onPress={() => void save()}
              />
            </View>
          </View>
        </CozySheet>
      </KeyboardAvoidingView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  bold: { fontFamily: 'PixelifySans_700Bold' },
  caption: { fontSize: 12, lineHeight: 17 },
  cardRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  icon: { width: 36, height: 36, alignItems: 'center', justifyContent: 'center', borderRadius: 0 },
  edit: { minWidth: 48, minHeight: 44, alignItems: 'center', justifyContent: 'center' },
  actions: { flexDirection: 'row', gap: 10 },
  action: { flex: 1 },
  backdrop: {
    flex: 1,
    paddingHorizontal: gameLayout.gutter,
    backgroundColor: c.shadow,
    justifyContent: 'flex-end',
    alignItems: 'center',
  },
  segments: { flexDirection: 'row', gap: 8 },
  segment: {
    flex: 1,
    minHeight: 44,
    borderRadius: 0,
    borderWidth: 1,
    borderColor: c.stone,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: c.paper,
  },
  window: { padding: 12, gap: 10, borderRadius: 0, borderWidth: 1, borderColor: c.stone },
  times: { flexDirection: 'row', gap: 12 },
  input: {
    minHeight: 48,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 0,
    borderWidth: 1,
    borderColor: c.outline,
    backgroundColor: c.highlight,
    color: c.ink,
    fontFamily: 'PixelifySans_700Bold',
    fontSize: 18,
  },
});
