/* Copyright (C) 2026. This fork is distributed under GPL-3.0-or-later. */
package app.morphe.extension.instanttranslate;

import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.WeakHashMap;
import java.util.concurrent.Executor;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.TimeUnit;
import java.util.regex.Pattern;

/**
 * Asynchronous last-resort transport. The original coroutine remains suspended;
 * the app's intercepted continuation is resumed once, without blocking Android's
 * main thread. Batch reconstruction is specific to the reviewed 50342 DEX;
 * the reviewed 50350 hook retries one final empty single-result path only.
 */
final class FallbackCoordinator {
    interface Client {
        String translate(String text, String source, String target) throws Exception;
    }

    private static final Pattern LANGUAGE = Pattern.compile("[A-Za-z0-9_-]{1,24}");
    private static final int MAX_TEXT = 8192;
    private static final int MAX_BATCH = 24;
    private static final long BATCH_BUDGET_NS = TimeUnit.SECONDS.toNanos(25);
    private final Client client;
    private final Executor executor;
    // A failed fallback resumes the same state machine with its original failure.
    // Its next visit consumes this marker instead of retrying forever. Weak keys
    // avoid retaining completed successful coroutines or their source text.
    private final Map<Object, Boolean> attempted = new WeakHashMap<>();

    FallbackCoordinator(Client client, Executor executor) {
        this.client = client;
        this.executor = executor;
    }

    boolean trySingle(String original, String text, String source, String target, Object token, Object continuation) {
        if (notBlank(original) || !validText(text) || !validLanguages(source, target)) return false;
        final Method resume = resumeMethod(continuation);
        if (token == null || resume == null) return false;
        return schedule(token, () -> {
            String result = original;
            try {
                String translated = client.translate(text, source, target);
                if (notBlank(translated)) result = translated;
            } catch (Exception ignored) {
                // Preserve the app's failure behavior; never log text or request URLs.
            }
            resume(resume, continuation, result);
        });
    }

    /**
     * The app handles an empty batch itself, including its own per-item retry;
     * this hook is only for nonempty lists containing explicit failed items.
     */
    boolean tryBatch(Object request, List<?> original, Object token, Object continuation) {
        if (token == null || original == null || original.isEmpty() || original.size() > MAX_BATCH) return false;
        final Method resume = resumeMethod(continuation);
        if (resume == null) return false;
        final Batch batch;
        try {
            batch = Batch.inspect(request, original);
        } catch (ReflectiveOperationException | RuntimeException ignored) {
            return false; // Unknown object layout: do not change original behavior.
        }
        if (batch == null || !validLanguages(batch.source, batch.target)) return false;
        return schedule(token, () -> {
            List<Object> translated = new ArrayList<>(batch.original);
            long deadline = System.nanoTime() + BATCH_BUDGET_NS;
            for (int index : batch.failed) {
                if (System.nanoTime() >= deadline || Thread.currentThread().isInterrupted()) break;
                try {
                    String text = batch.input.get(index);
                    String value = client.translate(text, batch.source, batch.target);
                    if (notBlank(value)) translated.set(index, batch.constructor.newInstance(text, value, null, batch.kind, false));
                } catch (Exception ignored) {
                    // Leave the individual original failure intact.
                }
            }
            resume(resume, continuation, translated);
        });
    }

    private boolean schedule(Object token, Runnable task) {
        synchronized (attempted) {
            if (attempted.remove(token) != null) return false;
            attempted.put(token, Boolean.TRUE);
            try {
                executor.execute(task);
                return true;
            } catch (RejectedExecutionException ignored) {
                attempted.remove(token);
                return false;
            }
        }
    }

    private static Method resumeMethod(Object continuation) {
        if (continuation == null) return null;
        try {
            Method method = continuation.getClass().getMethod("resumeWith", Object.class);
            method.setAccessible(true);
            return method;
        } catch (ReflectiveOperationException | RuntimeException ignored) {
            return null;
        }
    }

