package dev.jason.gboardpatches.extension.khmerlish;

import android.content.Context;
import android.util.Log;
import java.lang.ref.WeakReference;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Set;

/** Version-gated Gboard 18.5.4 synthetic toolbar access point. */
public final class KhmerlishAccessPoint {
    private static final String TAG = "GboardKhmerlish";
    private static final String TOKEN = "gboard_khmerlish_panel";
    private static final String PREFS = "gboard_khmerlish_panel";
    private static final String PLACED = "toolbar_position_initialized";

    private KhmerlishAccessPoint() {}

    public static Object extendOrderCatalog(Context context, Object original) {
        try {
            if (context == null || !(original instanceof Set<?> values)) { debug("catalog_input", null); return original; }
            Class<?> immutable = Class.forName("wpa", false, original.getClass().getClassLoader());
            if (!immutable.isInstance(original)) { debug("catalog_type", null); return original; }
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
            Object expanded = copy.invoke(null, tokens);
            debug("catalog_added", null);
            return expanded;
        } catch (Throwable failure) {
            debug("catalog_exception", failure);
            return original;
        }
    }

    public static void register(Object controller, Context context) {
        String stage = "register_input";
        try {
            if (controller == null || context == null) { debug(stage, null); return; }
            stage = "register_icon";
            int icon = context.getResources().getIdentifier(TOKEN, "drawable", context.getPackageName());
            if (icon == 0 || !"drawable".equals(context.getResources().getResourceTypeName(icon))) { debug(stage, null); return; }
            stage = "register_binding";
            ClassLoader loader = controller.getClass().getClassLoader();
            Class<?> descriptor = Class.forName("mtr", false, loader);
            Class<?> builder = Class.forName("mtm", false, loader);
            Class<?> controllerClass = Class.forName("mwv", false, loader);
            if (!controllerClass.isInstance(controller)) { debug("register_controller_type", null); return; }
            // Gboard keeps a second master catalog in the controller. The
            // order-factory hook alone does not extend that catalog; g() will
            // silently reject an otherwise valid synthetic access point.
            stage = "register_catalog";
            Class<?> orderClass = Class.forName("mwg", false, loader);
            Field helperField = controllerClass.getDeclaredField("g");
            Field masterField = orderClass.getDeclaredField("c");
            if (helperField.getType() != orderClass) return;
            helperField.setAccessible(true);
            masterField.setAccessible(true);
            Object helper = helperField.get(controller);
            Object stockCatalog = masterField.get(helper);
            Object expandedCatalog = extendOrderCatalog(context, stockCatalog);
            if (!(expandedCatalog instanceof Set<?>) || !((Set<?>) expandedCatalog).contains(TOKEN)) {
                debug("register_catalog_missing", null);
                return;
            }
            if (expandedCatalog != stockCatalog) masterField.set(helper, expandedCatalog);
            debug("register_catalog_ok", null);
            stage = "register_builder";
            Object value = method(descriptor, "c", builder, true).invoke(null);
            method(builder, "l", void.class, false, String.class).invoke(value, TOKEN);
            method(builder, "i", void.class, false, int.class).invoke(value, icon);
            Field title = builder.getDeclaredField("d");
            if (title.getType() != String.class || Modifier.isStatic(title.getModifiers())) return;
            title.setAccessible(true);
            title.set(value, "Khmerlish → ខ្មែរ");
            WeakReference<Context> weakContext = new WeakReference<>(context);
            method(builder, "q", void.class, false, Runnable.class).invoke(value,
                    (Runnable) () -> KhmerlishPanelRuntime.open(weakContext.get()));
            Object built = method(builder, "a", descriptor, false).invoke(value);
            stage = "register_descriptor";
            method(controllerClass, "g", void.class, false, descriptor, boolean.class)
                    .invoke(controller, built, false);
            debug("register_descriptor_ok", null);
            stage = "register_position";
            // Put the icon in the visible toolbar once. User reordering/removal
            // is then respected; subsequent keyboard openings never force it back.
            if (!context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getBoolean(PLACED, false)) {
                method(controllerClass, "x", void.class, false, String.class, int.class, boolean.class)
                        .invoke(controller, TOKEN, 0, false);
                context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
                        .putBoolean(PLACED, true).apply();
            }
            debug("register_done", null);
        } catch (Throwable failure) {
            // Debug output is opt-in via Android log settings; it never contains typed text.
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
