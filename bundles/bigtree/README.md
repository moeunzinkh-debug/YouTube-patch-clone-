# BigTree patches (experimental)

Standalone Morphe bundle for the reviewed BigTree APK only.

## Exact target

- Package: `com.app.bigtree`
- Version: `1.14` (`10`)
- Input APK SHA-256: `51b7b05b0171d0f242b37933af8c570dae50b6da3b33a0bfa7dce5814c08977a`
- Source asset: the `bigtree.apk` asset in the repository's `BigTree` pre-release

## Independent selectors

- **Snap Media** — adds a movable round download icon. A tap prioritizes full HLS/DASH manifests or full media/download URLs, rejects individual stream segments, and sends the result through BigTree's reviewed `openAppDownload` Android `ACTION_VIEW` path for an external downloader such as IDM. If no verified media URL exists, it shows an instruction instead of clicking an unrelated page control. Dragging moves the icon without starting a download and remembers its position.
- **Translation to English** — adds an English webpage-translation control and loads Google's hosted Translate Element. Page content is therefore sent to an external Google translation service.

Both selectors are disabled by default and may be selected separately or together.

## Validation

GitHub Actions run `42953360227` built the updated standalone MPP, listed exactly the two selectors, and applied:

1. Snap Media alone;
2. Translation to English alone; and
3. both selectors together.

For every output, static DEX inspection found the expected script marker(s) at the reviewed `LG1/m0;->onPageFinished` hook and verified that the original hook instructions outside the injections were preserved. See the three `*-validation.json` reports.

This does **not** prove live-device behavior. Site CSP, changing page markup, authenticated media URLs, Android storage behavior, Google Translate availability, translation quality, and network access still require device testing.
