# BigTree patches (experimental)

Standalone Morphe bundle for the reviewed BigTree APK only.

## Exact target

- Package: `com.app.bigtree`
- Version: `1.14` (`10`)
- Input APK SHA-256: `51b7b05b0171d0f242b37933af8c570dae50b6da3b33a0bfa7dce5814c08977a`
- Source asset: the `bigtree.apk` asset in the repository's `BigTree` pre-release

## Independent selectors

- **Snap Media** — uses the two-step direct-file flow. Chrome DevTools inspection of the supplied episode URL confirmed that the current site bundle resolves playback through `Android.nativePlayerOpen(JSON.stringify(...))`; its payload contains `url`, `type`, `manifest`, DRM/decryption fields, `backup`, title and quality. The unauthenticated inspection was redirected to `/login`, so it did not expose that episode's signed media response. dev.13 treats the native-player payload as authoritative on `/vplay/` pages, ignores unrelated webpage/tutorial MP4s, evaluates both primary and nested backup candidates, and uses the episode title as the downloaded filename. It permits native `saveFile` only for an unencrypted `mp4` or `progressive` source with no inline manifest, DRM, ClearKey, Youku key, or BBTS key. Adaptive streams, encrypted sources, initialization fragments, individual segments, external-downloader routes, and webpage-control activation remain blocked. This fail-closed behavior prevents another knowingly corrupt file; it does not convert protected/adaptive streams into a downloadable MP4. Dragging moves the button without activating it and remembers its position.
- **Translation to English** — adds an English webpage-translation control and loads Google's hosted Translate Element. Page content is therefore sent to an external Google translation service.

Both selectors are disabled by default and may be selected separately or together.

## Validation

GitHub Actions run `42995492790` built the dev.12 standalone MPP, listed exactly the two selectors, and applied:

1. Snap Media alone;
2. Translation to English alone; and
3. both selectors together.

For every output, static DEX inspection found the expected script marker(s) at the reviewed `LG1/m0;->onPageFinished` hook and verified that the original hook instructions outside the injections were preserved. See the three `*-validation.json` reports.

This does **not** prove live-device behavior. Site CSP, changing page markup, authenticated media URLs, Android storage behavior, Google Translate availability, translation quality, and network access still require device testing.
