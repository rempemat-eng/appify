// The terrain kit's renderer (docs/world-editor.md, "The kit"). The same algorithm as
// scripts/art/kit/compose.py, texel for texel; the GdUnit test test/test_terrain.gd holds them equal.
//
// The logical grid holds one material per 24-texel cell (cells_tex R). The picture is drawn on the
// dual grid: a display tile is centred on a cell corner and looks at its four cells. The lowest
// material there is drawn from its periodic fill by world position; each higher one is laid over
// it with the transition tile of its 4-bit mask, the variant picked by a hash, each texel an
// operation on the palette code below (keep, upper fill + delta, delta, absolute code).
shader_type canvas_item;
render_mode unshaded;

uniform sampler2D cells_tex : filter_nearest, repeat_disable;  // R material id, G tier
uniform sampler2D fills_tex : filter_nearest, repeat_disable;  // fills in a grid of fill_cols
uniform sampler2D over_tex : filter_nearest, repeat_disable;   // transitions, stacked by index
uniform sampler2D lut_tex : filter_nearest, repeat_disable;    // palette code -> RGB
uniform sampler2D meta_tex : filter_nearest, repeat_disable;   // row 0: priority, fill slot, present; row 1+u: pair table
uniform sampler2D noise_tex : filter_nearest, repeat_disable;  // smooth periodic noise (L) for the water's depth bands
uniform sampler2D shadow_tex : filter_nearest, repeat_disable; // R: cast shadow steps (0 to 2) per texel
uniform ivec2 grid = ivec2(1, 1);
uniform int period = 768;
uniform int variants = 4;
uniform int fill_cols = 4;
uniform int cell = 24;
uniform int profiles = 3;       // edges.OFFS: outline offsets where it crosses a tile border
uniform int atlas_cols = 64;    // tiles across a transition's atlas block
uniform int pair_rows = 9;      // atlas rows per transition

varying vec2 local_pos;

void vertex() {
	local_pos = VERTEX;
}

int byte_at(vec4 c, int ch) {
	return int(round(c[ch] * 255.0));
}

int material_at(int cx, int cy) {
	ivec2 q = clamp(ivec2(cx, cy), ivec2(0), grid - ivec2(1));
	return byte_at(texelFetch(cells_tex, q, 0), 0);
}

// a cell's layer: its material and its tier (cells_tex G), as m + 64 * tier
int layer_at(int cx, int cy) {
	ivec2 q = clamp(ivec2(cx, cy), ivec2(0), grid - ivec2(1));
	vec4 c = texelFetch(cells_tex, q, 0);
	return byte_at(c, 0) + 64 * byte_at(c, 1);
}

int prio_of(int m) {
	return byte_at(texelFetch(meta_tex, ivec2(m, 0), 0), 0);
}

// a layer's priority: higher tiers lie over lower ones, then the material's own priority
int eprio(int L) {
	return (L / 64) * 256 + prio_of(L % 64);
}

bool is_strip(int m) {
	return byte_at(texelFetch(meta_tex, ivec2(m, 0), 0), 2) == 2;
}

int step_code(int code, int d) {
	if (code < 0) {
		return code;
	}
	int t = code % 8;
	if (t >= 6) {
		return code;
	}
	return code - t + clamp(t + d, 0, 5);
}

bool lt2(int d2, int t, int j) {
	int tj = t - j;
	return tj > 0 && d2 < tj * tj;
}

