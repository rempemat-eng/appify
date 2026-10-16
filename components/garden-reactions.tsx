import { useEffect, useRef, useState } from 'react';
import { Image, View } from 'react-native';
import frogImg from '@/assets/garden/frog.png';

export type GardenReaction = {
  id: number;
  kind: 'water' | 'read' | 'pond' | 'pat' | 'lantern';
  x: number;
  y: number;
};

type Pixel = { x: number; y: number; w?: number; h?: number; color: string; opacity?: number };

const FLOWERS = [
  { x: 130, y: 115 },
  { x: 136, y: 115 },
  { x: 142, y: 115 },
  { x: 148, y: 115 },
  { x: 154, y: 115 },
  { x: 130, y: 121 },
  { x: 142, y: 121 },
  { x: 154, y: 121 },
  { x: 152, y: 143 },
  { x: 158, y: 143 },
  { x: 164, y: 143 },
];

// Eight stepped frames per second preserve the pixel silhouettes. Each reaction
// has a short lead-in, one action, then a quiet settle instead of a looping burst.
// The finite clock exists only while this keyed reaction is mounted.
export type Place = (
  x: number,
  y: number,
  groundY?: number,
) => { sx: number; sy: number; f: number };

export function GardenReactions({
  reaction,
  scale,
  reduced,
  place,
  base,
}: {
  reaction: GardenReaction;
  scale: number;
  reduced: boolean;
  /** maps native garden coordinates to the screen (flat or 2.5D) */
  place: Place;
  /** ground line for effects that float above a prop (book, hearts, lantern) */
  base?: number;
}) {
  const [phase, setPhase] = useState(0);
  const progress = useRef(0);
  useEffect(() => {
    if (reduced || progress.current >= 32) return undefined;
    let running = true;
    const timer = setInterval(() => {
      if (!running) return;
      const next = ++progress.current;
      setPhase(next);
      if (next >= 32) {
        running = false;
        clearInterval(timer);
      }
    }, 120);
    return () => {
      running = false;
      clearInterval(timer);
    };
  }, [reduced]);
  const t = reduced ? 22 : phase;
  const pixels: Pixel[] = [];
  const add = (x: number, y: number, color: string, w = 1, h = 1, opacity = 1) =>
    pixels.push({ x, y, color, w, h, opacity });

  const ring = (cx: number, cy: number, radius: number, opacity: number) => {
    const h = Math.max(2, Math.round(radius / 3));
    const color = '#B8DDD6';
    add(cx - radius + 2, cy - h, color, radius * 2 - 3, 1, opacity);
    add(cx - radius, cy - h + 1, color, 2, 1, opacity);
    add(cx + radius - 1, cy - h + 1, color, 2, 1, opacity);
    add(cx - radius - 1, cy - h + 2, color, 1, h * 2 - 3, opacity);
    add(cx + radius + 1, cy - h + 2, color, 1, h * 2 - 3, opacity);
    add(cx - radius, cy + h - 1, color, 2, 1, opacity);
    add(cx + radius - 1, cy + h - 1, color, 2, 1, opacity);
    add(cx - radius + 2, cy + h, color, radius * 2 - 3, 1, opacity);
  };

  if (reaction.kind === 'water') {
    // A tiny reflection tips the eye toward the can before the shower begins.
    if (!reduced && t < 3) {
      add(184, 101, '#D7F1D9', 1, 2);
      add(183, 102, '#B6DACC', 3);
    }
    FLOWERS.forEach(({ x, y }, i) => {
      const age = t - 3 - (i % 4) * 2;
      if (reduced) {
        add(x + 1, y - 5, '#CBECE6', 1, 2);
      } else if (age >= 0 && age < 7) {
        // Two offset beads, rather than a texture blinking between positions.
        const dropY = y - 13 + age * 2;
        add(x + Math.max(0, 3 - Math.floor(age / 2)), dropY, '#CBECE6', 1, 2);
        if (age > 1) add(x + 2, dropY - 4, '#98D0D1', 1, 2, 0.8);
      } else if (age >= 7 && age < 10) {
        const spread = age - 7;
        add(x - spread - 1, y + 1, '#B5DFDA', 2, 1, 1 - spread * 0.25);
        add(x + spread + 1, y, '#D7F0E2', 1, 1, 1 - spread * 0.25);
      }
      if (reduced || age >= 7) {
        const bend = !reduced && age >= 8 && age < 11 ? 1 : 0;
        const opacity = reduced ? 1 : Math.min(1, Math.max(0, (age - 6) / 3));
        add(x + bend, y - 1, '#FFF0B7', 1, 1, opacity);
        add(x - 1 + bend, y, '#F3D895', 1, 1, opacity);
        add(x + 1 + bend, y, '#FFF4D8', 1, 1, opacity);
        add(x + bend, y, '#E9AD48', 1, 1, opacity);
        add(x, y + 2, '#8FCB64', 1, 1, opacity);
      }
    });
  }

  if (reaction.kind === 'read') {
    // The right page lifts, crosses its crease edge-on, then lies on the left.
    const turn = Math.max(0, Math.min(8, t - 3));
    const page = reduced || t > 11 ? 3 : [3, 3, 2, 1, 1, 1, 2, 3, 3][turn];
    const left = reduced || t > 7 ? 109 - page : 110;
    const lifted = !reduced && t >= 3 && t <= 10;
    add(left, lifted ? 49 : 51, '#FFF8DC', page, lifted ? 4 : 3);
    add(left, lifted ? 48 : 50, '#D6B98A', page);
    if (lifted && page > 1) add(left + page - 1, 50, '#D9C797', 1, 3);
    add(109, 51, '#8A7652', 1, 4);
    if (!lifted || turn > 6) add(106, 52, '#C3AD82', 2);
    const ribbon = !reduced && t >= 11 && t < 15 ? 1 : 0;
    add(110 + ribbon, 55, '#9B79B0', 1, 3);
    add(111 + ribbon, 57, '#D5BCE5');
  }

  if (reaction.kind === 'pond') {
    // One landing sends out two rings. Both expand and fade without resetting.
    if (reduced) ring(34, 133, 7, 0.8);
    else {
      for (const delay of [8, 13]) {
        const age = t - delay;
        if (age >= 0 && age <= 16)
          ring(34, 133, 3 + Math.floor(age * 0.65), Math.max(0, 0.85 - age / 20));
      }
      if (t >= 8 && t < 11) {
        const reach = t - 7;
        add(28 - reach, 131 - reach, '#C4E4DC', 1, 2);
        add(40 + reach, 132 - reach, '#C4E4DC', 1, 2);
      }
    }
  }

  if (reaction.kind === 'pat') {
    for (const [offset, delay] of [
      [-8, 1],
      [7, 5],
    ]) {
      const age = t - delay;
      if (!reduced && (age < 0 || age > 25)) continue;
      const rise = reduced ? 4 : Math.min(16, Math.floor(age * 0.8));
      const opacity = reduced ? 1 : Math.min(1, (age + 1) / 3, Math.max(0, (25 - age) / 9));
      const x = reaction.x + offset;
      const y = reaction.y - 29 - rise + (offset > 0 ? 4 : 0);
      add(x, y, '#F3B8AF', 2, 1, opacity);
      add(x + 3, y, '#F3B8AF', 2, 1, opacity);
      add(x - 1, y + 1, '#CD797C', 7, 2, opacity);
      add(x, y + 3, '#CD797C', 5, 1, opacity);
      add(x + 1, y + 4, '#B65F72', 3, 1, opacity);
      add(x + 2, y + 5, '#B65F72', 1, 1, opacity);
    }
  }

  if (reaction.kind === 'lantern') {
    for (const [x, y, delay] of [
      [122, 69, 0],
      [132, 74, 3],
      [123, 81, 6],
    ]) {
      const age = t - delay;
      if (reduced || (age >= 0 && age < 9)) {
        const opacity = reduced ? 0.8 : Math.min(1, (age + 1) / 3, (9 - age) / 5);
        add(x, y, '#FFF0B4', 1, 3, opacity);
        add(x - 1, y + 1, '#FFF0B4', 3, 1, opacity);
      }
    }
  }

  const frogHop = !reduced && t >= 3 && t < 8 ? [1, 3, 5, 4, 2][t - 3] : 0;
  const frogDip = !reduced && (t < 3 || (t >= 8 && t < 10)) ? 1 : 0;

  return (
    <View
      pointerEvents="none"
      accessible={false}
      importantForAccessibility="no-hide-descendants"
      style={{ position: 'absolute', left: 0, top: 0, zIndex: 880 }}
    >
      {reaction.kind === 'pond' && (
        <>
          <View
            style={{
              position: 'absolute',
              left: Math.round(place(30, 132).sx),
              top: Math.round(place(30, 132).sy),
              width: Math.round(8 * scale * place(30, 132).f),
              height: Math.max(1, Math.round(scale * place(30, 132).f)),
              backgroundColor: '#284C5E',
              opacity: frogHop ? 0.25 : 0.45,
            }}
          />
          <Image
            source={frogImg}
            resizeMode="stretch"
            style={{
              position: 'absolute',
              left: Math.round(place(28, 124 + frogDip - frogHop, 134).sx),
              top: Math.round(place(28, 124 + frogDip - frogHop, 134).sy),
              width: Math.round(12 * scale * place(28, 134).f),
              height: Math.round(10 * scale * place(28, 134).f),
            }}
          />
        </>
      )}
      {pixels.map((p) => {
        const q = place(p.x, p.y, base);
        return (
          <View
            key={`${p.x}-${p.y}-${p.color}`}
            style={{
              position: 'absolute',
              left: Math.round(q.sx),
              top: Math.round(q.sy),
              width: Math.max(1, Math.round((p.w ?? 1) * scale * q.f)),
              height: Math.max(1, Math.round((p.h ?? 1) * scale * q.f)),
              backgroundColor: p.color,
              opacity: p.opacity ?? 1,
            }}
          />
        );
      })}
    </View>
  );
}
