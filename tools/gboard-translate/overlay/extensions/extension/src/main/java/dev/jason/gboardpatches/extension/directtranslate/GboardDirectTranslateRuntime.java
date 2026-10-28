/* Copyright (C) 2026. This fork is distributed under GPL-3.0-or-later. */
package dev.jason.gboardpatches.extension.directtranslate;

import android.os.Handler;
import android.os.Looper;

import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

/** Entry points called only from the opt-in Morphe Translate patch. */
public final class GboardDirectTranslateRuntime {
    private static final ThreadPoolExecutor WORKER = new ThreadPoolExecutor(
            1, 1, 30, TimeUnit.SECONDS, new ArrayBlockingQueue<>(1), runnable -> {
                Thread thread = new Thread(runnable, "GboardDirectTranslate");
                thread.setDaemon(true);
                return thread;
            });
    private static final Handler MAIN = new Handler(Looper.getMainLooper());
    private static final TranslateCoordinator COORDINATOR = new TranslateCoordinator(
            WORKER, command -> MAIN.post(command), () -> WORKER.getQueue().clear(), new GtxClient());

    static {
        WORKER.allowCoreThreadTimeOut(true);
    }

    private GboardDirectTranslateRuntime() {}

    public static boolean tryDispatch(Object provider, Object request, Object callback) {
        return COORDINATOR.tryDispatch(provider, request, callback);
    }

    public static void cancel() {
        COORDINATOR.cancel();
    }
}
