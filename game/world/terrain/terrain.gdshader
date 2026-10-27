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

int prio_of(int m) {
	return byte_at(texelFetch(meta_tex, ivec2(m, 0), 0), 0);
}

int fill_code(int m, ivec2 p) {
	int slot = byte_at(texelFetch(meta_tex, ivec2(m, 0), 0), 1);
	ivec2 o = ivec2((slot % fill_cols) * period, (slot / fill_cols) * period);
	vec4 c = texelFetch(fills_tex, o + ivec2(p.x % period, p.y % period), 0);
	return byte_at(c, 0) + 256 * byte_at(c, 1);
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

int pair_of(int upper, int lower) {
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
	q[0] = material_at(i - 1, j - 1);
	q[1] = material_at(i, j - 1);
	q[2] = material_at(i - 1, j);
	q[3] = material_at(i, j);
	// the distinct materials present, by priority (insertion sort of up to four)
	int ms[4];
	int n = 0;
	for (int k = 0; k < 4; k++) {
		int m = q[k];
		if (m == 0) {
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
		while (at > 0 && prio_of(ms[at - 1]) > prio_of(m)) {
			ms[at] = ms[at - 1];
			at--;
		}
		ms[at] = m;
		n++;
	}
	if (n == 0) {
		discard;
	}
	int code = fill_code(ms[0], p);
	int below = ms[0];
	for (int s = 1; s < n; s++) {
		int m = ms[s];
		int pm = prio_of(m);
		int bits = 0;
		for (int k = 0; k < 4; k++) {
			if (q[k] > 0 && prio_of(q[k]) >= pm) {
				bits |= (1 << k);
			}
		}
		int fu = fill_code(m, p);
		if (bits == 15) {
			code = fu;
		} else {
			int pr = pair_of(m, below);
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
	COLOR = vec4(texelFetch(lut_tex, ivec2(code, 0), 0).rgb, 1.0);
}
