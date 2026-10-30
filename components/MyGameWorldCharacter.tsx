import { Fragment, type ComponentProps } from 'react';
import { Image, View, type ImageSourcePropType } from 'react-native';
import { AtlasWalk } from '@/components/atlas-walk';
import {
  myGameClip,
  projectMyGameCharacter,
  sampleMyGameClip,
  type MyGameCharacterAsset,
  type MyGamePoint,
  type MyGameView,
} from '@/lib/mygame-character';

export type MyGameWorldCharacterProps = {
  asset: MyGameCharacterAsset;
  view: MyGameView;
  clip: string;
  /** From the scene's shared active-time clock, not a component-owned timer. */
  elapsed: number;
  foot: MyGamePoint;
  supportHeight: number;
  airborneHeight: number;
  worldUnit: number;
  assetPixelsPerWorldPixel: number;
  devicePixelRatio: number;
  resolveImage: (asset: string) => ImageSourcePropType;
  holding?: boolean;
  reducedMotion?: boolean;
  /** Supplied by AtlasWalk's level contract, not inferred from screen height. */
  depthOffset?: number;
  showShadow?: boolean;
};

/** A node for AtlasWalk's existing `scene` slot. Returns siblings so each foot
 * sorts among world props. No nested stacking plane, private clock or mirrored view. */
export function MyGameWorldCharacter(props: MyGameWorldCharacterProps) {
  const clip = myGameClip(props.asset, props.view, props.clip);
  if (!clip) return null;
  const { frame } = sampleMyGameClip(clip, props.elapsed, props);
  const projection = projectMyGameCharacter({ ...props, asset: props.asset.views[props.view]! });
  const [x, y, width, height] = frame.rect;
  const unit = projection.sourceUnit;
  return (
    <Fragment>
      {props.showShadow !== false && (
        <View
          pointerEvents="none"
          style={{
            position: 'absolute',
            left: projection.shadow.x - 9 * props.worldUnit,
            top: projection.shadow.y - 2 * props.worldUnit,
            width: 18 * props.worldUnit,
            height: 4 * props.worldUnit,
            borderRadius: 20 * props.worldUnit,
            backgroundColor: 'rgba(20,24,24,0.22)',
            zIndex: projection.depth,
          }}
        />
      )}
      <View
        pointerEvents="none"
        // @ts-expect-error dataSet is a react-native-web prop, as in AtlasWalk.
        dataSet={{ pixel: 'true' }}
        style={{
          position: 'absolute',
          left: projection.left + frame.cropOffset[0] * unit,
          top: projection.top + frame.cropOffset[1] * unit,
          width: width * unit,
          height: height * unit,
          overflow: 'hidden',
          zIndex: projection.depth,
        }}
      >
        <Image
          source={props.resolveImage(frame.asset)}
          resizeMode="stretch"
          accessible={false}
          style={{
            position: 'absolute',
            left: -x * unit,
            top: -y * unit,
            width: frame.atlasSize[0] * unit,
            height: frame.atlasSize[1] * unit,
          }}
        />
      </View>
    </Fragment>
  );
}

/** Add roster guests to the actual shared world renderer through its existing
 * supported slot. Foot coordinates are region-local, matching AtlasWalk. The
 * legacy playable companion still belongs to AtlasWalk's owner. */
export function MyGameAtlasWalk({
  guests,
  ...world
}: ComponentProps<typeof AtlasWalk> & {
  guests: readonly (MyGameWorldCharacterProps & { key: string })[];
}) {
  return (
    <AtlasWalk
      {...world}
      scene={
        <Fragment>
          {world.scene}
          {guests.map(({ key, ...guest }) => (
            <MyGameWorldCharacter key={key} {...guest} />
          ))}
        </Fragment>
      }
    />
  );
}
