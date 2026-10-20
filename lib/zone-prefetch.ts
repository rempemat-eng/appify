import { Image, type ImageSourcePropType } from 'react-native';
import { zoneIds, zoneMaps } from './zone-maps';
import { zoneGrounds, zoneProps } from './zone-assets';
import { regionTiles, type RegionId } from './region-walk';
import { WORLD_CANVAS } from './world-flag';
import { worldTiles } from './world-canvas';
import { worldFlowArt, worldTileArt } from './world-canvas-assets';
import { chunkFor } from './world-walk';

const asked = new Set<string>();

function uriOf(source: ImageSourcePropType | undefined): string | null {
  if (!source) return null;
  if (typeof source === 'object' && !Array.isArray(source) && 'uri' in source && source.uri)
    return source.uri;
  const resolved = Image.resolveAssetSource?.(source);
  return resolved?.uri ?? null;
}

/**
 * Start loading a region's ground and props while a journey plays, so the arrival
 * shows the place at once instead of an empty field while its pictures load. Each
 * picture is asked for once; failures are ignored (the scene still loads as usual).
 */
export function prefetchRegion(region: RegionId) {
  if (WORLD_CANVAS) {
    // the world canvas: the chunk's tile pictures and moving water, and its props
    const ch = chunkFor(region);
    const sources: (ImageSourcePropType | undefined)[] = [];
    for (const [key, t] of Object.entries(worldTiles[ch.plane])) {
      const [c, r] = key.split(',').map(Number);
      const x = c * 256 - ch.origin[0];
      const y = r * 256 - ch.origin[1];
      if (x + 256 <= 0 || y + 256 <= 0 || x >= ch.size[0] || y >= ch.size[1]) continue;
      if (t.art && !t.fill) sources.push(worldTileArt[t.art]);
      sources.push(worldFlowArt[ch.plane][key]);
      for (const [, sprite] of t.objects) sources.push(zoneProps[sprite]);
    }
    for (const source of sources) {
      const uri = uriOf(source);
      if (!uri || asked.has(uri)) continue;
      asked.add(uri);
      Image.prefetch(uri).catch(() => {});
    }
    return;
  }
  for (const tile of regionTiles(region)) {
    const zone = zoneIds.find((id) => id === tile.id);
    if (!zone) continue; // the garden: drawn from its own pictures, already loaded
    const sources = [
      zoneGrounds[zone],
      ...zoneMaps[zone].objects.map(([, sprite]) => zoneProps[sprite]),
    ];
    for (const source of sources) {
      const uri = uriOf(source);
      if (!uri || asked.has(uri)) continue;
      asked.add(uri);
      Image.prefetch(uri).catch(() => {});
    }
  }
}
