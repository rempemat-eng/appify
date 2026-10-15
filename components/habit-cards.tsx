import { useEffect, useState } from 'react';
import { FlatList, Pressable, View, useWindowDimensions } from 'react-native';
import Svg, { Rect } from 'react-native-svg';
import Animated, {
  FadeIn,
  useAnimatedStyle,
  useReducedMotion,
  useSharedValue,
  withDelay,
  withTiming,
} from 'react-native-reanimated';
import { cards, cardIds, cardPower, cardDetails, type CardId } from '@/lib/cards';
import { feedback, palette as c, useGame, missions, type Player } from '@/lib/game';
import { EnergyPips, PixelButton, PixelText } from '@/components/game-ui';
import { BodyText } from '@/components/pixel-feedback';

const art: Record<CardId, string[]> = {
  stretch: [
    '............',
    '.....ii.....',
    '....ipii....',
    '.....ii.....',
    '..iiiigiii..',
    '.....ig.....',
    '.....ig.....',
    '....i..i....',
    '...i....i...',
    '..ii....ii..',
    '............',
    '............',
  ],
  deep_breath: [
    '............',
    '...iii......',
    '..ipppi.....',
    '...iii......',
    '....i.......',
    '..iigii..s..',
    '..igggi.ss..',
    '..igggi..s..',
    '...iii......',
    '..ii.ii.....',
    '............',
    '............',
  ],
  glass_of_water: [
    '............',
    '............',
    '..iiiiiiii..',
    '..ippppppi..',
    '..ipsspspi..',
    '..issssssi..',
    '..issssssi..',
    '...issssi...',
    '...issssi...',
    '...iiiiii...',
    '............',
    '............',
  ],
  short_walk: [
    '............',
    '............',
    '.....ii.....',
    '....ippi....',
    '...ippii....',
    '...ippii....',
    '..ipppppi...',
    '.ipppppppi..',
    '.iiiiiiiii..',
    '............',
    '..g..g..g...',
    '............',
  ],
  morning_walk: [
    '....g.......',
    '..g.g.g.....',
    '...ggg......',
    '..ggggg.....',
    '...ggg......',
    '............',
    '.....ii.....',
    '....ippi....',
    '...ipppppi..',
    '..ipppppppi.',
    '..iiiiiiiii.',
    '............',
  ],
  read_a_chapter: [
    '............',
    '............',
    '.iiii..iiii.',
    '.ipppiipppi.',
    '.ipppiipppi.',
    '.ipppiipppi.',
    '.ipppiipppi.',
    '.ipppiipppi.',
    '.iiiiiiiiii.',
    '.....ii.....',
    '............',
    '............',
  ],
  early_night: [
    '.......ss...',
    '......ss....',
    '.....ss.....',
    '.....sss....',
    '......sss...',
    '..iiii......',
    '..ippi......',
    '..iiiiiiii..',
    '.ippppppppi.',
    '.iiiiiiiiii.',
    '.i........i.',
    '............',
  ],
  call_a_friend: [
    '............',
    '..iii..iii..',
    '.ipppiipppi.',
    '.ipppiipppi.',
    '..iii..iii..',
    '...i....i...',
    '.iigiiiigii.',
    '.igggiigggi.',
    '..igi..igi..',
    '..i.i..i.i..',
    '............',
    '............',
  ],
  digital_sunset: [
    '............',
    '............',
    '....gggg....',
    '...gggggg...',
    '..gggggggg..',
    '..gggggggg..',
    'iiiiiiiiiiii',
    '....ssss....',
    '..ssssssss..',
    'ssssssssssss',
    '............',
    '............',
  ],
};
function Illustration({ id }: { id: CardId }) {
  const colors: Record<string, string> = { i: c.ink, p: c.body, g: c.positive, s: c.slate };
  const pixels: { x: number; y: number; color: string }[] = [];
  for (let y = 0; y < art[id].length; y++) {
    const row = art[id][y];
    for (let x = 0; x < row.length; x++) {
      if (row[x] !== '.') pixels.push({ x, y, color: colors[row[x]] });
    }
  }
  return (
    <Svg width={36} height={36} viewBox="0 0 12 12">
      {pixels.map((pixel) => (
        <Rect
          key={`${pixel.x}-${pixel.y}`}
          x={pixel.x}
          y={pixel.y}
          width={1}
          height={1}
          fill={pixel.color}
        />
      ))}
    </Svg>
  );
}
export function HabitCard({
  id,
  count,
  selected = false,
  disabled = false,
  onPress,
  species,
  guided = false,
}: {
  id: CardId;
  guided?: boolean;
  count?: number;
  selected?: boolean;
  disabled?: boolean;
  onPress?: () => void;
  species?: Player['species'];
}) {
  const card = cards[id];
  const effect =
    species && card.power > 0 && card.habit === species
      ? card.effect.replace(String(card.power), String(cardPower(id, species)))
      : card.effect;
  const face = (
    <View
      style={{
        minHeight: 158,
        borderWidth: 2,
        borderColor: guided || selected ? c.moss : c.ink,
        backgroundColor: guided ? c.amber : c.paper,
        padding: 5,
        gap: 4,
        alignItems: 'center',
      }}
    >
      <View
        style={{
          flexDirection: 'row',
          width: '100%',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <EnergyPips value={card.cost} />
        <BodyText style={{ fontSize: 11, color: c.ink }}>
          {count === undefined ? card.rarity[0] : `X${count}`}
        </BodyText>
      </View>
      <Illustration id={id} />
      <BodyText
        style={{
          width: '100%',
          textAlign: 'center',
          fontFamily: 'Inter_600SemiBold',
          fontSize: 11,
          lineHeight: 15,
          minHeight: 45,
        }}
      >
        {card.name}
      </BodyText>
      <BodyText
        style={{
          width: '100%',
          textAlign: 'center',
          fontSize: 11,
          lineHeight: 16,
          fontFamily: 'Inter_600SemiBold',
        }}
      >
        {effect}
      </BodyText>
    </View>
  );
  return (
    <Animated.View
      entering={FadeIn.duration(150)}
      style={{
        flex: 1,
        transform: [{ translateY: selected ? -10 : 0 }],
      }}
    >
      {onPress ? (
        <Pressable
          accessibilityRole="button"
          accessibilityState={{ disabled, selected }}
          accessibilityLabel={`${card.name}, ${card.cost} energy, ${cardDetails[id]}${species ? (selected ? ', tap again to play' : ', tap to select') : ', show details'}`}
          onPress={onPress}
          disabled={disabled}
        >
          {face}
        </Pressable>
      ) : (
        face
      )}
    </Animated.View>
  );
}
export function RewardCard({ id, index }: { id: CardId; index: number }) {
  const progress = useSharedValue(0);
  const reduced = useReducedMotion();
  useEffect(() => {
    progress.set(
      withDelay(reduced ? 0 : index * 240, withTiming(1, { duration: reduced ? 120 : 380 })),
    );
  }, [index, progress, reduced]);
  const style = useAnimatedStyle(() => ({
    opacity: progress.value,
    transform: [
      { perspective: 700 },
      { rotateY: `${(1 - progress.value) * (reduced ? 0 : 90)}deg` },
    ],
  }));
  return (
    <Animated.View style={[{ flex: 1 }, style]}>
      <HabitCard id={id} />
    </Animated.View>
  );
}
export function DeckPanel({ reward = false }: { reward?: boolean }) {
  const p = useGame((s) => s.player)!;
  const [selected, setSelected] = useState<CardId | null>(null);
  const earned = useGame((s) => s.cardReward);
  const ids = reward && earned ? earned.cards : cardIds.filter((id) => p.deck.includes(id));
  const mission = missions.find((m) => m.id === earned?.mission);
  const { width } = useWindowDimensions();
  const columns = width < 360 ? 2 : 3;
  return (
    <View style={{ flex: 1, backgroundColor: c.paper, padding: 16, gap: 16 }}>
      <PixelText style={{ fontSize: 16, lineHeight: 28 }}>
        {reward && earned
          ? `+${ids.length} ${ids.length === 1 ? 'CARD' : 'CARDS'} FROM ${earned.minutes} MIN OFFLINE`
          : `MY DECK · ${p.deck.length}/20`}
      </PixelText>
      {reward ? (
        mission && <BodyText>{mission.name}</BodyText>
      ) : (
        <BodyText>EARN CARDS BY BEING OFFLINE. 15 MIN = 1 CARD.</BodyText>
      )}
      <FlatList
        key={columns}
        data={ids}
        numColumns={columns}
        keyExtractor={(id, index) => `${id}-${index}`}
        columnWrapperStyle={{ gap: 8 }}
        contentContainerStyle={{ gap: 12, paddingVertical: 8 }}
        renderItem={({ item, index }) => (
          <View style={{ flex: 1, maxWidth: `${100 / columns}%` }}>
            {reward ? (
              <RewardCard id={item} index={index} />
            ) : (
              <HabitCard
                id={item}
                count={p.deck.filter((id) => id === item).length}
                selected={selected === item}
                onPress={() => {
                  setSelected(selected === item ? null : item);
                  feedback('select');
                }}
              />
            )}
          </View>
        )}
      />
      {!reward && selected && (
        <BodyText>
          {cards[selected].rarity} · {cardDetails[selected]}
        </BodyText>
      )}
      <PixelButton
        label={reward ? 'KEEP GROWING' : 'DONE'}
        onPress={() => {
          useGame.getState().dismissCards();
          feedback('select');
        }}
      />
    </View>
  );
}
