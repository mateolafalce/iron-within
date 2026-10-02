"""Compile the Cogl shaders as GLES 1.00 and compare pixels to the contract."""

import ctypes
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from grade_reference import grade_pixel, identity_grade, sharpen_pixel

ROOT = pathlib.Path(__file__).resolve().parents[1]

EGL_PLATFORM_SURFACELESS_MESA = 0x31DD
EGL_OPENGL_ES_API = 0x30A0
EGL_CONTEXT_CLIENT_VERSION = 0x3098
EGL_NONE = 0x3038
EGL_RED_SIZE = 0x3024
EGL_GREEN_SIZE = 0x3025
EGL_BLUE_SIZE = 0x3026
EGL_ALPHA_SIZE = 0x3028
EGL_RENDERABLE_TYPE = 0x3040
EGL_OPENGL_ES2_BIT = 0x0004
EGL_SURFACE_TYPE = 0x3033
EGL_PBUFFER_BIT = 0x0001

GL_FRAGMENT_SHADER = 0x8B30
GL_VERTEX_SHADER = 0x8B31
GL_COMPILE_STATUS = 0x8B81
GL_LINK_STATUS = 0x8B82
GL_INFO_LOG_LENGTH = 0x8B84
GL_TEXTURE_2D = 0x0DE1
GL_RGBA = 0x1908
GL_UNSIGNED_BYTE = 0x1401
GL_FLOAT = 0x1406
GL_NEAREST = 0x2600
GL_CLAMP_TO_EDGE = 0x812F
GL_TEXTURE_MIN_FILTER = 0x2801
GL_TEXTURE_MAG_FILTER = 0x2800
GL_TEXTURE_WRAP_S = 0x2802
GL_TEXTURE_WRAP_T = 0x2803
GL_FRAMEBUFFER = 0x8D40
GL_COLOR_ATTACHMENT0 = 0x8CE0
GL_COLOR_BUFFER_BIT = 0x4000
GL_TRIANGLE_STRIP = 0x0005
GL_FALSE = 0

VERTEX = """
#version 100
attribute vec2 a_pos;
attribute vec2 a_uv;
varying vec2 v_uv;
void main() {
    v_uv = a_uv;
    gl_Position = vec4(a_pos, 0.0, 1.0);
}
"""


def to_gles(source):
    body = source.replace("cogl_tex_coord_in[0].st", "v_uv")
    body = body.replace("cogl_color_out", "gl_FragColor")
    header = "#version 100\nprecision highp float;\nvarying vec2 v_uv;\n"
    return header + body


