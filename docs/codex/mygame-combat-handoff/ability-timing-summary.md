# Canonical action timing quick reference

Times are seconds, shown to four decimal places. The JSON is authoritative. Format: total / release. These are simulation times, not new-art frame indices. Form time begins at special release.

| Character | Base primary | Powered primary | Base secondary | Powered secondary | Special entry | Form |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Bramble | 0.4200 / 0.1596 | 0.4200 / 0.1596 | 0.4800 / 0.1824 | 0.4800 / 0.1824 | 0.6500 / 0.2800 | 8 |
| Morel | 0.6200 / 0.2356 | 0.6200 / 0.2356 | 0.4800 / 0.1824 | 0.4800 / 0.1824 | 0.6500 / 0.2800 | 8 |
| Velvet | 0.3400 / 0.1292 | 0.3400 / 0.1292 | 0.4800 / 0.1824 | 0.4800 / 0.1824 | 0.6500 / 0.2800 | 8 |
| Cairn | 0.6800 / 0.3264 | 0.6800 / 0.3264 | 0.7200 / 0.3456 | 0.7200 / 0.3456 | 0.6500 / 0.2800 | 8 |
| Iona | 0.4800 / 0.1824 | 0.4800 / 0.1824 | 0.6500 / 0.2470 | 0.6500 / 0.2470 | 0.6500 / 0.2800 | 8 |
| Tam | 0.3200 / 0.1216 | 0.3200 / 0.1216 | 0.4800 / 0.1824 | 0.4800 / 0.1824 | 0.6500 / 0.2800 | 8 |
| Brine | 0.6400 / 0.2432 | 0.6400 / 0.2432 | 0.4800 / 0.1824 | 0.4800 / 0.1824 | 0.6500 / 0.2800 | 8 |
| Pendle | 0.4300 / 0.1634 | 0.9000 / 0.3420 | 0.4800 / 0.1824 | 0.4800 / 0.1824 | 0.6500 / 0.2800 | 8 |
| Mirra | 0.4300 / 0.1634 | 0.4300 / 0.1634 | 0.4800 / 0.1824 | 0.4800 / 0.1824 | 0.6500 / 0.2800 | 8 |
| Ashe | 0.4800 / 0.1824 | 0.4800 / 0.1824 | 0.6500 / 0.2470 | 0.6500 / 0.2470 | 0.6500 / 0.2800 | 8 |
| Clack | 0.8000 / 0.3840 | 0.7000 / 0.3360 | 0.7200 / 0.3456 | 0.7200 / 0.3456 | 0.6500 / 0.2800 | 8 |
| Nix | 0.2100 / 0.0798 | 0.2100 / 0.0798 | 0.4800 / 0.0500 | 0.4800 / 0.0500 | 0.6500 / 0.2800 | 7 |
| Rook | 0.3000 / 0.1140 | 0.3000 / 0.1140 | 0.5500 / 0.0500 | 0.5500 / 0.0500 | 0.6500 / 0.2800 | 10 |
| Mote | 0.4800 / 0.1824 | 0.4800 / 0.1824 | 0.4800 / 0.1824 | 0.4800 / 0.1824 | 0.6500 / 0.2800 | 8 |

Special cooldown is 25 seconds from commitment. Secondary cooldowns are per character in `canonical/abilities-v1.json`; primary cooldown follows its canonical duration. Guard raise is 0.18 seconds, with held/recovery rules in the data. A form expiring in flight does not rewrite a projectile’s captured launch state.

Pendle powered Q is a stock strike, Brine Q branches on a valid tether, and Velvet’s counter branches on its independent timer. Ashe’s natural expiry finisher has an immediate mechanical release, rather than a new delayed action. All new-art release indices and facing attachments must be authored separately.
