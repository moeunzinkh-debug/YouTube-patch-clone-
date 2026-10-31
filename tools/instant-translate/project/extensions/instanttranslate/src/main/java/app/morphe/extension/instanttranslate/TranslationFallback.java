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
    private static final ProviderRouter PROVIDER = new ProviderRouter(ProviderSettings::selected,
            new SeaLionClient(ProviderSettings::seaLionConfig));
    private static final FallbackCoordinator COORDINATOR = new FallbackCoordinator(PROVIDER, EXECUTOR);

    private TranslationFallback() {}

    /** Called only when the original result is blank or null. */
    public static boolean retryAfterBlank(String original, Object token, Object continuation) {
        if (original != null && !original.trim().isEmpty()) return false;
        if (token == null) return false;
        try {
            if (!ProviderRouter.SEA_LION.equals(ProviderSettings.selected())) return false;
            String[] request = readSingleRequest(token);
            if (request == null) return false;
            return COORDINATOR.trySingle(original, request[0], request[1], request[2], token, continuation);
        } catch (ReflectiveOperationException | RuntimeException ignored) {
            return false;
        }
    }

    /** Preserve valid results; retry only explicitly failed entries. */
    public static boolean retryFailedBatch(Object request, List<?> original, Object token, Object continuation) {
        try {
            if (!ProviderRouter.SEA_LION.equals(ProviderSettings.selected())) return false;
            return COORDINATOR.tryBatch(request, original, token, continuation);
        } catch (RuntimeException ignored) {
            return false;
        }
    }

    /** Read only a reviewed coroutine layout; unknown layouts fail closed. */
    static String[] readSingleRequest(Object token) throws ReflectiveOperationException {
        if (token == null) return null;
        Class<?> cls = token.getClass();
        String sourceField, targetField;
        if ("qy8".equals(cls.getName()) || "fra".equals(cls.getName())) {
            sourceField = "u"; targetField = "v";
        } else if ("d29".equals(cls.getName())) {
            sourceField = "morphe_source"; targetField = "morphe_target";
        } else {
            return null;
        }
        return new String[] {stringField(cls, token, "t"), stringField(cls, token, sourceField),
                stringField(cls, token, targetField)};
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