class GL:
    def __init__(self):
        self.egl = ctypes.CDLL("libEGL.so.1")
        self.gl = ctypes.CDLL("libGLESv2.so.2")
        self._bind()
        self._context()

    def _bind(self):
        egl = self.egl
        gl = self.gl
        egl.eglGetPlatformDisplay.restype = ctypes.c_void_p
        egl.eglGetPlatformDisplay.argtypes = [ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p]
        egl.eglInitialize.restype = ctypes.c_int
        egl.eglInitialize.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
        egl.eglBindAPI.restype = ctypes.c_int
        egl.eglBindAPI.argtypes = [ctypes.c_uint]
        egl.eglChooseConfig.restype = ctypes.c_int
        egl.eglChooseConfig.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_int, ctypes.POINTER(ctypes.c_int),
        ]
        egl.eglCreateContext.restype = ctypes.c_void_p
        egl.eglCreateContext.argtypes = [
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_int),
        ]
        egl.eglMakeCurrent.restype = ctypes.c_int
        egl.eglMakeCurrent.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        egl.eglGetError.restype = ctypes.c_int
        egl.eglGetError.argtypes = []

        def fn(name, restype, argtypes):
            func = getattr(gl, name)
            func.restype = restype
            func.argtypes = argtypes
            return func

        self.create_shader = fn("glCreateShader", ctypes.c_uint, [ctypes.c_uint])
        self.shader_source = fn("glShaderSource", None, [
            ctypes.c_uint, ctypes.c_int, ctypes.POINTER(ctypes.c_char_p), ctypes.POINTER(ctypes.c_int),
        ])
        self.compile_shader = fn("glCompileShader", None, [ctypes.c_uint])
        self.get_shader_iv = fn("glGetShaderiv", None, [ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_int)])
        self.get_shader_log = fn("glGetShaderInfoLog", None, [
            ctypes.c_uint, ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.c_char_p,
        ])
        self.create_program = fn("glCreateProgram", ctypes.c_uint, [])
        self.attach = fn("glAttachShader", None, [ctypes.c_uint, ctypes.c_uint])
        self.link = fn("glLinkProgram", None, [ctypes.c_uint])
        self.get_program_iv = fn("glGetProgramiv", None, [ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_int)])
        self.get_program_log = fn("glGetProgramInfoLog", None, [
            ctypes.c_uint, ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.c_char_p,
        ])
        self.use = fn("glUseProgram", None, [ctypes.c_uint])
        self.uniform_loc = fn("glGetUniformLocation", ctypes.c_int, [ctypes.c_uint, ctypes.c_char_p])
        self.attrib_loc = fn("glGetAttribLocation", ctypes.c_int, [ctypes.c_uint, ctypes.c_char_p])
        self.uniform1f = fn("glUniform1f", None, [ctypes.c_int, ctypes.c_float])
        self.uniform1i = fn("glUniform1i", None, [ctypes.c_int, ctypes.c_int])
        self.gen_textures = fn("glGenTextures", None, [ctypes.c_int, ctypes.POINTER(ctypes.c_uint)])
        self.bind_texture = fn("glBindTexture", None, [ctypes.c_uint, ctypes.c_uint])
        self.tex_param = fn("glTexParameteri", None, [ctypes.c_uint, ctypes.c_uint, ctypes.c_int])
        self.tex_image = fn("glTexImage2D", None, [
            ctypes.c_uint, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
            ctypes.c_int, ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p,
        ])
        self.gen_fb = fn("glGenFramebuffers", None, [ctypes.c_int, ctypes.POINTER(ctypes.c_uint)])
        self.bind_fb = fn("glBindFramebuffer", None, [ctypes.c_uint, ctypes.c_uint])
        self.fb_tex = fn("glFramebufferTexture2D", None, [
            ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_int,
        ])
        self.viewport = fn("glViewport", None, [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int])
        self.clear = fn("glClear", None, [ctypes.c_uint])
        self.enable_attr = fn("glEnableVertexAttribArray", None, [ctypes.c_uint])
        self.attr_pointer = fn("glVertexAttribPointer", None, [
            ctypes.c_uint, ctypes.c_int, ctypes.c_uint, ctypes.c_ubyte, ctypes.c_int, ctypes.c_void_p,
        ])
        self.draw_arrays = fn("glDrawArrays", None, [ctypes.c_uint, ctypes.c_int, ctypes.c_int])
        self.read_pixels = fn("glReadPixels", None, [
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
            ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p,
        ])
        self.delete_tex = fn("glDeleteTextures", None, [ctypes.c_int, ctypes.POINTER(ctypes.c_uint)])
        self.delete_fb = fn("glDeleteFramebuffers", None, [ctypes.c_int, ctypes.POINTER(ctypes.c_uint)])

    def _context(self):
        dpy = self.egl.eglGetPlatformDisplay(EGL_PLATFORM_SURFACELESS_MESA, None, None)
        if not dpy:
            raise RuntimeError("no surfaceless EGL display: 0x%x" % self.egl.eglGetError())
        major, minor = ctypes.c_int(), ctypes.c_int()
        if not self.egl.eglInitialize(dpy, ctypes.byref(major), ctypes.byref(minor)):
            raise RuntimeError("eglInitialize failed")
        if not self.egl.eglBindAPI(EGL_OPENGL_ES_API):
            raise RuntimeError("eglBindAPI failed")
        attrs = (ctypes.c_int * 13)(
            EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8, EGL_ALPHA_SIZE, 8,
            EGL_RENDERABLE_TYPE, EGL_OPENGL_ES2_BIT, EGL_SURFACE_TYPE, EGL_PBUFFER_BIT, EGL_NONE,
        )
        config = ctypes.c_void_p()
        count = ctypes.c_int()
        if not self.egl.eglChooseConfig(dpy, attrs, ctypes.byref(config), 1, ctypes.byref(count)) or not count.value:
            raise RuntimeError("eglChooseConfig failed")
        ctx_attr = (ctypes.c_int * 3)(EGL_CONTEXT_CLIENT_VERSION, 2, EGL_NONE)
        ctx = self.egl.eglCreateContext(dpy, config, None, ctx_attr)
        if not ctx:
            raise RuntimeError("eglCreateContext failed: 0x%x" % self.egl.eglGetError())
        if not self.egl.eglMakeCurrent(dpy, None, None, ctx):
            raise RuntimeError("eglMakeCurrent failed: 0x%x" % self.egl.eglGetError())

    def compile(self, fragment_source):
        def stage(kind, source):
            shader = self.create_shader(kind)
            encoded = source.encode()
            ptr = ctypes.c_char_p(encoded)
            self.shader_source(shader, 1, ctypes.byref(ptr), None)
            self.compile_shader(shader)
            status = ctypes.c_int()
            self.get_shader_iv(shader, GL_COMPILE_STATUS, ctypes.byref(status))
            if not status.value:
                log = ctypes.create_string_buffer(4096)
                length = ctypes.c_int()
                self.get_shader_log(shader, 4096, ctypes.byref(length), log)
                raise RuntimeError(log.value.decode(errors="replace"))
            return shader

        program = self.create_program()
        self.attach(program, stage(GL_VERTEX_SHADER, VERTEX))
        self.attach(program, stage(GL_FRAGMENT_SHADER, fragment_source))
        self.link(program)
        status = ctypes.c_int()
        self.get_program_iv(program, GL_LINK_STATUS, ctypes.byref(status))
        if not status.value:
            log = ctypes.create_string_buffer(4096)
            length = ctypes.c_int()
            self.get_program_log(program, 4096, ctypes.byref(length), log)
            raise RuntimeError(log.value.decode(errors="replace"))
        return program

    def draw(self, program, width, height, pixels, uniforms):
        tex = ctypes.c_uint()
        self.gen_textures(1, ctypes.byref(tex))
        self.bind_texture(GL_TEXTURE_2D, tex.value)
        self.tex_param(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        self.tex_param(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        self.tex_param(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        self.tex_param(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        data = (ctypes.c_ubyte * len(pixels)).from_buffer_copy(bytearray(pixels))
        self.tex_image(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)

        color = ctypes.c_uint()
        self.gen_textures(1, ctypes.byref(color))
        self.bind_texture(GL_TEXTURE_2D, color.value)
        self.tex_param(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        self.tex_param(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        self.tex_image(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)

        fb = ctypes.c_uint()
        self.gen_fb(1, ctypes.byref(fb))
        self.bind_fb(GL_FRAMEBUFFER, fb.value)
        self.fb_tex(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, color.value, 0)
        self.viewport(0, 0, width, height)
        self.clear(GL_COLOR_BUFFER_BIT)
        self.use(program)
        self.bind_texture(GL_TEXTURE_2D, tex.value)
        self.uniform1i(self.uniform_loc(program, b"tex"), 0)
        for name, value in uniforms.items():
            loc = self.uniform_loc(program, name.encode())
            if loc < 0:
                continue
            if isinstance(value, int) and name == "tex":
                self.uniform1i(loc, value)
            else:
                self.uniform1f(loc, float(value))

        pos = (ctypes.c_float * 8)(-1, -1, 1, -1, -1, 1, 1, 1)
        uv = (ctypes.c_float * 8)(0, 0, 1, 0, 0, 1, 1, 1)
        pos_loc = self.attrib_loc(program, b"a_pos")
        uv_loc = self.attrib_loc(program, b"a_uv")
        self.enable_attr(pos_loc)
        self.enable_attr(uv_loc)
        self.attr_pointer(pos_loc, 2, GL_FLOAT, GL_FALSE, 0, ctypes.cast(pos, ctypes.c_void_p))
        self.attr_pointer(uv_loc, 2, GL_FLOAT, GL_FALSE, 0, ctypes.cast(uv, ctypes.c_void_p))
        self.draw_arrays(GL_TRIANGLE_STRIP, 0, 4)

        out = (ctypes.c_ubyte * (width * height * 4))()
        self.read_pixels(0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE, out)
        self.delete_tex(1, ctypes.byref(tex))
        self.delete_tex(1, ctypes.byref(color))
        self.delete_fb(1, ctypes.byref(fb))
        return bytes(out)


def grade_uniforms(params, width, height):
    values = dict(params)
    values["gamma_power"] = values.pop("gamma")
    values["tex_width"] = width
    values["tex_height"] = height
    return values


def pixel(buf, width, x, y):
    i = (y * width + x) * 4
    return tuple(buf[i:i + 4])


class ShaderContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gl = GL()
        cls.grade = cls.gl.compile(to_gles((ROOT / "shaders" / "grade.glsl").read_text()))
        cls.sharp = cls.gl.compile(to_gles((ROOT / "shaders" / "sharpen.glsl").read_text()))

    def test_broken_shader_is_rejected(self):
        with self.assertRaises(RuntimeError):
            self.gl.compile("#version 100\nprecision highp float;\nvoid main() { not_a_function(); }\n")

    def test_grade_matches_the_encoded_contract(self):
        width = height = 4
        # Opaque mid gray, a premultiplied red, and a discarded pixel.
        src = bytearray(width * height * 4)
        for y in range(height):
            for x in range(width):
                i = (y * width + x) * 4
                src[i:i + 4] = bytes((128, 128, 128, 255))
        src[0:4] = bytes((64, 0, 0, 128))
        src[4:8] = bytes((10, 20, 30, 0))
        cases = [
            identity_grade(),
            identity_grade(exposure=-1),
            identity_grade(intensity=0, exposure=-1, contrast=1.5),
            identity_grade(blacks=-0.36),
            identity_grade(saturation=0),
            identity_grade(contrast=1.5),
            identity_grade(vignette=0.3),
            identity_grade(grain=0.14, grain_time=3),
            identity_grade(shadow_teal=0.4, skin_protect=1, exposure=-1.2, saturation=0.8),
        ]
        for params in cases:
            got = self.gl.draw(self.grade, width, height, src, grade_uniforms(params, width, height))
            for y in range(height):
                for x in range(width):
                    uv = ((x + 0.5) / width, (y + 0.5) / height)
                    i = (y * width + x) * 4
                    src_f = [src[i + c] / 255.0 for c in range(4)]
                    expect = grade_pixel(src_f, uv, params, width, height)
                    actual = pixel(got, width, x, y)
                    for channel in range(4):
                        byte = int(round(max(0.0, min(1.0, expect[channel])) * 255.0))
                        self.assertLessEqual(
                            abs(actual[channel] - byte), 1,
                            "grade %s pixel %d,%d channel %d got %s expect %s" % (
                                params, x, y, channel, actual, byte,
                            ),
                        )

    def test_sharpen_matches_the_contract_and_skips_translucent_pixels(self):
        width = height = 8
        src = bytearray(width * height * 4)
        for y in range(height):
            for x in range(width):
                i = (y * width + x) * 4
                if y == 0:
                    src[i:i + 4] = bytes((40, 50, 60, 100))
                else:
                    value = 102 if x < 4 else 178
                    src[i:i + 4] = bytes((value, value, value, 255))
        amount = 0.8
        got = self.gl.draw(self.sharp, width, height, src, {
            "amount": amount,
            "tex_width": width,
            "tex_height": height,
        })
        for y in range(height):
            for x in range(width):
                i = (y * width + x) * 4
                center = [src[i + c] / 255.0 for c in range(4)]

                def sample(ix, iy):
                    ix = min(max(ix, 0), width - 1)
                    iy = min(max(iy, 0), height - 1)
                    j = (iy * width + ix) * 4
                    return [src[j + c] / 255.0 for c in range(4)]

                expect = sharpen_pixel(
                    center,
                    [sample(x - 1, y), sample(x + 1, y), sample(x, y + 1), sample(x, y - 1)],
                    amount,
                )
                actual = pixel(got, width, x, y)
                for channel in range(4):
                    byte = int(round(expect[channel] * 255.0))
                    self.assertLessEqual(
                        abs(actual[channel] - byte), 1,
                        "sharpen pixel %d,%d channel %d got %s expect %s" % (x, y, channel, actual, byte),
                    )
        # The translucent row is copied. A step pixel is not.
        self.assertEqual(pixel(got, width, 1, 0), (40, 50, 60, 100))
        self.assertNotEqual(pixel(got, width, 4, 4)[0], 178)


if __name__ == "__main__":
    unittest.main()
