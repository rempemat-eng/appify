import type { ReactNode } from 'react';
import { Image, View } from 'react-native';

/** Bundled tile art, positioned in DIPs relative to its shared image layer. */
export type PixelImageProps = {
  source: number;
  x: number;
  y: number;
  width: number;
  height: number;
  nearest?: boolean;
  onError?: (error: Error) => void;
};

export type PixelImageLayerProps = {
  width: number;
  height: number;
  children?: ReactNode;
};

/** Native resolves this layer to one Skia canvas for the entire mounted set. */
export function PixelImageLayer({ width, height, children }: PixelImageLayerProps) {
  return (
    <View
      pointerEvents="none"
      // @ts-expect-error dataSet is a react-native-web prop (existing nearest-neighbour CSS).
      dataSet={{ pixel: 'true' }}
      style={{ width, height }}
    >
      {children}
    </View>
  );
}

/** Web keeps the existing Image/stretch path and inherited data-pixel styling.
 * On native, place every PixelImage inside one PixelImageLayer, not a View. */
export function PixelImage({ source, x, y, width, height, onError }: PixelImageProps) {
  return (
    <Image
      source={source}
      resizeMode="stretch"
      onError={onError ? (event) => onError(new Error(event.nativeEvent.error)) : undefined}
      style={{ position: 'absolute', left: x, top: y, width, height }}
    />
  );
}

export default PixelImage;
