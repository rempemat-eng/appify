import { Pressable, View } from 'react-native';
import Svg, { Rect } from 'react-native-svg';
import { cozy as c } from '@/lib/cozy';
import type {
  BreakCompanion,
  BreakIntention,
  CompanionMemory,
  CompanionMemoryOffer,
} from '@/lib/companion-memories';
import { CozyPanel } from '@/components/cozy-ui';
import { PixelButton } from '@/components/game-ui';
import { BodyText } from '@/components/pixel-feedback';

const intentions = [
  { id: 'rest', label: 'Rest', keepsake: 'lantern', title: 'A quiet moment' },
  { id: 'read', label: 'Read', keepsake: 'bookmark', title: 'A few pages' },
  { id: 'move', label: 'Move', keepsake: 'leaf', title: 'A little movement' },
  { id: 'create', label: 'Create', keepsake: 'sketch', title: 'Something you made' },
] as const;

// Small paper keepsakes share the garden's native grid and upper-left light.
// These are decorative SVG pixels, rather than another interactive pet.
const keepsakePixels: Record<BreakIntention, readonly string[]> = {
  rest: [
    '................',
    '......ooo.......',
    '.....o...o......',
    '.....o...o......',
    '....ooooooo.....',
    '....owyyyyo.....',
    '....owyhyyo.....',
    '....owhhhyo.....',
    '....owyhyyo.....',
    '....owyyyso.....',
    '....oyyysoo.....',
    '....ooooooo.....',
    '.....ossoo......',
    '....ooooooo.....',
    '................',
    '................',
  ],
  read: [
    '................',
    '....ooooooo.....',
    '....owwwhho.....',
    '....owwhhho.....',
    '....ohhhhho.....',
    '....ohhhhho.....',
    '....ohgggso.....',
    '....ohhghso.....',
    '....ohhhhso.....',
    '....ohhhhso.....',
    '....ohhhhso.....',
    '....ohhohso.....',
    '....oho.oso.....',
    '....oo...oo.....',
    '................',
    '................',
  ],
  move: [
    '................',
    '.........ooo....',
    '.......oolgo....',
    '.....oollggo....',
    '....ollglggo....',
    '...ollglggso....',
    '...olglggso.....',
    '...oggllgso.....',
    '...ogglgso......',
    '....ogso........',
    '....ogo.........',
    '...ogo..........',
    '..ooo...........',
    '................',
    '................',
    '................',
  ],
  create: [
    '................',
    '..ooooooooo.....',
    '..owwwwwhho.....',
    '..owhhhhhho.....',
    '..owhggghho.....',
    '..ohglhlhho.....',
    '..ohgglghho.oo..',
    '..ohhghhhhooyyo.',
    '..ohhhhhhooyyso.',
    '..ohhhhooyysoo..',
    '..ohhhooyyso....',
    '..ohhooyyso.....',
    '..oooossoo......',
    '....ooo.........',
    '................',
    '................',
  ],
};
const keepsakePalette: Record<string, string> = {
  o: c.ink,
  w: c.highlight,
  h: c.paper,
  s: c.stone,
  y: c.amber,
  l: c.positive,
  g: c.leafOutline,
};
function stampPixels(rows: readonly string[]) {
  return rows.flatMap((row, y) =>
    Array.from(row).flatMap((color, x) =>
      color === '.' ? [] : [{ key: `${x}-${y}`, x, y, color: keepsakePalette[color] }],
    ),
  );
}
const keepsakeArt = {
  rest: stampPixels(keepsakePixels.rest),
  read: stampPixels(keepsakePixels.read),
  move: stampPixels(keepsakePixels.move),
  create: stampPixels(keepsakePixels.create),
};

