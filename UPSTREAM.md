# Upstream provenance and subset policy

- **Upstream repository:** [MorpheApp/morphe-patches](https://github.com/MorpheApp/morphe-patches)
- **Upstream ref:** `main`
- **Upstream commit:** `e5464395441e916b643af4e2175c4e253e6df487`
- **Upstream release:** `v1.47.0` (2026-10-11)
- **License:** GNU GPL v3 with additional GPL Section 7 requirements; see the copied [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).

## Selection made for this repository

Included are the YouTube patch package, its common patch packages (`all`, `shared`, and `util`), the YouTube extension and required shared extension modules, the Android stubs/build configuration those modules use, and resources needed by that source. The upstream `patches-list.json` was filtered to 97 entries targeting `com.google.android.youtube` plus 5 generic entries with no app-specific target (102 entries total). Locale resource folders specific to Music and Reddit were removed.

Not included are the separate YouTube Music and Reddit extension/patch packages, their tests, and the upstream all-app bundle. `shared-youtube` is an intentional build/runtime dependency of YouTube and contains reusable helper code; its presence does not add the separate YouTube Music patch set.

This repository is therefore a **modified, YouTube-only source selection**, not a mirror of the complete upstream repository. Local changes include the filtered manifest and resources, a YouTube-only resource checker, removal of the Reddit locale list and YouTube Music Jam validation task, and metadata identifying this unofficial subset. The Voice-over translation code also adds Khmer-only TTS routing to the user's FastAPI Space via OpenAPI endpoint discovery, plus independent voice-over speed and pitch settings. Original YouTube patch implementations are retained from the recorded upstream revision; shared support code remains where required. Additions also include the independent `tools/version-advisor/` catalog/advisor (which reads upstream `patches-list.json` metadata at runtime, but does not vendor upstream patch code) and the generated `docs/youtube-versions.md`. Upstream code attribution and the required notice are preserved.
