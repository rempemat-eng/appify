import { Modal, Pressable, ScrollView, View, useWindowDimensions } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Svg, { Rect } from 'react-native-svg';
import { cozy as c } from '@/lib/cozy';
import type { BreakIntention, CompanionMemory } from '@/lib/companion-memories';
import { gardenKeepsakes, memoryPlace } from '@/lib/garden-life';
import { CozyPanel, CozySheet } from '@/components/cozy-ui';
import { PixelButton } from '@/components/game-ui';
import { MemoryStamp } from '@/components/memory-stamp';
import { BodyText } from '@/components/pixel-feedback';
import { FrameFill } from '@/components/pixel-frame';

const keepsakes = [
  { intention: 'rest', name: 'Lantern', title: 'A quiet moment', tint: c.rest },
  { intention: 'read', name: 'Bookmark', title: 'A few pages', tint: c.sage },
  { intention: 'move', name: 'Leaf', title: 'A little movement', tint: c.sage },
  { intention: 'create', name: 'Sketch', title: 'Something you made', tint: c.amber },
] as const;

type OrnamentPixel = { key: string; x: number; y: number; color: string };
type PaintRect = (x: number, y: number, width: number, height: number, color: string) => void;
function paintOrnament(draw: (rect: PaintRect) => void): OrnamentPixel[] {
  const pixels = new Map<string, OrnamentPixel>();
  draw((left, top, width, height, color) => {
    for (let y = top; y < top + height; y++) {
      for (let x = left; x < left + width; x++) {
        const key = `${x}-${y}`;
        pixels.set(key, { key, x, y, color });
      }
    }
  });
  return [...pixels.values()];
}
const timber = { light: '#D6A76C', body: '#AD7D4B', shade: '#805535' };
const ornamentArt: Record<BreakIntention, readonly OrnamentPixel[]> = {
  rest: paintOrnament((r) => {
    r(2, 15, 12, 1, c.shadow);
    r(2, 2, 3, 12, c.ink);
    r(3, 3, 1, 10, timber.light);
    r(4, 3, 1, 10, timber.shade);
    r(2, 1, 11, 3, c.ink);
    r(3, 1, 9, 1, timber.light);
    r(3, 2, 9, 1, timber.body);
    r(3, 3, 2, 1, timber.shade);
    r(10, 4, 1, 2, c.ink);
    r(8, 6, 5, 7, c.ink);
    r(9, 7, 3, 4, '#DEA955');
    r(9, 7, 1, 3, '#FFF0B3');
    r(10, 8, 1, 2, '#FFF9D9');
    r(11, 9, 1, 2, '#C8873E');
    r(8, 6, 5, 1, '#B87947');
    r(9, 5, 3, 1, c.ink);
    r(9, 12, 3, 1, '#805535');
    r(2, 14, 5, 1, c.ink);
    r(2, 13, 3, 1, c.leafOutline);
    r(4, 12, 2, 1, c.positive);
    r(5, 13, 2, 1, c.leafOutline);
    r(3, 12, 1, 1, '#B2C780');
  }),
  read: paintOrnament((r) => {
    r(2, 15, 12, 1, c.shadow);
    r(6, 10, 3, 4, c.ink);
    r(7, 10, 1, 3, timber.light);
    r(3, 14, 9, 1, c.ink);
    r(4, 13, 7, 1, timber.body);
    r(2, 3, 12, 8, c.ink);
    r(1, 4, 1, 6, c.ink);
    r(3, 2, 4, 1, c.ink);
    r(8, 2, 5, 1, c.ink);
    r(2, 4, 5, 6, c.paper);
    r(8, 4, 5, 6, '#E8DABC');
    r(3, 3, 4, 1, c.highlight);
    r(8, 3, 5, 1, c.paper);
    r(3, 5, 3, 1, '#B7A788');
    r(3, 7, 3, 1, '#B7A788');
    r(3, 9, 2, 1, '#B7A788');
    r(9, 5, 3, 1, '#B7A788');
    r(9, 7, 3, 1, '#B7A788');
    r(10, 3, 2, 7, c.leafOutline);
    r(10, 3, 1, 6, c.positive);
    r(10, 10, 1, 1, c.leafOutline);
    r(2, 11, 11, 1, timber.shade);
    r(2, 10, 5, 1, '#B7844D');
    r(8, 10, 5, 1, timber.body);
  }),
  move: paintOrnament((r) => {
    r(2, 15, 12, 1, c.shadow);
    r(2, 1, 12, 13, c.ink);
    r(3, 1, 10, 1, timber.light);
    r(2, 2, 1, 11, timber.light);
    r(3, 2, 10, 11, timber.body);
    r(13, 2, 1, 12, timber.shade);
    r(3, 13, 10, 1, timber.shade);
    r(4, 3, 8, 9, '#E8DABC');
    r(4, 3, 7, 1, c.highlight);
    r(4, 4, 1, 7, c.paper);
    r(9, 4, 2, 2, c.leafOutline);
    r(7, 5, 4, 3, c.leafOutline);
    r(6, 6, 4, 3, c.leafOutline);
    r(5, 8, 3, 2, c.leafOutline);
    r(5, 10, 1, 1, '#805535');
    r(9, 5, 1, 1, '#B2C780');
    r(8, 6, 1, 1, c.positive);
    r(7, 7, 1, 1, '#B2C780');
    r(6, 8, 1, 1, c.positive);
    r(4, 2, 1, 1, c.ink);
    r(11, 12, 1, 1, c.ink);
    r(4, 14, 8, 1, timber.body);
  }),
  create: paintOrnament((r) => {
    r(1, 15, 14, 1, c.shadow);
    r(6, 1, 3, 13, c.ink);
    r(7, 1, 1, 11, timber.light);
    r(3, 10, 2, 5, c.ink);
    r(11, 10, 2, 5, c.ink);
    r(3, 11, 1, 3, timber.light);
    r(11, 11, 1, 3, timber.body);
    r(2, 2, 12, 10, c.ink);
    r(3, 3, 10, 8, '#E8DABC');
    r(3, 3, 9, 1, c.highlight);
    r(3, 4, 1, 6, c.paper);
    r(5, 5, 6, 4, '#8DAEA8');
    r(5, 6, 6, 1, '#BFD2BA');
    r(6, 5, 4, 1, '#BFD2BA');
    r(6, 8, 4, 1, '#688E88');
    r(8, 6, 2, 1, c.leafOutline);
    r(7, 7, 1, 1, c.positive);
    r(4, 9, 2, 1, '#B7A788');
    r(8, 9, 3, 1, '#B7A788');
    r(2, 11, 12, 1, timber.light);
    r(2, 12, 12, 1, timber.shade);
    r(12, 8, 1, 3, '#DEA955');
    r(12, 7, 1, 1, c.ink);
    r(2, 14, 3, 1, timber.light);
    r(11, 14, 3, 1, timber.shade);
  }),
};

