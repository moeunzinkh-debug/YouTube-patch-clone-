package dev.jason.gboardpatches.extension.khmerlish;

/** Geometry guard for placing the panel inside an existing Gboard keyboard area. */
final class KhmerlishPanelBounds {
    private KhmerlishPanelBounds() {}

    static boolean fits(int parentWidth, int parentHeight, int left, int top, int width, int height) {
        return parentWidth > 0 && parentHeight > 0 && left >= 0 && top >= 0
                && width > 0 && height > 0
                && (long) left + width <= parentWidth && (long) top + height <= parentHeight;
    }
}
