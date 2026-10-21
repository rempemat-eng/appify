import { Image, Pressable, ScrollView, View } from 'react-native';
import { BodyText } from '@/components/pixel-feedback';
import { PixelButton } from '@/components/game-ui';
import { FrameShape, frameTones } from '@/components/pixel-frame';
import {
  areaOf,
  hutBoxes,
  placeOf,
  hutDoors,
  hutPaths,
  keepsake,
  keepsakes,
  type DecorArea,
  type DecorCheck,
  type DecorPlacement,
  type HutLook,
} from '@/lib/decor';
import { artMaterials } from '@/lib/art-direction';
import { decorImages } from '@/lib/decor-assets';
import { decorSizes } from '@/lib/decor-sizes';
import { useGame } from '@/lib/game';

/** Each door's paint as the hut draws it (scripts/art/garden_props.py, HUT_DOORS). */
const DOOR_PAINT: Readonly<Record<string, string>> = {
  oak: artMaterials.wood[3],
  red: artMaterials.red[2],
  violet: artMaterials.nap[2],
  green: artMaterials.leaf[2],
} satisfies Record<HutLook['door'], string>;
const HUT_CHOICES = [
  { part: 'door', name: 'DOOR', options: hutDoors },
  { part: 'boxes', name: 'WINDOWS', options: hutBoxes },
  { part: 'path', name: 'PATH', options: hutPaths },
] as const;

/**
 * The hut's outside (coherence plan, B1): its door's paint, what grows in boxes under
 * its windows and the path up to its step, each a row of choices. All are open from the
 * start, free and instant; the hut changes at once in the garden behind the panel.
 */
function HutLookChoices() {
  const look = useGame((s) => s.hutLook);
  const setHutLook = useGame((s) => s.setHutLook);
  return (
    <View style={{ gap: 6 }}>
      <BodyText
        accessibilityRole="header"
        style={{ fontSize: 13, fontFamily: 'PixelifySans_700Bold' }}
      >
        THE HUT
      </BodyText>
      {HUT_CHOICES.map(({ part, name, options }) => (
        <View
          key={part}
          accessibilityRole="radiogroup"
          accessibilityLabel={`The hut's ${part === 'boxes' ? 'window boxes' : part}`}
          style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}
        >
          <BodyText style={{ width: 64, fontSize: 11, fontFamily: 'PixelifySans_700Bold' }}>
            {name}
          </BodyText>
          {options.map((option) => {
            const chosen = look[part] === option;
            return (
              <Pressable
                key={option}
                accessibilityRole="radio"
                accessibilityState={{ checked: chosen }}
                accessibilityLabel={`${option}${part === 'door' ? ' door' : ''}`}
                onPress={() => !chosen && setHutLook({ [part]: option })}
                style={{
                  flex: 1,
                  minHeight: 44,
                  paddingHorizontal: 4,
                  flexDirection: 'row',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 4,
                }}
              >
                <FrameShape tone={chosen ? frameTones.gold : frameTones.paper} unit={2} />
                {part === 'door' && (
                  <View
                    style={{
                      width: 8,
                      height: 12,
                      backgroundColor: DOOR_PAINT[option],
                      borderTopLeftRadius: 4,
                      borderTopRightRadius: 4,
                    }}
                  />
                )}
                <BodyText
                  numberOfLines={1}
                  style={{ fontSize: 10, fontFamily: 'PixelifySans_700Bold' }}
                >
                  {option.toUpperCase()}
                </BodyText>
              </Pressable>
            );
          })}
        </View>
      ))}
    </View>
  );
}

type Why = Exclude<DecorCheck, { ok: true }>['why'];
const WHY: Record<DecorArea, Record<Why, string>> = {
  hut: {
    wall: 'Not there: that is a wall or furniture.',
    crowded: 'Something already stands there.',
    spot: 'Keep room where your companion stands: the door, the bed, the hearth, the table, the chest.',
    'cut-off': 'That would close the way through the room.',
    unknown: 'That keepsake has not been found yet.',
  },
  garden: {
    wall: 'Not there: that is water, a bed of plants, a path across or something built.',
    crowded: 'Something already stands there.',
    spot: 'Keep room at the places your companion goes: the hut, the pond, the stall, the gate.',
    'cut-off': 'That would close a way through the garden.',
    unknown: 'That keepsake has not been found yet.',
  },
};
const WHERE: Record<DecorArea, { name: string; ground: string; tag: string }> = {
  hut: { name: 'IN THE HUT', ground: 'floor', tag: 'HUT' },
  garden: { name: 'IN THE GARDEN', ground: 'grass', tag: 'GARDEN' },
};

/**
 * Decorating the nap hut (C12): the keepsakes found so far, the ones still out in the
 * world as a "?" with the place that leaves them, and what to do next. Choose one, tap
 * the floor (the companion carries it there), then set it down; tap one in the room to
 * move it or put it away. Nothing here costs or grants anything.
 */