/** A passive 16-pixel ornament. The parent owns positioning and interaction. */
export function GardenKeepsakeArt({
  intention,
  size = 48,
}: {
  intention: BreakIntention;
  size?: number;
}) {
  return (
    <View
      aria-hidden
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
      style={{ width: size, height: size, pointerEvents: 'none' }}
    >
      <Svg width={size} height={size} viewBox="0 0 16 16">
        {ornamentArt[intention].map((pixel) => (
          <Rect key={pixel.key} x={pixel.x} y={pixel.y} width={1} height={1} fill={pixel.color} />
        ))}
      </Svg>
    </View>
  );
}

export type GardenKeepsakeShelfProps = {
  memories: readonly CompanionMemory[];
  onOpen: (memory: CompanionMemory) => void;
};

export function GardenKeepsakeShelf({ memories, onOpen }: GardenKeepsakeShelfProps) {
  const latest = gardenKeepsakes(memories);
  const saved = keepsakes.filter((keepsake) => latest[keepsake.intention]);
  return (
    <CozyPanel style={{ padding: 12, gap: 8 }}>
      <BodyText style={{ fontSize: 13, fontFamily: 'PixelifySans_700Bold' }}>
        Little reminders
      </BodyText>
      {saved.length ? (
        <>
          <BodyText style={{ fontSize: 12, lineHeight: 18 }}>
            Keepsakes from your breaks, tucked into the garden.
          </BodyText>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
            {saved.map((keepsake) => {
              const memory = latest[keepsake.intention]!;
              return (
                <Pressable
                  key={memory.id}
                  accessibilityRole="button"
                  accessibilityLabel={`Open ${keepsake.name.toLowerCase()} memory with ${memory.companion.name}`}
                  accessibilityHint={`Displayed at the ${memoryPlace(memory.intention).label.toLowerCase()}`}
                  onPress={() => onOpen(memory)}
                  style={({ pressed }) => ({
                    minHeight: 44,
                    minWidth: 112,
                    flexBasis: '21%',
                    flexGrow: 1,
                    flexDirection: 'row',
                    justifyContent: 'center',
                    alignItems: 'center',
                    gap: 7,
                    padding: 8,
                    opacity: pressed ? 0.8 : 1,
                  })}
                >
                  {({ pressed }) => (
                    <>
                      <FrameFill fill={pressed ? c.sage : c.paper} outline={c.outline} />
                      <MemoryStamp intention={keepsake.intention} size={24} />
                      <BodyText
                        style={{
                          fontSize: 12,
                          fontFamily: 'PixelifySans_700Bold',
                          flexShrink: 1,
                          textAlign: 'center',
                        }}
                      >
                        {keepsake.name}
                      </BodyText>
                    </>
                  )}
                </Pressable>
              );
            })}
          </View>
        </>
      ) : (
        <View style={{ gap: 8 }}>
          <BodyText style={{ fontSize: 12, lineHeight: 18 }}>
            Bring back a bookmark, leaf, lantern or sketch from a break. Keep only the moments you
            want to remember.
          </BodyText>
        </View>
      )}
    </CozyPanel>
  );
}

