"""Encoded-framebuffer grade. This is the contract the shader has to match.

The framebuffer is already encoded. Nothing here converts to linear light.
`src` is premultiplied RGBA in 0..1, the same values `texture2D` returns.
"""

import math


def clamp(value, lo=0.0, hi=1.0):
    return min(hi, max(lo, value))


def mix(a, b, t):
    return a + (b - a) * t


def luma(color):
    return color[0] * 0.2126 + color[1] * 0.7152 + color[2] * 0.0722


def smoothstep(edge0, edge1, value):
    span = edge1 - edge0
    t = clamp((value - edge0) / span) if span != 0 else 0.0
    return t * t * (3.0 - 2.0 * t)


def s_curve(x, contrast):
    y = clamp(x) - 0.5
    denom = 1.0 + (contrast - 1.0) * 2.0 * abs(y)
    return clamp(y * contrast / max(denom, 0.0001) + 0.5)


def fract(value):
    return value - math.floor(value)


def hash2(px, py):
    p3x = fract(px * 0.1031)
    p3y = fract(py * 0.1031)
    p3z = fract(px * 0.1031)
    dot = p3x * (p3y + 33.33) + p3y * (p3z + 33.33) + p3z * (p3x + 33.33)
    p3x += dot
    p3y += dot
    p3z += dot
    return fract((p3x + p3y) * p3z)


def skin_mask(color, y):
    rb = color[0] - color[2]
    rg = color[0] - color[1]
    sat = max(color) - min(color)
    hue = smoothstep(0.03, 0.10, rb) * smoothstep(0.0, 0.05, rg)
    sat_ok = smoothstep(0.05, 0.14, sat) * (1.0 - smoothstep(0.50, 0.75, sat))
    y_ok = smoothstep(0.18, 0.32, y) * (1.0 - smoothstep(0.72, 0.90, y))
    return clamp(hue * sat_ok * y_ok)


def add_grain(color, uv, grain, grain_time, tex_w, tex_h):
    px = uv[0] * max(tex_w, 1.0)
    py = uv[1] * max(tex_h, 1.0)
    fine = hash2(math.floor(px) + grain_time, math.floor(py) + grain_time * 0.37) - 0.5
    coarse = hash2(
        math.floor(px * 0.42) + grain_time * 1.3,
        math.floor(py * 0.62) + grain_time * 0.7,
    ) - 0.5
    band = hash2(math.floor(py * 0.5), grain_time) - 0.5
    noise = fine * 0.45 + coarse * 1.05 + band * 0.22
    y = luma(color)
    mask = mix(0.78, 1.0, smoothstep(0.0, 0.22, y))
    mask *= mix(1.0, 0.62, smoothstep(0.72, 1.0, y))
    amp = noise * grain * mask
    return [color[0] + amp, color[1] + amp, color[2] + amp]


def grade_pixel(src, uv, params, tex_w, tex_h):
    if src[3] < 0.001:
        return [0.0, 0.0, 0.0, 0.0]
    amount = clamp(params["intensity"])
    original = [src[0] / src[3], src[1] / src[3], src[2] / src[3]]
    color = [channel * math.pow(2.0, params["exposure"]) for channel in original]
    black_point = clamp(-params["blacks"]) * 0.25
    lifted = [clamp((channel - black_point) / max(1.0 - black_point, 0.001)) for channel in color]
    y = luma(lifted)
    shadow_mask = smoothstep(0.0, 0.16, y) * (1.0 - smoothstep(0.16, 0.55, y))
    high_mask = smoothstep(0.58, 0.94, y)
    color = [channel * mix(1.0, 1.0 + params["shadows"], shadow_mask) for channel in lifted]
    color = [channel * mix(1.0, 1.0 + params["highlights"], high_mask) for channel in color]
    color = [clamp(channel) for channel in color]
    curve = max(params["contrast"], 0.05)
    color = [s_curve(channel, curve) for channel in color]
    gamma = max(params["gamma"], 0.05)
    color = [math.pow(max(channel, 0.0), gamma) for channel in color]
    y = luma(color)
    sat = clamp(params["saturation"], 0.0, 2.0)
    color = [mix(y, channel, sat) for channel in color]
    t = clamp(params["temperature"], -1.0, 1.0)
    color[0] *= 1.0 + 0.25 * t
    color[1] *= 1.0 + 0.04 * t
    color[2] *= 1.0 - 0.16 * t
    color = [clamp(channel) for channel in color]
    y = luma(color)
    shadow_tint = 1.0 - smoothstep(0.0, 0.18, y)
    high_tint = smoothstep(0.62, 0.96, y)
    mid = smoothstep(0.38, 0.50, y) * (1.0 - smoothstep(0.50, 0.64, y))
    skin = skin_mask(color, y) * clamp(params["skin_protect"])
    teal_cut = clamp(mid + skin)
    teal_amt = params["shadow_teal"] * shadow_tint * (1.0 - teal_cut)
    warm_amt = params["highlight_warmth"] * high_tint * (1.0 - mid)
    color[0] += -0.40 * teal_amt + 0.90 * warm_amt
    color[1] += 0.12 * teal_amt + 0.22 * warm_amt
    color[2] += 0.50 * teal_amt - 0.55 * warm_amt
    if params["grain"] > 0.001:
        color = add_grain(color, uv, params["grain"], params["grain_time"], tex_w, tex_h)
    vig = smoothstep(0.28, 0.78, math.hypot(uv[0] - 0.5, uv[1] - 0.5))
    gain = 1.0 - clamp(params["vignette"]) * vig
    color = [clamp(channel * gain) for channel in color]
    color = [mix(original[i], color[i], amount) for i in range(3)]
    return [color[0] * src[3], color[1] * src[3], color[2] * src[3], src[3]]


def identity_grade(**overrides):
    params = {
        "intensity": 1.0,
        "exposure": 0.0,
        "contrast": 1.0,
        "highlights": 0.0,
        "shadows": 0.0,
        "blacks": 0.0,
        "saturation": 1.0,
        "temperature": 0.0,
        "shadow_teal": 0.0,
        "highlight_warmth": 0.0,
        "gamma": 1.0,
        "vignette": 0.0,
        "skin_protect": 0.0,
        "grain": 0.0,
        "grain_time": 0.0,
    }
    params.update(overrides)
    return params


def sharpen_pixel(src, neighbors, amount):
    """`neighbors` is left, right, up, down. All values are premultiplied."""
    if src[3] < 0.98 or amount <= 0.001:
        return list(src)
    if min(sample[3] for sample in neighbors) < 0.98:
        return list(src)
    color = [src[i] / src[3] for i in range(3)]
    blur = [0.0, 0.0, 0.0]
    for sample in neighbors:
        for channel in range(3):
            blur[channel] += sample[channel] / sample[3]
    blur = [channel * 0.25 for channel in blur]
    detail = luma(color) - luma(blur)
    graded = [clamp(color[i] + detail * amount) for i in range(3)]
    return [graded[0] * src[3], graded[1] * src[3], graded[2] * src[3], src[3]]
