/*
 * Feasibility probe for the loading-screen test pipeline (spec 007).
 *
 * The FML early window is plain LWJGL/GLFW + OpenGL 3.2 core, drawn before Minecraft exists.
 * This probe does what a test hook in a custom ImmediateWindowProvider would do:
 *   1. create a GLFW window the way FML's DisplayWindow does (hidden, GL 4.6 -> 3.2 core fallback),
 *   2. draw a few frames of quads with a core-profile shader (stand-in for the sprite renderer),
 *   3. read the framebuffer back with glReadPixels and write a PNG (stb_image_write),
 *   4. print GL_RENDERER and fail if it is not the expected software renderer (llvmpipe) in CI.
 *
 * Run: xvfb-run -a -s "-screen 0 1280x720x24" java -cp "<lwjgl jars>" EarlyWindowProbe.java out.png
 */
import static org.lwjgl.glfw.GLFW.*;
import static org.lwjgl.opengl.GL32C.*;

import java.nio.ByteBuffer;
import java.nio.FloatBuffer;
import org.lwjgl.BufferUtils;
import org.lwjgl.opengl.GL;
import org.lwjgl.stb.STBImageWrite;

public class EarlyWindowProbe {
    static final int W = 854, H = 480; // FML renders the early screen into an 854x480 framebuffer

