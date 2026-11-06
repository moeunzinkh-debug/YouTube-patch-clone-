package dev.jason.gboardpatches.extension.khmerlish;

import android.content.Context;
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
    private static final String TOKEN = "gboard_khmerlish_panel";
    private static final String PREFS = "gboard_khmerlish_panel";
    private static final String PLACED = "toolbar_position_initialized";

    private KhmerlishAccessPoint() {}

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
        } catch (Throwable ignored) {
            return original;
        }
    }

    public static void register(Object controller, Context context) {
        try {
            if (controller == null || context == null) return;
            int icon = context.getResources().getIdentifier(TOKEN, "drawable", context.getPackageName());
            if (icon == 0 || !"drawable".equals(context.getResources().getResourceTypeName(icon))) return;
            ClassLoader loader = controller.getClass().getClassLoader();
            Class<?> descriptor = Class.forName("mtr", false, loader);
            Class<?> builder = Class.forName("mtm", false, loader);
            Class<?> controllerClass = Class.forName("mwv", false, loader);
            if (!controllerClass.isInstance(controller)) return;
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
            method(controllerClass, "g", void.class, false, descriptor, boolean.class)
                    .invoke(controller, built, false);
            // Put the icon in the visible toolbar once. User reordering/removal
            // is then respected; subsequent keyboard openings never force it back.
            if (!context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getBoolean(PLACED, false)) {
                method(controllerClass, "x", void.class, false, String.class, int.class, boolean.class)
                        .invoke(controller, TOKEN, 0, false);
                context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
                        .putBoolean(PLACED, true).apply();
            }
        } catch (Throwable ignored) {
            // A missing/changed Gboard toolbar ABI must not break the keyboard.
        }
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