// softground.water's depth from the true distance to the shore cells around (compose.water_delta)
int water_delta(int m, ivec2 p) {
	ivec2 c = p / cell;
	int far = 1 << 20;
	int dN = far;
	int dO = far;
	int d = far;
	for (int oy = -2; oy <= 2; oy++) {
		for (int ox = -2; ox <= 2; ox++) {
			ivec2 q = c + ivec2(ox, oy);
			if (q.x < 0 || q.y < 0 || q.x >= grid.x || q.y >= grid.y || material_at(q.x, q.y) == m) {
				continue;
			}
			int ddx = max(max(q.x * cell - p.x, p.x - (q.x * cell + cell - 1)), 0);
			int ddy = max(max(q.y * cell - p.y, p.y - (q.y * cell + cell - 1)), 0);
			int d2 = ddx * ddx + ddy * ddy;
			d = min(d, d2);
			if (oy < 0 && ddx == 0) {
				dN = min(dN, d2);
			} else {
				dO = min(dO, d2);
			}
		}
	}
	int j = (byte_at(texelFetch(noise_tex, ivec2(p.x % period, p.y % period), 0), 0) * 14) / 255 - 7;
	bool chk = ((p.x + p.y) % 2) == 0;
	bool n16 = lt2(dN, 16, j);
	bool n21 = lt2(dN, 21, j);
	int o = 0;
	if (n16) { o = -1; }
	if (!n16 && n21 && chk) { o = -1; }
	if (!lt2(d, 30, j) && !n16) { o = -1; }
	if (!lt2(d, 26, j) && lt2(d, 30, j) && !n21 && chk) { o = -1; }
	if (!n21 && lt2(dO, 5, 0)) { o = 1; }
	return o;
}

int fill_code(int m, ivec2 p) {
	vec4 mt = texelFetch(meta_tex, ivec2(m, 0), 0);
	int slot = byte_at(mt, 1);
	ivec2 o = ivec2((slot % fill_cols) * period, (slot / fill_cols) * period);
	int fy = p.y % period;
	if (byte_at(mt, 2) == 2) {
		// a face's strip, by depth below the rim (compose.strip_rows)
		int strip = byte_at(mt, 3);
		int cx = p.x / cell;
		int cy = p.y / cell;
		if (material_at(cx, cy) == m) {
			int run = 0;
			for (int k = 1; k <= 8; k++) {
				if (cy - k >= 0 && material_at(cx, cy - k) == m && run == k - 1) {
					run = k;
				}
			}
			fy = run * cell + p.y % cell;
		} else if (cy + 1 < grid.y && material_at(cx, cy + 1) == m) {
			fy = 0;
		} else {
			fy = strip - 1;
		}
		fy = clamp(fy, 0, strip - 1);
	}
	vec4 c = texelFetch(fills_tex, o + ivec2(p.x % period, fy), 0);
	int code = byte_at(c, 0) + 256 * byte_at(c, 1);
	if (byte_at(mt, 2) == 3) {
		code = step_code(code, water_delta(m, p));
	}
	return code;
}


// build.Kit.pair_for: a face's own pair, across tiers the upper's '^' pair (column 63), else the
// exact pair, then the upper's '*' pair (column 0)
int pair_of(int upper, int lower, bool tiers_differ) {
	if (tiers_differ && !is_strip(lower)) {
		return byte_at(texelFetch(meta_tex, ivec2(63, 1 + upper), 0), 0) - 1;
	}
	int v = byte_at(texelFetch(meta_tex, ivec2(lower, 1 + upper), 0), 0);
	if (v == 0) {
		v = byte_at(texelFetch(meta_tex, ivec2(0, 1 + upper), 0), 0);
	}
	return v - 1;
}

int variant_of(int i, int j, int m) {
	uint h = (uint(i) * 0x8DA6B343u) ^ (uint(j) * 0xD8163841u) ^ (uint(m) * 0xCB1AB31Fu);
	h = h ^ (h >> 15u);
	h = h * 0x2C1B3C6Du;
	h = h ^ (h >> 12u);
	return int(h % uint(variants));
}

int profile_of(int a, int b, int c, int m) {
	uint h = (uint(a) * 0x9E3779B1u) ^ (uint(b) * 0x85EBCA77u) ^ (uint(c) * 0xC2B2AE3Du) ^ (uint(m) * 0x27D4EB2Fu);
	h = h ^ (h >> 16u);
	h = h * 0x7FEB352Du;
	h = h ^ (h >> 15u);
	return int(h % uint(profiles));
}

// which of the tile's borders (n, e, s, w) the outline crosses for a mask
bvec4 crossings(int k) {
	bool nw = (k & 1) != 0;
	bool ne = (k & 2) != 0;
	bool sw = (k & 4) != 0;
	bool se = (k & 8) != 0;
	return bvec4(nw != ne, ne != se, sw != se, nw != sw);
}

