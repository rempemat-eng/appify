"""The native library: art drawn natively at any density (the first finished screen, 21 Oct).

raster   parts, shading, outline (the house style's rendering)
terrain  height, faces, water and paths through the cliff core
flora    trees, shrubs and ground plants
props    the made things (seats, lanterns, woodpiles, stones, bridges)
ground   the floor, its dressing, light pools and shadows
rig      the character rig (proportions, parts, facings, timing) and its folk
animate  the world's animators (water, the fall, the lantern)
screen   a screen from a layout and a biome: layers, objects, walk grid
"""
import json
import os

BIOMES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'biomes')


def biome(name: str) -> dict:
    with open(os.path.join(BIOMES, name + '.json')) as f:
        return json.load(f)
