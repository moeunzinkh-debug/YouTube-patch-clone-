# Releases and tags / ការចេញផ្សាយ និងស្លាក

## Tag scheme

| Pattern | Meaning |
| --- | --- |
| `v<major.minor.patch>` | **Patch-bundle release.** An annotated tag whose version matches `version` in `gradle.properties`. Pushing it automatically creates a GitHub Release through `.github/workflows/release-mpp.yml`. |
| `youtube-<version>` | **Supported YouTube target marker.** A lightweight annotated tag pointing at the source revision that supports that YouTube version. It carries no release assets. |

Current tags:

| Tag | Type | Notes |
| --- | --- | --- |
| [`v1.47.0`](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/tag/v1.47.0) | annotated + GitHub Release | Compiled `patch.mpp` (JAR + extension DEX), SHA-256 checksum and `patches-bundle.json`. |
| [`youtube-21.20.405`](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/tree/youtube-21.20.405) | annotated | Recommended **stable** YouTube target, min Android 9 / SDK 28. |
| [`youtube-21.40.161`](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/tree/youtube-21.40.161) | annotated | Newest **experimental** YouTube target, min Android 10 / SDK 29. |

All tags point at the same source revision — they are labels, not separate builds. See the [tag list](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/tags) and the badges in [README.md](../README.md).

## What a release contains

| Asset | Purpose |
| --- | --- |
| `patch.mpp` | The compiled Morphe Patch Package. Import into Morphe Desktop/Manager; it is **not** an installable YouTube APK. |
| `patch.mpp.sha256` | SHA-256 of the bundle. Verify with `sha256sum -c patch.mpp.sha256`. |
| `patches-bundle.json` | Morphe Manager source descriptor (`version`, `download_url`, `created_at`, `description`). The copy in the repository root is the one Manager reads from the default branch; the release copy is generated for the tag. |

The bundle declares `Version: 1.47.0` and `Patcher-Version: 1.14.0` in `META-INF/MANIFEST.MF`. See [building-mpp.md](building-mpp.md) for how it is built and verified.

## Supported YouTube versions in this release

Nine targets from `patches-list.json`:

- **Stable:** `21.20.405` (SDK 28), `21.16.256` (SDK 28), `20.51.39` (SDK 28), `20.21.37` (SDK 26)
- **Experimental:** `21.40.161` (SDK 29), `21.39.522` (SDK 29), `21.38.130` (SDK 29), `21.28.208` (SDK 29), `21.23.492` (SDK 28)

Use the [version advisor](../tools/version-advisor/README.md) to choose a version/APK variant for a specific phone, or read [youtube-versions.md](youtube-versions.md) for the catalog diff against upstream.

## Cutting a new release

1. Make sure `patch.mpp`, `patch.mpp.sha256`, `patches-list.json` and `gradle.properties` agree on the version. Rebuild the bundle if the patch sources changed (`.github/workflows/build-mpp.yml`).
2. Regenerate the descriptor on the default branch (`version` + `download_url` must name the new tag), and update the badges/tag table in `README.md`.
3. Tag and push:

```bash
git tag -a v1.48.0 -m "YouTube patch bundle v1.48.0"
git push origin v1.48.0
```

4. `release-mpp.yml` verifies the bundle, generates `patches-bundle.json` for the tag and creates the GitHub Release with `--verify-tag --generate-notes --latest`. If the release already exists it only replaces the assets (`gh release upload --clobber`).
5. Optionally re-run the same workflow manually with `workflow_dispatch` and a `tag` input.

To add another YouTube target tag:

```bash
git tag -a youtube-21.42.241 -m "Supported YouTube target 21.42.241 (experimental)"
git push origin youtube-21.42.241
```

> A `youtube-*` tag alone does **not** make a new YouTube version patchable — the Kotlin patch sources must be synced from upstream first (see the note in [youtube-versions.md](youtube-versions.md)).

## Using this repo as a Morphe patch source

`patches-bundle.json` follows the Morphe Manager schema:

```json
{
  "created_at": "2026-10-27T07:36:58Z",
  "description": "...",
  "download_url": "https://github.com/<owner>/<repo>/releases/download/<tag>/patch.mpp",
  "signature_download_url": "",
  "version": "1.47.0"
}
```

Add the source with `https://morphe.software/add-source?github=moeunzinkh-debug/YouTube-patch-clone-`, or import `patch.mpp` directly in Morphe Desktop. Always patch an **original, unmodified** YouTube APK whose version is listed above, and select patches from this source only (mixing sources causes the `MORPHE_BRANDING.TXT` collision).
