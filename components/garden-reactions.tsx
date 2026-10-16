import { useEffect, useState } from 'react';
import { Image, View } from 'react-native';
import frogImg from '@/assets/garden/frog.png';

export type GardenReaction = {
  id: number;
  kind: 'water' | 'read' | 'pond' | 'pat' | 'lantern';
  x: number;
  y: number;
};

type Pixel = { x: number; y: number; w?: number; h?: number; color: string };

// All effects use the world's native pixel grid. Their clock is finite and lives
// only while the parent shows a reaction, so hidden tabs cannot keep it running.
export function GardenReactions({
  reaction,
  scale,
  reduced,
}: {
  reaction: GardenReaction;
  scale: number;
  reduced: boolean;
}) {
  const [phase, setPhase] = useState(0);
  useEffect(() => {
    if (reduced) return undefined;
    let next = 0;
    const timer = setInterval(() => {
      next += 1;
      setPhase(next);
      if (next >= 24) clearInterval(timer);
    }, 180);
    return () => clearInterval(timer);
  }, [reduced]);
  const t = reduced ? 5 : phase;
  const pixels: Pixel[] = [];
  const add = (x: number, y: number, color: string, w = 1, h = 1) =>
    pixels.push({ x, y, color, w, h });

  if (reaction.kind === 'water') {
    // A short shower falls into the two raised beds, never an endlessly
    // repeating watering task. Highlighted petals are the lasting feedback.
    if (reduced || t < 12) {
      for (let i = 0; i < 12; i++) {
        const second = i >= 8;
        const x = second ? 152 + (i - 8) * 4 : 130 + (i % 5) * 6;
        const y = (second ? 136 : 108) + (reduced ? 2 : (t * 2 + i * 3) % 8);
        add(x, y, '#BDE7E3', 1, reduced ? 1 : 2);
        add(x, y - 1, '#E0F5E8');
      }
    }
    for (const [x, y] of [
      [130, 115],
      [136, 115],
      [142, 115],
      [148, 115],
      [154, 115],
      [130, 121],
      [142, 121],
      [154, 121],
      [152, 143],
      [158, 143],
      [164, 143],
    ]) {
      add(x, y - 1, '#FFF0B7');
      add(x - 1, y, '#F3D895');
      add(x + 1, y, '#FFF4D8');
      add(x, y, '#E9AD48');
      add(x, y + 2, '#8FCB64');
    }
  }

  if (reaction.kind === 'read') {
    // One page turns, then settles with a ribbon bookmark. No screen time
    // counter or reward makes a real book compete with this little one.
    const page = reduced || t > 5 ? 3 : [3, 2, 1, 1, 2, 3][t];
    const left = reduced || t > 2 ? 106 : 110 - page;
    add(left, 51, '#FFF8DC', page, 3);
    add(left, 50, '#D6B98A', page, 1);
    add(109, 51, '#8A7652', 1, 4);
    add(106, 52, '#C3AD82', 2, 1);
    add(110, 55, '#9B79B0', 1, 3);
    add(111, 57, '#D5BCE5');
  }

  if (reaction.kind === 'pond') {
    // Square-stepped oval rings match the pond's tile language.
    const radius = reduced ? 7 : 4 + (t % 8);
    const cx = 41;
    const cy = 137;
    const color = '#A9D7D5';
    add(cx - radius + 2, cy - 3, color, radius * 2 - 3);
    add(cx - radius, cy - 2, color, 2);
    add(cx + radius - 1, cy - 2, color, 2);
    add(cx - radius - 1, cy - 1, color, 1, 2);
    add(cx + radius + 1, cy - 1, color, 1, 2);
    add(cx - radius, cy + 1, color, 2);
    add(cx + radius - 1, cy + 1, color, 2);
    add(cx - radius + 2, cy + 2, color, radius * 2 - 3);
  }

  if (reaction.kind === 'pat') {
    const rise = reduced ? 4 : Math.min(12, Math.floor(t / 2));
    for (const offset of [-8, 7]) {
      const x = reaction.x + offset;
      const y = reaction.y - 29 - rise + (offset > 0 ? 4 : 0);
      add(x, y, '#F3B8AF', 2);
      add(x + 3, y, '#F3B8AF', 2);
      add(x - 1, y + 1, '#CD797C', 7, 2);
      add(x, y + 3, '#CD797C', 5);
      add(x + 1, y + 4, '#B65F72', 3);
      add(x + 2, y + 5, '#B65F72');
    }
  }

  if (reaction.kind === 'lantern') {
    for (const [x, y] of [
      [122, 69],
      [132, 74],
      [123, 81],
    ]) {
      add(x, y, '#FFF0B4', 1, 3);
      add(x - 1, y + 1, '#FFF0B4', 3);
    }
  }

  return (
    <View
      pointerEvents="none"
      accessible={false}
      importantForAccessibility="no-hide-descendants"
      style={{ position: 'absolute', left: 0, top: 0, zIndex: 880 }}
    >
      {reaction.kind === 'pond' && (
        <Image
          source={frogImg}
          resizeMode="stretch"
          style={{
            position: 'absolute',
            left: Math.round(28 * scale),
            top: Math.round((124 - (!reduced && t > 0 && t < 4 ? 2 : 0)) * scale),
            width: Math.round(12 * scale),
            height: Math.round(10 * scale),
          }}
        />
      )}
      {pixels.map((p) => (
        <View
          key={`${p.x}-${p.y}-${p.color}`}
          style={{
            position: 'absolute',
            left: Math.round(p.x * scale),
            top: Math.round(p.y * scale),
            width: Math.max(1, Math.round((p.w ?? 1) * scale)),
            height: Math.max(1, Math.round((p.h ?? 1) * scale)),
            backgroundColor: p.color,
          }}
        />
      ))}
    </View>
  );
}
