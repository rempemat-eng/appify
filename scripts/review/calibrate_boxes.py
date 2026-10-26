"""Prop boxes in Eastward's official shots (native 640 x 360 px), used for the detail bands and as
clean props in the false-positive count. Numbers only; the shots stay local."""
EW = {
 "17": (
  (
   135,
   47,
   162,
   112,
   "churns",
   "prop"
  ),
  (
   340,
   40,
   392,
   83,
   "churns2",
   "prop"
  ),
  (
   410,
   15,
   472,
   55,
   "bench",
   "prop"
  ),
  (
   305,
   177,
   450,
   218,
   "fence",
   "prop"
  ),
  (
   460,
   165,
   550,
   250,
   "rocks",
   "stone"
  ),
  (
   120,
   165,
   200,
   215,
   "bale",
   "prop"
  )
 ),
 "13": (
  (
   375,
   20,
   415,
   125,
   "lamp",
   "prop"
  ),
  (
   410,
   155,
   470,
   220,
   "pot",
   "prop"
  ),
  (
   345,
   150,
   395,
   235,
   "tree",
   "foliage"
  ),
  (
   510,
   150,
   565,
   230,
   "tree2",
   "foliage"
  ),
  (
   505,
   295,
   540,
   350,
   "churns3",
   "prop"
  ),
  (
   325,
   247,
   350,
   268,
   "rocks2",
   "stone"
  )
 ),
 "12": (
  (
   180,
   200,
   248,
   235,
   "bench2",
   "prop"
  ),
  (
   387,
   200,
   420,
   248,
   "postbox",
   "prop"
  ),
  (
   465,
   110,
   590,
   230,
   "redtree",
   "foliage"
  ),
  (
   175,
   65,
   245,
   165,
   "pines",
   "foliage"
  ),
  (
   497,
   205,
   555,
   235,
   "rocks3",
   "stone"
  )
 )
}


# Ground planes in the same shots (native px): calm fields people walk on, measured for the ground
# band (bands.ground_plane): the dungeon floor in shade (06), a lawn and path (13), the yard's dirt
# and its lawn (17). Boxes stay clear of props, people, light sources and effects.
EW_GROUND = {
 "06": ((160, 190, 240, 250, "dungeon floor"), (165, 255, 225, 300, "dungeon floor south")),
 "13": ((200, 175, 290, 230, "grass and path"),),
 "17": ((20, 200, 150, 245, "yard dirt"), (200, 200, 300, 250, "yard dirt east"), (480, 250, 560, 300, "lawn")),
}
