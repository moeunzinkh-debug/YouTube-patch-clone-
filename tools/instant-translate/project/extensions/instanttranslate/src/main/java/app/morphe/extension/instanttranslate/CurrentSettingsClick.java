/* Copyright (C) 2026. This fork is distributed under GPL-3.0-or-later. */
package app.morphe.extension.instanttranslate;

import kotlin.jvm.functions.Function0;

/** Settings callback for the reviewed v7.5.00307 Compose row. */
public final class CurrentSettingsClick implements Function0<Object> {
    public CurrentSettingsClick() {}

    @Override public Object invoke() {
        try { SettingsUi.open(); } catch (RuntimeException ignored) { /* preserve app UI */ }
        try {
            java.lang.reflect.Field field = Class.forName("d1b").getDeclaredField("a");
            field.setAccessible(true);
            return field.get(null);
        } catch (ReflectiveOperationException | RuntimeException ignored) {
            return null;
        }
    }
}
