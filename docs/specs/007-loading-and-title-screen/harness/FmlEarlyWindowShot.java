/*
 * Drives FML's real early window (net.neoforged.fml.earlydisplay.DisplayWindow, FML 4.0.39 = NeoForge 21.1.x)
 * outside Minecraft, feeds it fake mod-loading progress, and lets an external grabber (ffmpeg x11grab) capture
 * the Xvfb screen. Proves the "screenshot the loading screen at time T" step headless, with the same code path
 * a custom ImmediateWindowProvider would extend.
 */
import java.nio.file.*;
import net.neoforged.fml.earlydisplay.DisplayWindow;
import net.neoforged.fml.loading.FMLConfig;
import net.neoforged.fml.loading.FMLPaths;
import net.neoforged.fml.loading.progress.StartupNotificationManager;

public class FmlEarlyWindowShot {
    public static void main(String[] args) throws Exception {
        Path game = Files.createDirectories(Path.of(args.length > 0 ? args[0] : "run-early"));
        long seconds = args.length > 1 ? Long.parseLong(args[1]) : 6;
        FMLPaths.loadAbsolutePaths(game);
        FMLConfig.load();
        DisplayWindow w = new DisplayWindow();
        Runnable tick = w.initialize(new String[] {"--fml.mcVersion", "1.21.1", "--fml.neoForgeVersion", "21.1.172", "--width", "854", "--height", "480"});
        var bar = StartupNotificationManager.addProgressBar("Loading mods", 331);
        String[] mods = {"create", "mekanism", "ae2", "immersiveengineering", "powah", "xnet", "arffornia"};
        long end = System.currentTimeMillis() + seconds * 1000;
        int i = 0;
        System.out.println("EARLY_WINDOW_SHOWN"); // marker a launcher or test runner can wait for
        while (System.currentTimeMillis() < end) {
            tick.run();
            if (i % 2 == 0) { bar.increment(); StartupNotificationManager.addModMessage("Constructing mod " + mods[(i / 2) % mods.length]); }
            Thread.sleep(50);
            i++;
        }
        System.out.println("DONE frames~" + i);
        System.exit(0);
    }
}
