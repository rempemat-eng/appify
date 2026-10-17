import { worldCatalogue } from './world-catalogue';
import { WORLD, worldMaps, type WorldId } from './world-maps';

/** Left edge of a window this wide that centres on x across a world this wide:
 * clamped to the world, or negative (centred) when the world is narrower. */
export function windowStart(centre: number, window: number, world: number) {
  if (world <= window) return (world - window) / 2;
  return Math.max(0, Math.min(world - window, centre - window / 2));
}

/** Frame a world's landmark for a preview window, in the flat 3/4 view at this pixel
 * scale (coherence plan, step 7). Width and height are the window's inner size; the
 * height is a minimum that grows to keep the whole landmark visible. */
export function worldPreviewFrame(world: WorldId, width: number, height: number, scale: number) {
  const worldWidth = WORLD.width * scale;
  const worldHeight = WORLD.height * scale;
  const object = worldMaps[world].objects.find(
    (entry) => entry.id === worldCatalogue[world].previewLandmark,
  );
  const landmark = object
    ? {
        left: object.x * scale,
        top: object.y * scale,
        width: object.w * scale,
        height: object.h * scale,
      }
    : null;
  const centreX = landmark ? landmark.left + landmark.width / 2 : worldWidth / 2;
  const centreY = landmark ? landmark.top + landmark.height / 2 : worldHeight / 2;
  const viewportHeight = Math.max(height, Math.ceil(landmark?.height ?? 0) + 4);
  const maxTop = Math.max(0, worldHeight - viewportHeight);
  const top = Math.round(Math.max(0, Math.min(maxTop, centreY - viewportHeight / 2)));
  const left = Math.round(windowStart(centreX, width, worldWidth));
  return { left, top, height: viewportHeight, worldWidth, worldHeight, landmark };
}