function MemoryStamp({ intention, size = 32 }: { intention: BreakIntention; size?: number }) {
  return (
    <View
      aria-hidden
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
      pointerEvents="none"
    >
      <Svg width={size} height={size} viewBox="0 0 16 16">
        {keepsakeArt[intention].map((pixel) => (
          <Rect key={pixel.key} x={pixel.x} y={pixel.y} width={1} height={1} fill={pixel.color} />
        ))}
      </Svg>
    </View>
  );
}

export type BreakIntentionPickerProps = {
  value: BreakIntention | null;
  onChange: (value: BreakIntention | null) => void;
  disabled?: boolean;
};

export function BreakIntentionPicker({
  value,
  onChange,
  disabled = false,
}: BreakIntentionPickerProps) {
  const choiceStyle = (selected: boolean, pressed: boolean) => ({
    minHeight: 44,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: selected ? c.leafOutline : c.outline,
    backgroundColor: selected ? c.sage : c.paper,
    opacity: disabled ? 0.55 : pressed ? 0.75 : 1,
    paddingHorizontal: 10,
    paddingVertical: 7,
    gap: 8,
  });
  return (
    <CozyPanel style={{ padding: 12, gap: 10 }}>
      <BodyText style={{ fontFamily: 'Nunito_800ExtraBold', fontSize: 13 }}>
        A little break idea
      </BodyText>
      <BodyText style={{ fontSize: 12, lineHeight: 18 }}>
        Optional. Choose what suits you; there is no target to meet.
      </BodyText>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Just a break, no activity intention"
        accessibilityState={{ selected: value === null, disabled }}
        disabled={disabled}
        onPress={() => onChange(null)}
        style={({ pressed }) => ({
          ...choiceStyle(value === null, pressed),
          alignItems: 'center',
          justifyContent: 'center',
        })}
      >
        <BodyText style={{ fontFamily: 'Nunito_800ExtraBold', fontSize: 13 }}>
          Just a break
        </BodyText>
      </Pressable>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
        {intentions.map((intention) => (
          <Pressable
            key={intention.id}
            accessibilityRole="button"
            accessibilityLabel={`${intention.label} break idea`}
            accessibilityState={{ selected: value === intention.id, disabled }}
            disabled={disabled}
            onPress={() => onChange(intention.id)}
            style={({ pressed }) => ({
              ...choiceStyle(value === intention.id, pressed),
              flexDirection: 'row',
              alignItems: 'center',
              justifyContent: 'center',
              flexGrow: 1,
              flexBasis: '45%',
            })}
          >
            <MemoryStamp intention={intention.id} size={24} />
            <BodyText style={{ fontFamily: 'Nunito_800ExtraBold', fontSize: 13 }}>
              {intention.label}
            </BodyText>
          </Pressable>
        ))}
      </View>
    </CozyPanel>
  );
}

export type MemoryReflectionProps = {
  offer: CompanionMemoryOffer;
  onKeep: () => void;
  onSkip: () => void;
  disabled?: boolean;
};

export function MemoryReflection({
  offer,
  onKeep,
  onSkip,
  disabled = false,
}: MemoryReflectionProps) {
  const intention = intentions.find((item) => item.id === offer.intention)!;
  return (
    <CozyPanel style={{ padding: 14, gap: 10 }}>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
        <View
          style={{
            width: 48,
            height: 48,
            borderWidth: 1,
            borderColor: c.outline,
            borderRadius: 10,
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: c.sage,
          }}
        >
          <MemoryStamp intention={offer.intention} />
        </View>
        <View style={{ flex: 1, minWidth: 0, gap: 3 }}>
          <BodyText style={{ fontSize: 11, fontFamily: 'Nunito_800ExtraBold' }}>
            A MEMORY TO KEEP?
          </BodyText>
          <BodyText style={{ fontFamily: 'Nunito_800ExtraBold', fontSize: 14 }}>
            Did you make time to {intention.id}?
          </BodyText>
        </View>
      </View>
      <BodyText style={{ fontSize: 13, lineHeight: 19 }}>
        Keep a {intention.keepsake} in {offer.companion.name}&apos;s album if you&apos;d like to
        remember it.
      </BodyText>
      <BodyText style={{ fontSize: 11, lineHeight: 17 }}>
        Optional and self-reported. This adds a memory, with no extra rewards.
      </BodyText>
      <PixelButton small label="KEEP THIS MEMORY" disabled={disabled} onPress={onKeep} />
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Skip this memory"
        accessibilityState={{ disabled }}
        disabled={disabled}
        onPress={onSkip}
        style={({ pressed }) => ({
          minHeight: 44,
          alignItems: 'center',
          justifyContent: 'center',
          borderRadius: 10,
          borderWidth: 1,
          borderColor: c.outline,
          backgroundColor: c.paper,
          opacity: disabled ? 0.55 : pressed ? 0.75 : 1,
        })}
      >
        <BodyText style={{ fontFamily: 'Nunito_800ExtraBold', fontSize: 12 }}>SKIP</BodyText>
      </Pressable>
    </CozyPanel>
  );
}

