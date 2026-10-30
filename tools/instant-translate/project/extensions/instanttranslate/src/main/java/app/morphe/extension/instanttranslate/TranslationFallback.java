/* Copyright (C) 2026. This fork is distributed under GPL-3.0-or-later. */
package app.morphe.extension.instanttranslate;

import java.lang.reflect.Field;
import java.util.List;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

/** Entry points injected only into the explicitly selected, exact-build patch. */
public final class TranslationFallback {
    private static final ThreadPoolExecutor EXECUTOR = new ThreadPoolExecutor(
            2, 2, 30, TimeUnit.SECONDS, new ArrayBlockingQueue<>(8), runnable -> {
                Thread thread = new Thread(runnable, "instant-translate-fallback");
                thread.setDaemon(true);
                return thread;
            }, new ThreadPoolExecutor.AbortPolicy());
    private static final FallbackCoordinator COORDINATOR = new FallbackCoordinator(new GtxClient(), EXECUTOR);

    private TranslationFallback() {}

    /** Called only when the original result is blank or null. */
    public static boolean retryAfterBlank(String original, Object token, Object continuation) {
        if (original != null && !original.trim().isEmpty()) return false;
        if (token == null) return false;
        try {
            Class<?> cls = token.getClass();
            String text = stringField(cls, token, "t");
            String source;
            String target;
            if ("qy8".equals(cls.getName())) {
                source = stringField(cls, token, "u");
                target = stringField(cls, token, "v");
            } else if ("d29".equals(cls.getName())) {
                source = stringField(cls, token, "morphe_source");
                target = stringField(cls, token, "morphe_target");
            } else {
                return false;
            }
            return COORDINATOR.trySingle(original, text, source, target, token, continuation);
        } catch (ReflectiveOperationException | RuntimeException ignored) {
            return false;
        }
    }

    /** Preserve valid results; retry only explicitly failed entries. */
    public static boolean retryFailedBatch(Object request, List<?> original, Object token, Object continuation) {
        try {
            return COORDINATOR.tryBatch(request, original, token, continuation);
        } catch (RuntimeException ignored) {
            return false;
        }
    }

    private static String stringField(Class<?> cls, Object receiver, String name)
            throws ReflectiveOperationException {
        Field field = cls.getDeclaredField(name);
        field.setAccessible(true);
        Object value = field.get(receiver);
        if (value != null && !(value instanceof String)) throw new IllegalArgumentException("Unexpected field type");
        return (String) value;
    }
}
