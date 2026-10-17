import { useEffect, useState } from 'react';
import { FlatList, Pressable, View, useWindowDimensions } from 'react-native';
import Svg, { Rect } from 'react-native-svg';
import Animated, {
  cancelAnimation,
  useAnimatedStyle,
  useSharedValue,
  withDelay,
  withSpring,
  withTiming,
} from 'react-native-reanimated';
import { LinearGradient } from 'expo-linear-gradient';
import { Zap } from 'lucide-react-native';
import { useReducedMotion } from '@/lib/motion';
import { cards, cardIds, cardPower, cardDetails, type CardId } from '@/lib/cards';
import { feedback, useGame, missions, type Player } from '@/lib/game';
import { cozy as c, panelStyle } from '@/lib/cozy';
import { CozyBackground, PaperFinish } from '@/components/cozy-ui';
import { PixelButton, PixelText } from '@/components/game-ui';
import { BodyText } from '@/components/pixel-feedback';
import { cardIllustrations } from '@/lib/card-art';
export function CardIllustration({ id }: { id: CardId }) {
  return (
    <Svg width={48} height={48} viewBox="0 0 16 16">
      {cardIllustrations[id].map((pixel) => (
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
  count?: number;
  selected?: boolean;
  disabled?: boolean;
  onPress?: () => void;
  species?: Player['species'];
  guided?: boolean;
}) {
  const card = cards[id];
  const reduced = useReducedMotion();
  const lift = useSharedValue(0);
  const press = useSharedValue(1);
  useEffect(() => {
    lift.set(reduced ? 0 : withSpring(selected ? -8 : 0, { damping: 18, stiffness: 350 }));
  }, [lift, reduced, selected]);
  const motion = useAnimatedStyle(() => ({
    opacity: disabled ? 0.6 : 1,
    transform: [{ translateY: lift.value }, { scale: press.value }],
  }));
  const color =
    card.habit === 'BLOB'
      ? c.rest
      : card.habit === 'RAT'
        ? c.roam
        : card.habit === 'CUBE'
          ? c.focus
          : c.body;
  const habit =
    card.habit === 'BLOB'
      ? 'REST'
      : card.habit === 'RAT'
        ? 'ROAM'
        : card.habit === 'CUBE'
          ? 'FOCUS'
          : 'CARE';
  const effect = (
    species && card.power > 0 && card.habit === species
      ? card.effect.replace(String(card.power), String(cardPower(id, species)))
      : card.effect
  ).replace('⚡', 'energy');
  const face = (
    <View
      style={{
        ...panelStyle,
        borderRadius: 12,
        minHeight: 168,
        borderColor:
          guided || selected
            ? c.moss
            : card.rarity === 'EPIC'
              ? c.goldFrame
              : card.rarity === 'RARE'
                ? c.silver
                : c.outline,
      }}
    >
      <PaperFinish />
      <View
        style={{
          borderTopLeftRadius: 10,
          borderTopRightRadius: 10,
          backgroundColor: color,
          padding: 8,
          paddingRight: 30,
          minHeight: 32,
        }}
      >
        <BodyText
          numberOfLines={1}
          style={{ fontSize: 11, fontFamily: 'PixelifySans_700Bold', color: c.buttonInk }}
        >
          {habit}
          {count !== undefined ? ` ×${count}` : ''}
        </BodyText>
      </View>
      <View
        style={{
          position: 'absolute',
          right: 4,
          top: 4,
          width: 28,
          height: 28,
          borderRadius: 14,
          backgroundColor: c.paper,
          borderWidth: 1,
          borderColor: c.outline,
          flexDirection: 'row',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 1,
        }}
      >
        <Zap size={11} color={c.ink} fill={c.ink} />
        <BodyText style={{ fontSize: 12, fontFamily: 'PixelifySans_700Bold' }}>
          {card.cost}
        </BodyText>
      </View>
      <View style={{ alignItems: 'center', padding: 6, gap: 4 }}>
        <View
          style={{
            width: 56,
            height: 56,
            borderRadius: 8,
            borderWidth: 2,
            borderColor: c.outline,
            backgroundColor: c.body,
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <CardIllustration id={id} />
        </View>
        <BodyText
          numberOfLines={2}
          style={{
            fontFamily: 'PixelifySans_700Bold',
            fontSize: 13,
            lineHeight: 17,
            minHeight: 34,
            textAlign: 'center',
          }}
        >
          {card.name}
        </BodyText>
        <BodyText numberOfLines={1} style={{ fontSize: 12, lineHeight: 18, textAlign: 'center' }}>
          {effect}
        </BodyText>
      </View>
      {card.rarity !== 'COMMON' && <CardShine gold={card.rarity === 'EPIC'} />}
    </View>
  );
  return (
    <Animated.View style={[{ flex: 1 }, motion]}>
      {onPress ? (
        <Pressable
          accessibilityRole="button"
          accessibilityState={{ disabled, selected }}
          accessibilityLabel={`${card.name}, ${card.cost} energy, ${cardDetails[id]}${species ? (selected ? ', tap again to play' : ', tap to select') : ', show details'}`}
          onPress={onPress}
          disabled={disabled}
          onPressIn={() => press.set(reduced ? 1 : withTiming(0.97, { duration: 80 }))}
          onPressOut={() => press.set(reduced ? 1 : withSpring(1, { damping: 15, stiffness: 400 }))}
        >
          {face}
        </Pressable>
      ) : (
        face
      )}
    </Animated.View>
  );
}
function CardShine({ gold }: { gold: boolean }) {
  const reduced = useReducedMotion();
  const x = useSharedValue(-100);
  useEffect(() => {
    // One arrival glint, then settle. A rare card does not need watching.
    x.set(reduced ? -100 : withDelay(1200, withTiming(240, { duration: 700 })));
    return () => cancelAnimation(x);
  }, [x, reduced]);
  const motion = useAnimatedStyle(() => ({
    transform: [{ translateX: x.value }, { rotate: '20deg' }],
  }));
  return (
    <View
      pointerEvents="none"
      style={{ position: 'absolute', inset: 0, borderRadius: 12, overflow: 'hidden' }}
    >
      <Animated.View style={[{ width: 36, height: '140%', top: -20 }, motion]}>
        <LinearGradient
          colors={[c.transparent, gold ? c.amber : c.highlight, c.transparent]}
          style={{ flex: 1, opacity: 0.45 }}
        />
      </Animated.View>
    </View>
  );
}
export function RewardCard({
  id,
  index,
  skip = false,
}: {
  id: CardId;
  index: number;
  skip?: boolean;
}) {
  const reduced = useReducedMotion();
  const p = useSharedValue(0);
  useEffect(() => {
    p.set(
      skip
        ? 1
        : withDelay(reduced ? 0 : index * 150, withTiming(1, { duration: reduced ? 100 : 240 })),
    );
    return () => cancelAnimation(p);
  }, [p, skip, reduced, index]);
  const motion = useAnimatedStyle(() => ({
    opacity: p.value,
    transform: [{ perspective: 700 }, { rotateY: `${(1 - p.value) * (reduced ? 0 : 90)}deg` }],
  }));
  return (
    <Animated.View style={[{ flex: 1 }, motion]}>
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
  const columns = width < 600 ? 2 : 3;
  return (
    <View style={{ flex: 1, padding: 16, gap: 16 }}>
      <CozyBackground />
      <PixelText style={{ fontSize: 16, lineHeight: 28 }}>
        {reward && earned
          ? `+${ids.length} ${ids.length === 1 ? 'CARD' : 'CARDS'} FROM ${earned.minutes} MIN OFFLINE`
          : `MY DECK · ${p.deck.length}/20`}
      </PixelText>
      {reward ? (
        mission && <BodyText>{mission.name}</BodyText>
      ) : (
        <BodyText style={{ fontSize: 12 }}>
          15 offline MIN = 1 common card. Tap a card for details.
        </BodyText>
      )}
      <FlatList
        key={columns}
        data={ids}
        numColumns={columns}
        keyExtractor={(id, index) => `${id}-${index}`}
        columnWrapperStyle={{ gap: 12 }}
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
        <BodyText accessibilityLiveRegion="polite">{cardDetails[selected]}</BodyText>
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