export type GardenKeepsakeSheetProps = {
  memory: CompanionMemory | null;
  onClose: () => void;
  onJournal: () => void;
};

function fullMemoryDate(timestamp: number) {
  const date = new Date(timestamp);
  return Number.isNaN(date.getTime())
    ? 'A saved break'
    : date.toLocaleDateString('en-GB', {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
        year: 'numeric',
      });
}

export function GardenKeepsakeSheet({ memory, onClose, onJournal }: GardenKeepsakeSheetProps) {
  const { height } = useWindowDimensions();
  const insets = useSafeAreaInsets();
  const keepsake = memory ? keepsakes.find((item) => item.intention === memory.intention) : null;
  if (!memory || !keepsake) return null;
  return (
    <Modal visible transparent animationType="none" onRequestClose={onClose}>
      <View
        style={{
          flex: 1,
          justifyContent: 'flex-end',
          backgroundColor: c.shadow,
          paddingHorizontal: 16,
          paddingTop: insets.top + 16,
          paddingBottom: insets.bottom + 16,
        }}
      >
        <CozySheet
          key={memory.id}
          style={{
            alignSelf: 'center',
            width: '100%',
            maxWidth: 608,
            maxHeight: Math.max(180, height - insets.top - insets.bottom - 32),
            gap: 12,
          }}
        >
          {memory && keepsake && (
            <>
              <ScrollView
                style={{ flexShrink: 1 }}
                contentContainerStyle={{ alignItems: 'center', gap: 12, paddingBottom: 4 }}
              >
                <View
                  style={{
                    width: 112,
                    height: 112,
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <FrameFill fill={keepsake.tint} outline={c.outline} inset />
                  <GardenKeepsakeArt intention={memory.intention} size={80} />
                </View>
                <BodyText
                  accessibilityRole="header"
                  style={{
                    fontSize: 20,
                    lineHeight: 27,
                    fontFamily: 'PixelifySans_700Bold',
                    textAlign: 'center',
                  }}
                >
                  {keepsake.title}
                </BodyText>
                <BodyText style={{ textAlign: 'center', fontSize: 14 }}>
                  With {memory.companion.name}
                </BodyText>
                <BodyText style={{ textAlign: 'center', fontSize: 12, lineHeight: 18 }}>
                  {fullMemoryDate(memory.completedAt)}
                </BodyText>
                <View
                  style={{
                    alignSelf: 'stretch',
                    padding: 12,
                    gap: 5,
                    backgroundColor: c.sage,
                    borderRadius: 0,
                  }}
                >
                  <BodyText style={{ fontSize: 11, fontFamily: 'PixelifySans_700Bold' }}>
                    IN YOUR GARDEN
                  </BodyText>
                  <BodyText style={{ fontSize: 13, fontFamily: 'PixelifySans_700Bold' }}>
                    {memoryPlace(memory.intention).label}
                  </BodyText>
                  <BodyText style={{ fontSize: 12, lineHeight: 18 }}>
                    {memoryPlace(memory.intention).description}
                  </BodyText>
                </View>
                <BodyText style={{ textAlign: 'center', fontSize: 12, lineHeight: 18 }}>
                  A memory you chose to keep. Self-reported, with no extra rewards or stats.
                </BodyText>
              </ScrollView>
              <PixelButton
                small
                light
                label="OPEN MEMORY ALBUM"
                onPress={() => {
                  onClose();
                  onJournal();
                }}
              />
              <PixelButton small label="DONE" onPress={onClose} />
            </>
          )}
        </CozySheet>
      </View>
    </Modal>
  );
}
