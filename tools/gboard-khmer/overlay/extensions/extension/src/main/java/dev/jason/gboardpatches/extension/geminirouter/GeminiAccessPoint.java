package dev.jason.gboardpatches.extension.geminirouter;

import android.content.Context;
import android.util.Log;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Set;

/** Version-gated Gboard 18.5.4 toolbar access point labelled Gmn. */
public final class GeminiAccessPoint {
    private static final String TAG = "GboardGeminiRouter";
    private static final String TOKEN = "gboard_gemini_chat";
    private static final String PREFS = "gboard_gemini_chat";
    private static final String PLACED = "toolbar_position_initialized";
    private static final String LABEL = "Gmn · Gemini translation";

    private GeminiAccessPoint() {}

    public static Object extendOrderCatalog(Context context, Object original) {
        try {
            if (context == null || !(original instanceof Set<?> values)) return original;
            Class<?> immutable = Class.forName("wpa", false, original.getClass().getClassLoader());
            if (!immutable.isInstance(original)) return original;
            List<String> tokens = new ArrayList<>();
            for (Object value : values) {
                if (!(value instanceof String token)) return original;
                if (!tokens.contains(token)) tokens.add(token);
            }
            if (tokens.contains(TOKEN)) return original;
            tokens.add(TOKEN);
            Method copy = immutable.getDeclaredMethod("n", Collection.class);
            if (!Modifier.isStatic(copy.getModifiers()) || copy.getReturnType() != immutable) return original;
            copy.setAccessible(true);
            return copy.invoke(null, tokens);
        } catch (Throwable failure) {
            debug("catalog", failure);
            return original;
        }
    }

    public static void register(Object controller, Context context) {
        String stage = "input";
        try {
            if (controller == null || context == null) return;
            stage = "icon";
            int icon = context.getResources().getIdentifier(TOKEN, "drawable", context.getPackageName());
            if (icon == 0 || !"drawable".equals(context.getResources().getResourceTypeName(icon))) return;
            ClassLoader loader = controller.getClass().getClassLoader();
            Class<?> descriptor = Class.forName("mtr", false, loader);
            Class<?> builder = Class.forName("mtm", false, loader);
            Class<?> controllerClass = Class.forName("mwv", false, loader);
            if (!controllerClass.isInstance(controller)) return;

            stage = "catalog";
            Class<?> orderClass = Class.forName("mwg", false, loader);
            Field helperField = controllerClass.getDeclaredField("g");
            Field masterField = orderClass.getDeclaredField("c");
            if (helperField.getType() != orderClass) return;
            helperField.setAccessible(true);
            masterField.setAccessible(true);
            Object helper = helperField.get(controller);
            Object stockCatalog = masterField.get(helper);
            Object expandedCatalog = extendOrderCatalog(context, stockCatalog);
            if (!(expandedCatalog instanceof Set<?>) || !((Set<?>) expandedCatalog).contains(TOKEN)) return;
            if (expandedCatalog != stockCatalog) masterField.set(helper, expandedCatalog);

            stage = "descriptor";
            Object value = method(descriptor, "c", builder, true).invoke(null);
            method(builder, "l", void.class, false, String.class).invoke(value, TOKEN);
            method(builder, "i", void.class, false, int.class).invoke(value, icon);
            Field title = builder.getDeclaredField("d");
            if (title.getType() != String.class || Modifier.isStatic(title.getModifiers())) return;
            title.setAccessible(true);
            title.set(value, LABEL);
            method(builder, "q", void.class, false, Runnable.class).invoke(value,
                    (Runnable) () -> GeminiChatRouter.open(context));
            Object built = method(builder, "a", descriptor, false).invoke(value);
            method(controllerClass, "g", void.class, false, descriptor, boolean.class)
                    .invoke(controller, built, false);

            stage = "position";
            if (!context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getBoolean(PLACED, false)) {
                method(controllerClass, "x", void.class, false, String.class, int.class, boolean.class)
                        .invoke(controller, TOKEN, 0, false);
                context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
                        .putBoolean(PLACED, true).apply();
            }
        } catch (Throwable failure) {
            debug(stage, failure);
        }
    }

    private static void debug(String stage, Throwable failure) {
        try {
            if (!Log.isLoggable(TAG, Log.DEBUG)) return;
            Throwable cause = failure != null && failure.getCause() != null ? failure.getCause() : failure;
            Log.d(TAG, stage + (cause == null ? "" : ":" + cause.getClass().getSimpleName()));
        } catch (Throwable ignored) {}
    }

    private static Method method(Class<?> owner, String name, Class<?> result,
            boolean isStatic, Class<?>... arguments) throws ReflectiveOperationException {
        Method method = owner.getDeclaredMethod(name, arguments);
        if (method.getReturnType() != result || Modifier.isStatic(method.getModifiers()) != isStatic) {
            throw new NoSuchMethodException(name);
        }
        method.setAccessible(true);
        return method;
    }
}
