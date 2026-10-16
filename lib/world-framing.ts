import { billboard, makeProjection } from './garden-projection';
import { worldCatalogue } from './world-catalogue';
import { WORLD, worldMaps, type WorldId } from './world-maps';

/** Frame a landmark using the same projected sprite bounds as WorldScene.
 * Width and height are the preview's inner dimensions, excluding its border.
 * The requested height is a minimum: a short, wide layout grows enough to
 * keep the landmark visible instead of clipping its roof or base.
 */
export function worldPreviewFrame(world: WorldId, width: number, height: number) {
  const projection = makeProjection('tilt', width, WORLD, Math.round(width * 0.14));
  const object = worldMaps[world].objects.find(
    (entry) => entry.id === worldCatalogue[world].previewLandmark,
  );
  const landmark = object ? billboard(projection, object.x, object.y, object.w, object.h) : null;
  const centre = landmark ? landmark.top + landmark.height / 2 : projection.height / 2;
  const viewportHeight = Math.max(height, Math.ceil(landmark?.height ?? 0) + 4);
  const maxTop = Math.max(0, projection.height - viewportHeight);
  const top = Math.round(Math.max(0, Math.min(maxTop, centre - viewportHeight / 2)));
  return { top, height: viewportHeight, worldHeight: projection.height, landmark };
}