    public static void main(String[] args) {
        String out = args.length > 0 ? args[0] : "early-window-probe.png";
        String expect = System.getenv().getOrDefault("EXPECT_RENDERER", "llvmpipe");
        if (!glfwInit()) throw new IllegalStateException("glfwInit failed (no display?)");
        glfwDefaultWindowHints();
        glfwWindowHint(GLFW_VISIBLE, GLFW_FALSE);
        glfwWindowHint(GLFW_CLIENT_API, GLFW_OPENGL_API);
        glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
        glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GLFW_TRUE);
        long win = 0;
        int[][] versions = {{4, 6}, {4, 5}, {4, 1}, {3, 3}, {3, 2}}; // same idea as DisplayWindow.GL_VERSIONS
        for (int[] v : versions) {
            glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, v[0]);
            glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, v[1]);
            win = glfwCreateWindow(W, H, "Arffornia early window probe", 0L, 0L);
            if (win != 0) break;
        }
        if (win == 0) throw new IllegalStateException("could not create a GL 3.2+ core context");
        glfwMakeContextCurrent(win);
        GL.createCapabilities();
        String renderer = glGetString(GL_RENDERER), version = glGetString(GL_VERSION);
        System.out.println("GL_RENDERER=" + renderer);
        System.out.println("GL_VERSION=" + version);

        // offscreen framebuffer, like FML's EarlyFramebuffer
        int fbo = glGenFramebuffers(), tex = glGenTextures();
        glBindTexture(GL_TEXTURE_2D, tex);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, W, H, 0, GL_RGBA, GL_UNSIGNED_BYTE, (ByteBuffer) null);
        glBindFramebuffer(GL_FRAMEBUFFER, fbo);
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, tex, 0);
        if (glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE) throw new IllegalStateException("FBO incomplete");

        int prog = program(
                "#version 150\nin vec2 pos; in vec4 col; out vec4 c; uniform vec2 size;\n"
                        + "void main(){ c = col; gl_Position = vec4(pos / size * 2.0 - 1.0, 0.0, 1.0); gl_Position.y = -gl_Position.y; }",
                "#version 150\nin vec4 c; out vec4 o; void main(){ o = c; }");
        int vao = glGenVertexArrays(), vbo = glGenBuffers();
        glBindVertexArray(vao);
        glBindBuffer(GL_ARRAY_BUFFER, vbo);
        int posLoc = glGetAttribLocation(prog, "pos"), colLoc = glGetAttribLocation(prog, "col");
        glEnableVertexAttribArray(posLoc);
        glVertexAttribPointer(posLoc, 2, GL_FLOAT, false, 24, 0);
        glEnableVertexAttribArray(colLoc);
        glVertexAttribPointer(colLoc, 4, GL_FLOAT, false, 24, 8);
        glUseProgram(prog);
        glUniform2f(glGetUniformLocation(prog, "size"), W, H);
        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

        long t0 = System.nanoTime();
        int frames = 40; // 2 s of the 20 Hz early-window tick
        for (int f = 0; f < frames; f++) {
            float progress = (f + 1) / (float) frames;
            glViewport(0, 0, W, H);
            glClearColor(0x0b / 255f, 0x11 / 255f, 0x16 / 255f, 1f);
            glClear(GL_COLOR_BUFFER_BIT);
            FloatBuffer vb = BufferUtils.createFloatBuffer(6 * 6 * 32);
            // iso emblem: top (orange), left (dark), right (darker)
            float cx = 80, cy = 380, s = 28, c30 = 0.866f;
            quad(vb, cx, cy - s, cx + s * c30, cy - s / 2, cx, cy, cx - s * c30, cy - s / 2, 0.878f, 0.439f, 0.235f, 1f);
            quad(vb, cx - s * c30, cy - s / 2, cx, cy, cx, cy + s, cx - s * c30, cy + s / 2, 0.16f, 0.21f, 0.25f, 1f);
            quad(vb, cx, cy, cx + s * c30, cy - s / 2, cx + s * c30, cy + s / 2, cx, cy + s, 0.10f, 0.14f, 0.17f, 1f);
            // progress bar track + fill + head, as in direction A
            rect(vb, 160, 430, 640, 4, 1f, 1f, 1f, 0.08f);
            rect(vb, 160, 430, 640 * progress, 4, 0.878f, 0.439f, 0.235f, 1f);
            rect(vb, 158 + 640 * progress, 424, 3, 16, 1f, 0.89f, 0.78f, 1f);
            // moving "conveyor items"
            for (int i = 0; i < 6; i++) {
                float x = 200 + ((f * 6 + i * 90) % 540);
                rect(vb, x, 250 + (x - 200) * 0.25f, 14, 14, 0.878f, 0.439f, 0.235f, 1f);
            }
            vb.flip();
            glBufferData(GL_ARRAY_BUFFER, vb, GL_STREAM_DRAW);
            glDrawArrays(GL_TRIANGLES, 0, vb.limit() / 6);
            glfwPollEvents();
        }
        glFinish();
        double ms = (System.nanoTime() - t0) / 1e6 / frames;

        ByteBuffer px = BufferUtils.createByteBuffer(W * H * 4);
        glReadPixels(0, 0, W, H, GL_RGBA, GL_UNSIGNED_BYTE, px);
        STBImageWrite.stbi_flip_vertically_on_write(true);
        if (!STBImageWrite.stbi_write_png(out, W, H, 4, px, W * 4)) throw new IllegalStateException("PNG write failed");
        System.out.printf("frames=%d avg_frame_ms=%.2f png=%s%n", frames, ms, out);

        // sanity: the progress bar head must be bright at the expected pixel (bottom-left origin in GL)
        int x = 159 + 640, y = H - 432;
        int r = px.get((y * W + x) * 4) & 0xff;
        glfwDestroyWindow(win);
        glfwTerminate();
        boolean rendererOk = expect.isEmpty() || renderer.toLowerCase().contains(expect.toLowerCase());
        if (r < 200 || !rendererOk) {
            System.out.println("FAIL: pixel r=" + r + " renderer_ok=" + rendererOk);
            System.exit(1);
        }
        System.out.println("OK: pixel check passed, renderer " + (expect.isEmpty() ? "not asserted" : "is " + expect));
    }

    static void rect(FloatBuffer b, float x, float y, float w, float h, float r, float g, float bl, float a) {
        quad(b, x, y, x + w, y, x + w, y + h, x, y + h, r, g, bl, a);
    }

    static void quad(FloatBuffer b, float x0, float y0, float x1, float y1, float x2, float y2, float x3, float y3, float r, float g, float bl, float a) {
        float[][] v = {{x0, y0}, {x1, y1}, {x2, y2}, {x0, y0}, {x2, y2}, {x3, y3}};
        for (float[] p : v) b.put(p[0]).put(p[1]).put(r).put(g).put(bl).put(a);
    }

    static int program(String vs, String fs) {
        int p = glCreateProgram();
        for (int[] s : new int[][] {{GL_VERTEX_SHADER, 0}, {GL_FRAGMENT_SHADER, 1}}) {
            int sh = glCreateShader(s[0]);
            glShaderSource(sh, s[1] == 0 ? vs : fs);
            glCompileShader(sh);
            if (glGetShaderi(sh, GL_COMPILE_STATUS) == 0) throw new IllegalStateException(glGetShaderInfoLog(sh));
            glAttachShader(p, sh);
        }
        glBindAttribLocation(p, 0, "pos");
        glLinkProgram(p);
        if (glGetProgrami(p, GL_LINK_STATUS) == 0) throw new IllegalStateException(glGetProgramInfoLog(p));
        return p;
    }
}