    private static void resume(Method method, Object continuation, Object result) {
        try {
            method.invoke(continuation, result);
        } catch (ReflectiveOperationException | RuntimeException ignored) {
            // Never expose source/translated text or request details in logs.
        }
    }

    private static boolean validText(String text) {
        return text != null && !text.isEmpty() && text.length() <= MAX_TEXT;
    }

    private static boolean notBlank(String value) {
        return value != null && !value.trim().isEmpty();
    }

    private static boolean validLanguages(String source, String target) {
        return (source == null || source.isEmpty() || LANGUAGE.matcher(source).matches()) &&
                target != null && LANGUAGE.matcher(target).matches() && !"auto".equalsIgnoreCase(target);
    }

    private static Field field(Class<?> owner, String name) throws ReflectiveOperationException {
        Field result = owner.getDeclaredField(name);
        result.setAccessible(true);
        return result;
    }

    private static String defaultTarget() {
        try {
            Method method = Class.forName("d54").getDeclaredMethod("I");
            method.setAccessible(true);
            Object value = method.invoke(null);
            return value instanceof String ? (String) value : null;
        } catch (ReflectiveOperationException | RuntimeException ignored) {
            return null;
        }
    }

    private static final class Batch {
        final ArrayList<Object> original;
        final ArrayList<String> input;
        final ArrayList<Integer> failed;
        final String source;
        final String target;
        final Constructor<?> constructor;
        final Object kind;

        Batch(ArrayList<Object> original, ArrayList<String> input, ArrayList<Integer> failed,
              String source, String target, Constructor<?> constructor, Object kind) {
            this.original = original;
            this.input = input;
            this.failed = failed;
            this.source = source;
            this.target = target;
            this.constructor = constructor;
            this.kind = kind;
        }

        static Batch inspect(Object request, List<?> original) throws ReflectiveOperationException {
            if (request == null || !"eh7".equals(request.getClass().getName())) return null;
            Class<?> callback = request.getClass();
            Object sourceValue = field(callback, "c").get(request);
            Object targetValue = field(callback, "d").get(request);
            Object inputs = field(callback, "e").get(request);
            if ((sourceValue != null && !(sourceValue instanceof String)) ||
                    (targetValue != null && !(targetValue instanceof String)) || !(inputs instanceof List)) return null;
            List<?> rawInput = (List<?>) inputs;
            if (rawInput.size() != original.size() || rawInput.size() > MAX_BATCH) return null;
            String source = (String) sourceValue;
            String target = targetValue == null ? defaultTarget() : (String) targetValue;
            Class<?> result = Class.forName("h19");
            Class<?> kindClass = Class.forName("a29");
            Field textField = field(result, "a");
            Field outputField = field(result, "b");
            Field errorField = field(result, "c");
            Object kind = field(kindClass, "c").get(null);
            if (kind == null) return null;
            Constructor<?> constructor = result.getDeclaredConstructor(String.class, String.class,
                    Throwable.class, kindClass, boolean.class);
            constructor.setAccessible(true);
            ArrayList<Object> copy = new ArrayList<>(original);
            ArrayList<String> text = new ArrayList<>(original.size());
            ArrayList<Integer> failed = new ArrayList<>();
            for (int i = 0; i < original.size(); i++) {
                Object input = rawInput.get(i);
                Object item = original.get(i);
                if (!(input instanceof String) || !validText((String) input) || !result.isInstance(item)) return null;
                if (!input.equals(textField.get(item))) return null;
                Object value = outputField.get(item);
                Object error = errorField.get(item);
                if (value != null && !(value instanceof String)) return null;
                if (error != null || !notBlank((String) value)) failed.add(i);
                text.add((String) input);
            }
            if (failed.isEmpty()) return null;
            return new Batch(copy, text, failed, source, target, constructor, kind);
        }
    }
}
