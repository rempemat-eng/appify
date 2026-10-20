import { PixelImage, PixelImageLayer } from '@/components/pixel-image';
import { tileLayout, type Point, type ProbeTile } from '@/lib/native-pixels';

export type NativePixelTilesProps = {
  tiles: readonly ProbeTile[];
  camera: Point;
  pixel: number;
  dpr: number;
  width: number;
  height: number;
  nearest: boolean;
  onError: (error: Error) => void;
};

function Tile({
  tile,
  camera,
  pixel,
  dpr,
  nearest,
  onError,
}: Pick<NativePixelTilesProps, 'camera' | 'pixel' | 'dpr' | 'nearest' | 'onError'> & {
  tile: ProbeTile;
}) {
  const { left, top, width, height } = tileLayout(tile, camera, pixel, dpr);
  return (
    <PixelImage
      source={tile.source}
      x={left}
      y={top}
      width={width}
      height={height}
      nearest={nearest}
      onError={onError}
    />
  );
}

/** One screen-sized native surface; only mounted tiles decode. Coordinates are
 * art pixels, dimensions are DIPs, and Skia applies the device density once.
 * Keep this component out of .web imports; #126 can supply worldTileArt here. */
export default function NativePixelTiles({
  tiles,
  camera,
  pixel,
  dpr,
  width,
  height,
  nearest,
  onError,
}: NativePixelTilesProps) {
  return (
    <PixelImageLayer width={width} height={height}>
      {tiles.map((tile) => (
        <Tile
          key={tile.id}
          tile={tile}
          camera={camera}
          pixel={pixel}
          dpr={dpr}
          nearest={nearest}
          onError={onError}
        />
      ))}
    </PixelImageLayer>
  );
}
