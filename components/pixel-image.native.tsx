import { Canvas, FilterMode, Image, MipmapMode, useImage } from '@shopify/react-native-skia';
import type { PixelImageLayerProps, PixelImageProps } from './pixel-image';

export type { PixelImageLayerProps, PixelImageProps } from './pixel-image';

/** One viewport-sized native surface shared by every mounted PixelImage. */
export function PixelImageLayer({ width, height, children }: PixelImageLayerProps) {
  return (
    <Canvas style={{ width, height }} pointerEvents="none">
      {children}
    </Canvas>
  );
}

/** Drawing node only: its parent PixelImageLayer owns the single native canvas. */
export function PixelImage({
  source,
  x,
  y,
  width,
  height,
  nearest = true,
  onError,
}: PixelImageProps) {
  const image = useImage(source, onError);
  return (
    <Image
      image={image}
      x={x}
      y={y}
      width={width}
      height={height}
      fit="fill"
      sampling={{
        filter: nearest ? FilterMode.Nearest : FilterMode.Linear,
        mipmap: MipmapMode.None,
      }}
    />
  );
}

export default PixelImage;
