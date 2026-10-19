import type { SceneExtra } from '@/components/atlas-walk';
import { decorBox, type DecorPlacement } from '@/lib/decor';
import { decorImages } from '@/lib/decor-assets';

/** Keepsakes as things standing in a scene (their feet in region pixels), for AtlasWalk. */
export function decorExtras(list: readonly DecorPlacement[]): SceneExtra[] {
  return list.map((p) => {
    const b = decorBox(p.item, p.x, p.y);
    return {
      key: `decor-${p.item}`,
      src: decorImages[p.item],
      x: b.left,
      y: b.top,
      w: b.w,
      h: b.h,
      // a rug lies under everything; the rest stand at their feet
      z: b.flat ? 2 : p.y,
    };
  });
}