export type CompanionMemoriesProps = {
  memories: readonly CompanionMemory[];
  companionKey?: BreakCompanion['key'];
  companionName?: string;
  limit?: number;
};

function memoryDate(timestamp: number) {
  const date = new Date(timestamp);
  return Number.isNaN(date.getTime())
    ? 'Saved break'
    : date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
}

export function CompanionMemories({
  memories,
  companionKey,
  companionName,
  limit = 3,
}: CompanionMemoriesProps) {
  const album = memories
    .filter((memory) => companionKey === undefined || memory.companion.key === companionKey)
    .sort((a, b) => b.completedAt - a.completedAt || b.recordedAt - a.recordedAt);
  const count = Number.isFinite(limit) ? Math.max(1, Math.min(5, Math.floor(limit))) : 3;
  const shown = album.slice(0, count);
  return (
    <CozyPanel style={{ padding: 14, gap: 12 }}>
      <View style={{ gap: 3 }}>
        <BodyText style={{ fontFamily: 'Nunito_800ExtraBold', fontSize: 13 }}>
          {companionName ? `${companionName}'s memory album` : 'Your memory album'}
        </BodyText>
        <BodyText style={{ fontSize: 12, lineHeight: 18 }}>
          Small moments you chose to remember together.
        </BodyText>
      </View>
      {shown.length === 0 ? (
        <BodyText style={{ fontSize: 12, lineHeight: 18 }}>
          No memories yet. Choose an optional break idea, then keep a memory when you return.
        </BodyText>
      ) : (
        <View style={{ gap: 12 }}>
          {shown.map((memory) => {
            const intention = intentions.find((item) => item.id === memory.intention)!;
            return (
              <View key={memory.id} style={{ flexDirection: 'row', gap: 12, alignItems: 'center' }}>
                <View
                  style={{
                    width: 44,
                    height: 48,
                    borderRadius: 8,
                    borderWidth: 1,
                    borderColor: c.outline,
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: c.body,
                  }}
                >
                  <MemoryStamp intention={memory.intention} />
                </View>
                <View style={{ flex: 1, minWidth: 0, gap: 2 }}>
                  <BodyText style={{ fontFamily: 'Nunito_800ExtraBold', fontSize: 13 }}>
                    {intention.title}
                  </BodyText>
                  <BodyText style={{ fontSize: 12, lineHeight: 18 }}>
                    With {memory.companion.name} · {memoryDate(memory.completedAt)}
                  </BodyText>
                  <BodyText style={{ fontSize: 11, lineHeight: 16 }}>Your reflection</BodyText>
                </View>
              </View>
            );
          })}
        </View>
      )}
      {album.length > shown.length && (
        <BodyText style={{ fontSize: 11, lineHeight: 17 }}>
          Latest {shown.length} of {album.length} memories
        </BodyText>
      )}
    </CozyPanel>
  );
}
