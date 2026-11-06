# Upstream provenance and subset policy

- **Upstream repository:** [MorpheApp/morphe-patches](https://github.com/MorpheApp/morphe-patches)
- **YouTube source base:** [`v2.0.0`](https://github.com/MorpheApp/morphe-patches/releases/tag/v2.0.0), commit `6cb8e6b6ee425eda8a854e026507286359f38a32`.
- **Previous source base:** upstream tag `v1.48.0`, commit `f3acc10e2691ffc4db29c6a6a651ee61fb54c047`. Earlier documentation incorrectly identified this tag as `a5662d30d3`.
- **Targeted later fix:** [`589c3abbe540026426f3336b04c2f13cd692b127`](https://github.com/MorpheApp/morphe-patches/commit/589c3abbe540026426f3336b04c2f13cd692b127), the Translate posts crash fix for Android versions below 10. The fingerprint/reference access was adapted to the v2.0 patcher API used here.
- **License:** GNU GPL v3 with additional GPL Section 7 requirements; see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).

## Selection made for this repository

The development `patches-list.json` and `patch.mpp` describe **110 YouTube selectors plus 5 generic selectors**. The four selectors added in the v2.0.0 sync are `Download post images`, `Search comments`, `Translate posts`, and `Niconico comments`. The previously added nine YouTube patches and the custom `Audio equalizer` remain included.

The recommended stable target for Android 10+ is **YouTube `21.30.216`** (minimum SDK 29). For Android 9, the newest stable target is **`21.23.492`** (SDK 28); `21.28.208`, `20.51.39` and `20.26.46` are also stable targets. `21.43.523` and `21.42.241` are upstream experimental targets, visible in Manager only when experimental versions are enabled. Morphe Manager reads the compatibility targets compiled into the MPP, not just the JSON catalog.

Included are the YouTube patch package, its common patch packages (`all`, `shared`, and `util`), the YouTube extension and required shared extension modules, Android stubs/build configuration, and resources needed by that source. Locale resource folders specific to Music and Reddit are excluded. Not included in `patch.mpp` are the separate YouTube Music and Reddit patch sets or the upstream all-app bundle. `shared-youtube` is a necessary dependency and does not add the YouTube Music patch set.

Local customizations retained through the sync include the in-app equalizer and top-player shortcut, Khmer FastAPI TTS, the SEA-LION voice-over translation provider, existing Khmer translations, the YouTube-only resource checker, and fork metadata. This is a **modified YouTube-only selection**, not an unmodified upstream mirror. See [`docs/upstream-sync.md`](docs/upstream-sync.md) for the current sync and historical details, and [`docs/youtube-versions.md`](docs/youtube-versions.md) for the generated target catalog.

## Development bundle versus release

The source update and built bundle on this branch use version **`2.0.0-dev.1`**, published as a [YouTube pre-release](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/tag/v2.0.0-dev.1). The stable YouTube release and default `patches-bundle.json` remain at **`1.49.0`**. To try the development update, [download `patch.mpp`](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/download/v2.0.0-dev.1/patch.mpp) and import it as a local patch source in Morphe Manager. The repository source does not automatically discover this GitHub pre-release.

Alternatively, the release contains a descriptor, also available as a [pinned direct JSON source](https://raw.githubusercontent.com/moeunzinkh-debug/YouTube-patch-clone-/refs/tags/v2.0.0-dev.1/docs/releases/v2.0.0-dev.1/patches-bundle.json); it stays on this version instead of tracking later updates. Compilation, patch application, and actual behavior on a device are separate validation stages; a listed target alone does not establish runtime success.
