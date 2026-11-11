# BigTree patches (experimental)

Standalone Morphe bundle for the reviewed BigTree APK only.

## Exact target

- Package: `com.app.bigtree`
- Version: `1.14` (`10`)
- Input APK SHA-256: `51b7b05b0171d0f242b37933af8c570dae50b6da3b33a0bfa7dce5814c08977a`
- Source asset: the `bigtree.apk` asset in the repository's `BigTree` pre-release

## Independent selectors

- **Snap Media** — adds a movable round button and a two-step capture/download flow. The first tap starts a 20-second capture window and locks a full direct video URL discovered through media elements, links/data attributes, Fetch/XHR, resource timing, dynamically added content, embedded script URLs, accessible frames, or BigTree's native `shouldInterceptRequest` hook for cross-origin iframe traffic. When a direct file is captured, the button turns green. The second tap passes that locked URL, filename, and video MIME type to BigTree's native `saveFile` bridge for a direct device download. HLS/DASH manifests, initialization fragments, and individual segments are not passed to `saveFile` as fake MP4 files. It never guesses or clicks webpage controls. Dragging moves the button without activating it and remembers its position.
- **Translation to English** — adds an English webpage-translation control and loads Google's hosted Translate Element. Page content is therefore sent to an external Google translation service.

Both selectors are disabled by default and may be selected separately or together.

## Validation

GitHub Actions run `42955395308` built the dev.8 standalone MPP, listed exactly the two selectors, and applied:

1. Snap Media alone;
2. Translation to English alone; and
3. both selectors together.

For every output, static DEX inspection found the expected script marker(s) at the reviewed `LG1/m0;->onPageFinished` hook and verified that the original hook instructions outside the injections were preserved. See the three `*-validation.json` reports.

This does **not** prove live-device behavior. Site CSP, changing page markup, authenticated media URLs, Android storage behavior, Google Translate availability, translation quality, and network access still require device testing.
