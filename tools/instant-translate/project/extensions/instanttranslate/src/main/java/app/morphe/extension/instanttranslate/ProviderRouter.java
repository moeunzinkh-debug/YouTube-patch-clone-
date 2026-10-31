/* Copyright (C) 2026. This fork is distributed under GPL-3.0-or-later. */
package app.morphe.extension.instanttranslate;

import java.io.IOException;

/** Route only to SEA-LION when explicitly selected; all other values fail closed. */
final class ProviderRouter implements FallbackCoordinator.Client {
    static final String ORIGINAL = "original";
    static final String SEA_LION = "sea_lion";

    interface Selection { String selected(); }
    private final Selection selection;
    private final FallbackCoordinator.Client seaLion;

    ProviderRouter(Selection selection, FallbackCoordinator.Client seaLion) {
        this.selection = selection;
        this.seaLion = seaLion;
    }

    static String normalizeSelection(String value) {
        return SEA_LION.equals(value) ? SEA_LION : ORIGINAL;
    }

    @Override
    public String translate(String text, String source, String target) throws Exception {
        if (SEA_LION.equals(selection.selected())) return seaLion.translate(text, source, target);
        throw new IOException("SEA-LION fallback is not selected");
    }
}
