/* Copyright (C) 2026. This fork is distributed under GPL-3.0-or-later. */
package dev.jason.gboardpatches.extension.directtranslate;

import java.lang.ref.WeakReference;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.List;
import java.util.concurrent.Executor;

/** Bridges only the reviewed 18.5.4 native Translate request/callback types. */
final class TranslateCoordinator {
    interface Client {
        GtxClient.Translation translate(String text, String source, String target) throws Exception;
    }

    private final Object lock = new Object();
    private final Executor worker;
    private final Executor main;
    private final Runnable clearPending;
    private final Client client;
    private WeakReference<Object> expectedRequest = new WeakReference<>(null);
    private WeakReference<Object> expectedCallback = new WeakReference<>(null);
    private long generation;

    TranslateCoordinator(Executor worker, Executor main, Runnable clearPending, Client client) {
        this.worker = worker;
        this.main = main;
        this.clearPending = clearPending;
        this.client = client;
    }

    void prepare(Object request, Object callback) {
        synchronized (lock) {
            expectedRequest = new WeakReference<>(request);
            expectedCallback = new WeakReference<>(callback);
        }
    }

    boolean tryDispatch(Object provider, Object request, Object callback) {
        // Gboard uses the same provider for server-health probes. Only replace
        // requests with the actual Translate UI callback; leave probes alone.
        if (provider == null || request == null || callback == null
                || !"kjx".equals(provider.getClass().getName())
                || !"klg".equals(request.getClass().getName())
                || !"kli".equals(callback.getClass().getName())) return false;
        synchronized (lock) {
            if (expectedRequest.get() != request || expectedCallback.get() != callback) return true;
        }
        final Bindings bindings;
        final String text;
        final String source;
        final String target;
        try {
            bindings = new Bindings(request.getClass().getClassLoader(), callback.getClass());
            text = (String) bindings.text.get(request);
            source = (String) bindings.source.get(request);
            target = (String) bindings.target.get(request);
        } catch (ReflectiveOperationException | RuntimeException mismatch) {
            // If still current, an unexpected runtime shape leaves Gboard's
            // original route intact. A request cancelled meanwhile is dropped.
            synchronized (lock) {
                if (expectedRequest.get() != request || expectedCallback.get() != callback) return true;
                expectedRequest.clear();
                expectedCallback.clear();
            }
            return false;
        }
        synchronized (lock) {
            // Native throttling can call e() after an empty edit or view close.
            // Only the request/callback pair prepared by the latest actual UI
            // dispatch may send; consume it exactly once, without retaining text.
            if (expectedRequest.get() != request || expectedCallback.get() != callback) return true;
            expectedRequest.clear();
            expectedCallback.clear();
            long ticket = ++generation;
            clearPending.run();
            try {
                worker.execute(() -> execute(ticket, bindings, callback, text, source, target));
            } catch (RuntimeException rejected) {
                // A rejected task still delivers Gboard's native error response.
                post(ticket, bindings, callback, null, source);
            }
        }
        return true;
    }

    void cancel() {
        synchronized (lock) {
            generation++;
            expectedRequest.clear();
            expectedCallback.clear();
            clearPending.run();
        }
    }

    private void execute(long ticket, Bindings bindings, Object callback,
                         String text, String source, String target) {
        synchronized (lock) {
            if (generation != ticket) return;
        }
        GtxClient.Translation translation;
        try {
            translation = client.translate(text, source, target);
        } catch (Exception failure) {
            // Never log typed text, URLs, exception details, or response bodies.
            translation = null;
        }
        post(ticket, bindings, callback, translation, source);
    }

    private void post(long ticket, Bindings bindings, Object callback,
                      GtxClient.Translation translation, String source) {
        try {
            main.execute(() -> {
                synchronized (lock) {
                    if (generation != ticket) return;
                }
                try {
                    Object response = translation == null
                            ? bindings.failure.newInstance(1)
                            : bindings.success.newInstance(translation.text);
                    if (translation != null && (source == null || source.isEmpty() || "auto".equals(source))
                            && translation.detectedLanguage != null) {
                        @SuppressWarnings("unchecked")
                        List<String> detected = (List<String>) bindings.detectedLanguages.get(response);
                        detected.add(translation.detectedLanguage);
                    }
                    bindings.callback.invoke(callback, response);
                } catch (ReflectiveOperationException | RuntimeException ignored) {
                    // No user text or stack traces in logs. Native shape drift is
                    // rejected at patch time; a runtime failure is not success.
                }
            });
        } catch (RuntimeException ignored) {
            // Do not crash the keyboard if its UI looper is shutting down.
        }
    }

    private static final class Bindings {
        final Field text;
        final Field source;
        final Field target;
        final Field detectedLanguages;
        final Constructor<?> success;
        final Constructor<?> failure;
        final Method callback;

        Bindings(ClassLoader loader, Class<?> callbackClass) throws ReflectiveOperationException {
            Class<?> request = Class.forName("klg", false, loader);
            Class<?> response = Class.forName("abxb", false, loader);
            text = field(request, "a", String.class);
            source = field(request, "b", String.class);
            target = field(request, "c", String.class);
            detectedLanguages = field(response, "a", Object.class);
            success = response.getDeclaredConstructor(String.class);
            failure = response.getDeclaredConstructor(int.class);
            callback = callbackClass.getDeclaredMethod("a", response);
            success.setAccessible(true);
            failure.setAccessible(true);
            callback.setAccessible(true);
        }

        private static Field field(Class<?> owner, String name, Class<?> type)
                throws ReflectiveOperationException {
            Field field = owner.getDeclaredField(name);
            if (field.getType() != type) throw new NoSuchFieldException(name);
            field.setAccessible(true);
            return field;
        }
    }
}