export function DecoratePanel({
  area,
  onArea,
  found,
  placed,
  selected,
  check,
  onSelect,
  onPlace,
  onStore,
  onDone,
  flipped = false,
  onFlip,
}: {
  /** where keepsakes are being set out now */
  area: DecorArea;
  /** go and decorate the other place */
  onArea: (area: DecorArea) => void;
  found: readonly string[];
  placed: readonly DecorPlacement[];
  /** the keepsake in hand, if any */
  selected: string | null;
  /** whether it may stand where it was last tapped (none until a tap) */
  check: DecorCheck | null;
  onSelect: (item: string | null) => void;
  onPlace: () => void;
  onStore: () => void;
  onDone: () => void;
  /** whether the keepsake in hand is turned to face the other way */
  flipped?: boolean;
  /** turn it (shown when the screen passes it) */
  onFlip?: () => void;
}) {
  const name = selected ? (keepsake(selected)?.name ?? selected).toLowerCase() : '';
  const isPlaced = !!selected && placed.some((p) => p.item === selected && areaOf(p) === area);
  const elsewhere = !!selected && placed.some((p) => p.item === selected && areaOf(p) !== area);
  const status = !selected
    ? `${found.length} of ${keepsakes.length} keepsakes found. Choose one, or tap one ${area === 'hut' ? 'in the room' : 'in the garden'} to move it.`
    : !check
      ? area === 'hut' && placeOf(selected) === 'surface'
        ? `Tap the floor, or the mantel, a sill, the bookcase, the counter or the table, where the ${name} goes.${elsewhere ? ' It comes from the garden.' : ''}`
        : `Tap the ${WHERE[area].ground} where the ${name} goes.${elsewhere ? ` It comes from ${area === 'hut' ? 'the garden' : 'the hut'}.` : ''}`
      : check.ok
        ? `The ${name} fits here.`
        : WHY[area][check.why];
  return (
    <View style={{ gap: 8 }}>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
        <BodyText
          accessibilityRole="header"
          style={{ flex: 1, fontSize: 16, fontFamily: 'PixelifySans_700Bold' }}
        >
          DECORATE
        </BodyText>
        <View style={{ width: 96 }}>
          <PixelButton small light label="DONE" onPress={onDone} />
        </View>
      </View>
      <View style={{ flexDirection: 'row', gap: 6 }}>
        {(['hut', 'garden'] as const).map((a) => (
          <Pressable
            key={a}
            accessibilityRole="tab"
            accessibilityState={{ selected: a === area }}
            accessibilityLabel={`Decorate ${a === 'hut' ? 'the hut' : 'the garden'}`}
            onPress={() => a !== area && onArea(a)}
            style={{ flex: 1, minHeight: 44, alignItems: 'center', justifyContent: 'center' }}
          >
            <FrameShape tone={a === area ? frameTones.leaf : frameTones.paper} unit={2} />
            <BodyText style={{ fontSize: 12, fontFamily: 'PixelifySans_700Bold' }}>
              {WHERE[a].name}
            </BodyText>
          </Pressable>
        ))}
      </View>
      <BodyText accessibilityLiveRegion="polite" style={{ fontSize: 13, lineHeight: 17 }}>
        {status}
      </BodyText>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={{ gap: 6 }}
      >
        {keepsakes.map((k) => {
          const open = found.includes(k.id);
          const chosen = k.id === selected;
          const at = placed.find((p) => p.item === k.id);
          const out = at ? WHERE[areaOf(at)].tag : null;
          const size = decorSizes[k.id];
          // the keepsake drawn at whole art pixels, as large as fits the tile
          const scale = Math.max(1, Math.floor(Math.min(40 / size.w, 34 / size.h)));
          return (
            <Pressable
              key={k.id}
              accessibilityRole="button"
              accessibilityLabel={
                open
                  ? `${k.name}${out ? `, set out in the ${out.toLowerCase()}` : ''}`
                  : `A keepsake not found yet, from ${k.from}`
              }
              accessibilityState={{ selected: chosen, disabled: !open }}
              disabled={!open}
              onPress={() => onSelect(chosen ? null : k.id)}
              style={{
                width: 72,
                minHeight: 84,
                padding: 6,
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <FrameShape tone={chosen ? frameTones.gold : frameTones.paper} unit={2} />
              <View style={{ height: 36, justifyContent: 'center' }}>
                {open ? (
                  <Image
                    source={decorImages[k.id]}
                    resizeMode="stretch"
                    // @ts-expect-error dataSet is a react-native-web prop (crisp pixel scaling)
                    dataSet={{ pixel: 'true' }}
                    style={{ width: size.w * scale, height: size.h * scale }}
                  />
                ) : (
                  <BodyText
                    style={{ fontSize: 22, fontFamily: 'PixelifySans_700Bold', opacity: 0.5 }}
                  >
                    ?
                  </BodyText>
                )}
              </View>
              <BodyText
                numberOfLines={2}
                style={{
                  fontSize: 10,
                  lineHeight: 12,
                  textAlign: 'center',
                  opacity: open ? 1 : 0.7,
                }}
              >
                {open ? (out ? `${k.name} · ${out}` : k.name) : k.from}
              </BodyText>
            </Pressable>
          );
        })}
      </ScrollView>
      {selected && (
        <View style={{ flexDirection: 'row', gap: 8 }}>
          <View style={{ flex: 1 }}>
            <PixelButton
              small
              label={isPlaced || elsewhere ? 'MOVE HERE' : 'SET IT HERE'}
              disabled={!check?.ok}
              onPress={onPlace}
            />
          </View>
          {onFlip && (
            <View style={{ flex: 1 }}>
              <PixelButton small light label={flipped ? 'TURN BACK' : 'TURN'} onPress={onFlip} />
            </View>
          )}
          {isPlaced && (
            <View style={{ flex: 1 }}>
              <PixelButton small light label="PUT AWAY" onPress={onStore} />
            </View>
          )}
        </View>
      )}
      {area === 'garden' && !selected && <HutLookChoices />}
    </View>
  );
}
