shader_type canvas_item;
// Sharp bilinear: nearest-neighbour inside each texel, a one-device-pixel linear blend at texel edges.
// Used only when the window is not a whole multiple of 960 x 540 (main/pixel_screen.gd); whole
// multiples draw with plain nearest filtering and no shader.
uniform float scale = 2.0;

void fragment() {
	vec2 size = 1.0 / TEXTURE_PIXEL_SIZE;
	vec2 texel = UV * size;
	vec2 base = floor(texel);
	vec2 d = fract(texel) - 0.5;
	float keep = 0.5 - 0.5 / scale;
	vec2 f = (d - clamp(d, -keep, keep)) * scale + 0.5;
	COLOR = texture(TEXTURE, (base + f) / size);
}
