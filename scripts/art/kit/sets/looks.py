"""The prop sets' buildings drawn by the house builder (scripts/art/native/houses.building): their
looks, as data with no painter imports, so the kit index (scripts/art/kit/props.py, volume_look)
can cast each one's volume shadow (scripts/art/native/volume.house_cast) without painting the set.
"""

# The water mill at the size guide's `water_mill` (round 5 of the detail audit, R5-1): 104 world px
# wide (14 x 7 cells), two storeys and a loft, 76 to the eaves, built by the house builder
# (houses.building) like the Crossroads houses, whose eaves are 40: a loading door 32 x 22 on the
# yard side with a hoist door and its beam above, the wheel 44 across on the water side.
MILL_SPEC = dict(w=104, depth=56, wall_h=76, roof_h=40, wall='stone', roof='slate', paint='timber', doors=[[18, 'timber']],
                 door_w=22, door_h=32, windows=[44], win_w=12, win_h=12, win_top=34, shutters=False,
                 # round 6 of the detail audit (R6-5, R6-6): a calm slate draw with the lowest third a tone
                 # darker, no moss stuck mid-slate (the mill lays its own cushions in the joints) and a
                 # stove chimney to break the roof's field. Its eave shadow is the slate's own band
                 # (volume.eave_band, 16 art px; Claude A on round 9's P9-1: Eastward's slate eaves are
                 # E 10 to 12, so the 8 world px band R6-6 asked for was the deepest front studied)
                 slate_calm=True, eave_dark=True, roof_moss=0, roof_lichen=0, chimney=[88], chimney_w=7, chimney_h=12)

# {piece id: look}: the piece's picture stands on the look's foot (the middle of its front foot line)
VOLUME_LOOKS = {
    'mill_wheel': MILL_SPEC,
}
