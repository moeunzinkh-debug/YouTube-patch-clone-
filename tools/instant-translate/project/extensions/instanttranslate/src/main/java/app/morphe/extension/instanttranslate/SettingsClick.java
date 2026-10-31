/* Copyright (C) 2026. This fork is distributed under GPL-3.0-or-later. */
package app.morphe.extension.instanttranslate;

import kotlin.jvm.functions.Function0;

/** Callback accepted by the reviewed app's existing Compose settings-row renderer. */
public final class SettingsClick implements Function0<Object> {
    public SettingsClick() {}

    @Override public Object invoke() {
        try { SettingsUi.open(); } catch (RuntimeException ignored) { /* preserve app UI */ }
        try {
            // The app's Kotlin Unit singleton is obfuscated in this exact build.
            java.lang.reflect.Field field = Class.forName("c89").getDeclaredField("a");
            field.setAccessible(true);
            return field.get(null);
        } catch (ReflectiveOperationException | RuntimeException ignored) {
            return null;
        }
    }
}
