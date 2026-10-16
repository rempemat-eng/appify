import { useState } from 'react';
import { Pressable, View } from 'react-native';
import { ChevronDown, ChevronUp } from 'lucide-react-native';
import type { Player } from '@/lib/game';
import { companionProfile } from '@/lib/companion-profiles';
import { befriendedVisitorIds, collectionOf, postcardsOf } from '@/lib/visitors';
import { cozy as c } from '@/lib/cozy';
import { CozyPanel } from '@/components/cozy-ui';
import { PixelButton } from '@/components/game-ui';
import { BodyText } from '@/components/pixel-feedback';
import { PixelProp } from '@/components/pixel-scenes';

type JourneyAction = 'missions' | 'journal' | 'companions' | 'spar';
type JourneyStep = { heading: string; body: string; label: string; action: JourneyAction };

function nextGardenStep(player: Player): JourneyStep {
  const companion = companionProfile(player);
  const met = collectionOf(player).length;
  const friends = befriendedVisitorIds(player).length;
  const postcards = postcardsOf(player);
  if (met === 0)
    return {
      heading: 'A little path beyond home',
      body: `Your garden is ${companion.name}'s home. A first break of 10 simulated MIN or more brings a visitor; Park Patrol is a short place to start.`,
      label: 'CHOOSE A FIRST OUTING',
      action: 'missions',
    };
  if (friends === 0)
    return {
      heading: 'A neighbour has found your garden',
      body: 'You have met a visitor. Befriend them for free while they are visiting to invite them along. The Field Journal explains how visits work.',
      label: 'MEET YOUR NEIGHBOURS',
      action: 'journal',
    };
  if (postcards.length === 0)
    return {
      heading: 'Bring home your first postcard',
      body: `${companion.name} can explore the park or join Book Club while you take a break. Finish a mission to keep its postcard; a break idea is optional.`,
      label: 'CHOOSE A PLACE',
      action: 'missions',
    };
  if (companion.id === null)
    return {
      heading: 'A familiar face for your next outing',
      body: `${friends === 1 ? 'A befriended visitor can' : `${friends} befriended visitors can`} come along too. Preview their personalities or stay with ${companion.name}; your progress is shared.`,
      label: 'MEET YOUR COMPANIONS',
      action: 'companions',
    };
  if (new Set(postcards.map((postcard) => postcard.mission)).size >= 2)
    return {
      heading: 'Try the cards you brought home',
      body: 'Dave is ready for a friendly local practice fight. It is optional: your garden, postcards and memories are here whenever you return.',
      label: 'VISIT DAVE',
      action: 'spar',
    };
  return {
    heading: 'Every outing leaves a little story',
    body: 'Your Field Journal keeps postcards, visitor meetings and the memories you choose to save. Take a look, or leave the next outing for another day.',
    label: 'OPEN YOUR FIELD JOURNAL',
    action: 'journal',
  };
}

/** A read-only invitation. The caller owns every navigation or game action. */
export function GardenJourney({
  player,
  onMissions,
  onJournal,
  onCompanions,
  onSpar,
}: {
  player: Player;
  onMissions: () => void;
  onJournal: () => void;
  onCompanions: () => void;
  onSpar: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const next = nextGardenStep(player);
  const actions: Record<JourneyAction, () => void> = {
    missions: onMissions,
    journal: onJournal,
    companions: onCompanions,
    spar: onSpar,
  };
  const Chevron = expanded ? ChevronUp : ChevronDown;
  return (
    <CozyPanel style={{ padding: 14, gap: 10 }}>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
        <View
          aria-hidden
          accessibilityElementsHidden
          importantForAccessibility="no-hide-descendants"
          style={{ padding: 6, borderRadius: 10, backgroundColor: c.sage }}
        >
          <PixelProp kind="tree" size={32} />
        </View>
        <View style={{ flex: 1, minWidth: 0, gap: 3 }}>
          <BodyText
            style={{ fontSize: 10, fontFamily: 'Nunito_800ExtraBold', color: c.leafOutline }}
          >
            AROUND THE GARDEN
          </BodyText>
          <BodyText
            accessibilityRole="header"
            style={{ fontSize: 14, fontFamily: 'Nunito_800ExtraBold' }}
          >
            {next.heading}
          </BodyText>
        </View>
      </View>
      <BodyText style={{ fontSize: 12, lineHeight: 18 }}>{next.body}</BodyText>
      <PixelButton small light label={next.label} onPress={actions[next.action]} />
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={expanded ? 'Close garden trail' : 'Explore the garden trail'}
        accessibilityState={{ expanded }}
        aria-expanded={expanded}
        onPress={() => setExpanded((value) => !value)}
        style={({ pressed }) => ({
          minHeight: 44,
          paddingHorizontal: 8,
          flexDirection: 'row',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 8,
          borderTopWidth: 1,
          borderTopColor: c.faded,
          opacity: pressed ? 0.7 : 1,
        })}
      >
        <BodyText style={{ fontSize: 11, fontFamily: 'Nunito_800ExtraBold' }}>
          GARDEN TRAIL
        </BodyText>
        <Chevron size={16} color={c.ink} />
      </Pressable>
      {expanded && (
        <View style={{ gap: 10, paddingHorizontal: 2 }}>
          {[
            [
              'A home to return to',
              'Wander, pat your companion and enjoy the little garden details. These moments have no cost or reward.',
            ],
            [
              'A place to take a break',
              'Park Patrol, Book Club and Mountain Retreat give your companion somewhere to explore while you are away.',
            ],
            [
              'A story to bring back',
              'Completed missions bring cards and postcards. Befriend visitors, or keep an optional self-reported memory in your journal.',
            ],
          ].map(([title, body]) => (
            <View key={title} style={{ gap: 3 }}>
              <BodyText style={{ fontSize: 12, fontFamily: 'Nunito_800ExtraBold' }}>
                {title}
              </BodyText>
              <BodyText style={{ fontSize: 12, lineHeight: 18 }}>{body}</BodyText>
            </View>
          ))}
        </View>
      )}
    </CozyPanel>
  );
}
