/* Copyright (C) 2026. This fork is distributed under GPL-3.0-or-later. */
package app.morphe.extension.instanttranslate;

import java.io.IOException;

/** Route only to the explicitly selected fallback. Never silently switch providers. */
final class ProviderRouter implements FallbackCoordinator.Client {
    static final String ORIGINAL = "original";
    static final String GOOGLE = "google";
    static final String SEA_LION = "sea_lion";

    interface Selection { String selected(); }
    private final Selection selection;
    private final FallbackCoordinator.Client google;
    private final FallbackCoordinator.Client seaLion;

    ProviderRouter(Selection selection, FallbackCoordinator.Client google, FallbackCoordinator.Client seaLion) {
        this.selection = selection;
        this.google = google;
        this.seaLion = seaLion;
    }

    @Override
    public String translate(String text, String source, String target) throws Exception {
        String current = selection.selected();
        if (GOOGLE.equals(current)) return google.translate(text, source, target);
        if (SEA_LION.equals(current)) return seaLion.translate(text, source, target);
        throw new IOException("No fallback provider selected");
    }
}
