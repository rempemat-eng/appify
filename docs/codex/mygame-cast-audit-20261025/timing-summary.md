# Timing and scale review

Source: pinned main in report.json. Values are seconds, shown as art release → canonical release. These are metadata comparisons, not a new balance proposal. All 69 supplied action clips require duration or release retiming; Pendle's powered secondary has no clip to retime.

| Character | Art body target (texels) | Primary | Powered primary | Secondary | Powered secondary | Special |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Bramble | 74 | 0.3300 → 0.1596 | 0.3299 → 0.1596 | 0.3300 → 0.1824 | 0.3300 → 0.1824 | 0.3800 → 0.2800 |
| Morel | 73 | 0.3300 → 0.2356 | 0.3300 → 0.2356 | 0.3300 → 0.1824 | 0.3300 → 0.1824 | 0.3800 → 0.2800 |
| Velvet | 76 | 0.3299 → 0.1292 | 0.3300 → 0.1292 | 0.3300 → 0.1824 | 0.3300 → 0.1824 | 0.3799 → 0.2800 |
| Cairn | 104 | 0.5600 → 0.3264 | 0.5599 → 0.3264 | 0.5601 → 0.3456 | 0.5601 → 0.3456 | 0.3800 → 0.2800 |
| Iona | 75 | 0.3300 → 0.1824 | 0.3300 → 0.1824 | 0.3301 → 0.2470 | 0.3301 → 0.2470 | 0.3800 → 0.2800 |
| Tam | 73 | 0.3300 → 0.1216 | 0.3300 → 0.1216 | 0.3299 → 0.1824 | 0.3299 → 0.1824 | 0.3800 → 0.2800 |
| Brine | 73 | 0.3298 → 0.2432 | 0.3301 → 0.2432 | 0.3300 → 0.1824 | 0.3300 → 0.1824 | 0.3800 → 0.2800 |
| Pendle | 74 | 0.3300 → 0.1634 | 0.3301 → 0.3420 | 0.3300 → 0.1824 | missing | 0.3800 → 0.2800 |
| Mirra | 74 | 0.3301 → 0.1634 | 0.3300 → 0.1634 | 0.3299 → 0.1824 | 0.3299 → 0.1824 | 0.3800 → 0.2800 |
| Ashe | 75 | 0.3300 → 0.1824 | 0.3300 → 0.1824 | 0.3299 → 0.2470 | 0.3299 → 0.2470 | 0.3799 → 0.2800 |
| Clack | 76 | 0.3300 → 0.3840 | 0.3299 → 0.3360 | 0.3301 → 0.3456 | 0.3301 → 0.3456 | 0.3800 → 0.2800 |
| Nix | 74 | 0.3300 → 0.0798 | 0.3300 → 0.0798 | 0.3299 → 0.0500 | 0.3299 → 0.0500 | 0.3800 → 0.2800 |
| Rook | 74 | 0.3299 → 0.1140 | 0.3301 → 0.1140 | 0.2200 → 0.0500 | 0.2200 → 0.0500 | 0.3800 → 0.2800 |
| Mote | 74 | 0.3301 → 0.1824 | 0.3300 → 0.1824 | 0.3299 → 0.1824 | 0.3299 → 0.1824 | 0.1701 → 0.2800 |

The retiming file preserves the authored contact index and separately fits preparation and recovery to the canonical release and completion. A uniform whole-clip speed multiplier would put contact at the wrong fraction of the action. Strongly compressed preparation, especially Nix and Rook, needs a pose/timing review by Claude A before import. These schedules do not author missing variants, wall policy, physics or height.

Body targets are manifest declarations, not independently measured rendered silhouettes. At the 960×540 art grid shown 2×, a 74-texel body targets 148 display pixels, and Cairn's updated 104 targets 208. The art cell is 160×144 with foot pivot (80,136). Do not rescale that cell by density 3 again. The current walk speeds are authored texels/second; mapping the recovered planar speeds remains an explicit owner decision, including foot-slide review.
