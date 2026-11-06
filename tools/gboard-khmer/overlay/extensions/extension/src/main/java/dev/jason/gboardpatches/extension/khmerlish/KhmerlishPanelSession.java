package dev.jason.gboardpatches.extension.khmerlish;

/** One host-field composing session; no text is persisted or transmitted. */
final class KhmerlishPanelSession {
    interface Output {
        boolean isCurrent();
        boolean replace(String text);
        void finish();
    }

    private final KhmerlishDictionary dictionary;
    private final Output output;
    private boolean active = true;
    private boolean hasComposition;

    KhmerlishPanelSession(KhmerlishDictionary dictionary, Output output) {
        if (dictionary == null || output == null) throw new IllegalArgumentException();
        this.dictionary = dictionary;
        this.output = output;
    }

    boolean update(CharSequence roman) {
        if (!active || roman == null || roman.length() > KhmerlishPanelConverter.MAX_LENGTH) return false;
        try {
            if (!output.isCurrent()) {
                close();
                return false;
            }
            String converted = KhmerlishPanelConverter.convert(roman, dictionary);
            if (!output.replace(converted)) {
                close();
                return false;
            }
            hasComposition = true;
            return true;
        } catch (Throwable unavailable) {
            close();
            return false;
        }
    }

    void close() {
        if (!active) return;
        active = false;
        try {
            if (hasComposition && output.isCurrent()) output.finish();
        } catch (Throwable ignored) {
            // The app may have closed or stopped accepting input already.
        }
    }
}