int n_crossings(int k) {
	bvec4 c = crossings(k);
	return int(c.x) + int(c.y) + int(c.z) + int(c.w);
}

int ipow(int b, int e) {
	int r = 1;
	for (int k = 0; k < e; k++) {
		r *= b;
	}
	return r;
}

// edges.layout: per mask, its crossing profiles times the variants
int tile_index(int i, int j, int m, int bits) {
	int base = 0;
	for (int k = 1; k < bits; k++) {
		base += ipow(profiles, n_crossings(k)) * variants;
	}
	bvec4 c = crossings(bits);
	int combo = 0;
	if (c.x) { combo = combo * profiles + profile_of(i, j - 1, 0, m); }
	if (c.y) { combo = combo * profiles + profile_of(i, j, 1, m); }
	if (c.z) { combo = combo * profiles + profile_of(i, j, 0, m); }
	if (c.w) { combo = combo * profiles + profile_of(i - 1, j, 1, m); }
	return base + combo * variants + variant_of(i, j, m);
}

void fragment() {
	ivec2 p = ivec2(floor(local_pos));
	int half_cell = cell / 2;
	int i = (p.x + half_cell) / cell;
	int j = (p.y + half_cell) / cell;
	ivec2 l = ivec2(p.x + half_cell - i * cell, p.y + half_cell - j * cell);
	int q[4];
	q[0] = layer_at(i - 1, j - 1);
	q[1] = layer_at(i, j - 1);
	q[2] = layer_at(i - 1, j);
	q[3] = layer_at(i, j);
	// the distinct layers present, by priority (insertion sort of up to four)
	int ms[4];
	int n = 0;
	for (int k = 0; k < 4; k++) {
		int m = q[k];
		if (m % 64 == 0) {
			continue;
		}
		bool seen = false;
		for (int s = 0; s < n; s++) {
			if (ms[s] == m) {
				seen = true;
			}
		}
		if (seen) {
			continue;
		}
		int at = n;
		while (at > 0 && eprio(ms[at - 1]) > eprio(m)) {
			ms[at] = ms[at - 1];
			at--;
		}
		ms[at] = m;
		n++;
	}
	if (n == 0) {
		discard;
	}
	int code = fill_code(ms[0] % 64, p);
	int below = ms[0];
	for (int s = 1; s < n; s++) {
		int m = ms[s];
		int pm = eprio(m);
		int bits = 0;
		for (int k = 0; k < 4; k++) {
			if (q[k] % 64 > 0 && eprio(q[k]) >= pm) {
				bits |= (1 << k);
			}
		}
		int fu = fill_code(m % 64, p);
		if (bits == 15) {
			code = fu;
		} else {
			int pr = pair_of(m % 64, below % 64, m / 64 != below / 64);
			if (pr < 0) {
				// no transition drawn yet: a hard cell edge (the library gate refuses such a zone)
				int qx = l.x < half_cell ? 0 : 1;
				int qy = l.y < half_cell ? 0 : 1;
				if ((bits & (1 << (qy * 2 + qx))) != 0) {
					code = fu;
				}
			} else {
				int ti = tile_index(i, j, m, bits);
				ivec2 at = ivec2((ti % atlas_cols) * cell, (pr * pair_rows + ti / atlas_cols) * cell);
				vec4 t = texelFetch(over_tex, at + l, 0);
				int op = byte_at(t, 0);
				int val = byte_at(t, 1) + 256 * byte_at(t, 2);
				if (op == 1) {
					code = step_code(fu, val - 128);
				} else if (op == 2) {
					code = step_code(code, val - 128);
				} else if (op == 3) {
					code = val;
				}
			}
		}
		below = m;
	}
	code = step_code(code, -byte_at(texelFetch(shadow_tex, p, 0), 0));
	COLOR = vec4(texelFetch(lut_tex, ivec2(code, 0), 0).rgb, 1.0);
}
