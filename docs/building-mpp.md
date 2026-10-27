# Building `patch.mpp`

`patch.mpp` is a **Morphe Patch Package** — a JAR that contains the compiled Kotlin patch classes plus the compiled extension DEX files. Morphe Desktop / Morphe Manager imports it to patch an original YouTube APK. It is **not** a YouTube APK, and it is **not** a source archive.

The bundle in this repository was produced from these checked-in sources with the Morphe Gradle plugin (`app.morphe.patches` 2.0.0) at bundle version `1.48.1` (`gradle.properties`).

## Prerequisites for a local build

- JDK 21 (Temurin).
- Android SDK with platform 36 and matching build tools (`ANDROID_HOME` / `sdk.dir` in `local.properties`).
- Credentials for the plugin registry `https://maven.pkg.github.com/MorpheApp/registry`:
  - `gpr.user` + `gpr.key` in `~/.gradle/gradle.properties`, **or**
  - `GITHUB_ACTOR` + `GITHUB_TOKEN` environment variables (the token needs `read:packages`).
- Network access to `services.gradle.org`, the Gradle Plugin Portal, Google Maven, GitHub Packages and JitPack.

## Local build

```bash
./gradlew :patches:buildAndroid --no-daemon
cp "$(ls patches/build/libs/patches-*.mpp | head -1)" patch.mpp
sha256sum patch.mpp > patch.mpp.sha256
unzip -l patch.mpp | head -20
```

`buildAndroid` adds the extension DEX to the JAR in place, so it must be the **last** Gradle task — a later JVM task would rewrite the archive without DEX.

## CI build (how `patch.mpp` here was made)

`.github/workflows/build-mpp.yml` runs on pushes to the branch that touch `patches/**`, `extensions/**`, `gradle/**` or the Gradle files, and on manual `workflow_dispatch`:

```bash
gh workflow run build-mpp.yml --ref arena/a06798d3-youtube-patch-clone
```

It checks out the branch, sets up JDK 21, runs `./gradlew :patches:buildAndroid`, normalizes the output name to `patch.mpp`, writes `patch.mpp.sha256`, uploads a `patch-mpp` workflow artifact, and publishes both files back onto the branch. The commit is skipped when the bundle is unchanged, and `patch.mpp` is not in the workflow's push path filter, so publishing cannot loop.

Why CI? The Arena sandbox has no JDK or Android SDK and cannot reach the Gradle/Maven hosts, so the real compilation happens on GitHub Actions and the result is pulled into the workspace with a normal `git pull` (Actions artifact downloads use a host the sandbox cannot reach).

## Using the bundle

1. Import `patch.mpp` in Morphe Desktop / Morphe Manager.
2. Provide an **original** YouTube APK whose version is in `patches-list.json` — see [youtube-versions.md](youtube-versions.md) and the [version advisor](../tools/version-advisor/README.md) for the version/ABI/density that fits a phone.
3. Patch and install the resulting APK.

Experimental targets are newer but may crash on some devices; the advisor recommends a stable target by default.

## Verify the bundle

```bash
sha256sum -c patch.mpp.sha256
python3 - <<'PY'
import zipfile
with zipfile.ZipFile("patch.mpp") as z:
    names = z.namelist()
    print("entries:", len(names))
    print(z.read("META-INF/MANIFEST.MF").decode())
    print("extension DEX:", [n for n in names if n.endswith(".mpe")])
PY
```

The v1.48.0 bundle contained 3,094 entries: 1,380 compiled `.class` patch files (847 under `app/morphe/patches/youtube/`, none from the excluded Music/Reddit sets), four extension DEX files (`extensions/all/versioncode/change-version-code.mpe`, `extensions/youtube.mpe`, `extensions/shared-youtube.mpe`, `extensions/shared.mpe`), patch resources/translations, and a `META-INF/MANIFEST.MF` declaring `Version: 1.48.1` and `Patcher-Version: 2.0.0`. `extensions/youtube.mpe` contains the Khmer voice-over client, confirming the local TTS change was compiled into the bundle.

## Troubleshooting

- **`JSONObject.keySet()` compile errors in `KhmerTtsClient.java`** — Android's `org.json.JSONObject` exposes `keys()` but not `keySet()`. The file now uses a small `keySet(JSONObject)` helper that returns `() -> object.keys()`.
- **Plugin/dependency resolution fails** — check `GITHUB_TOKEN`/`gpr.key`, that the token can read packages, and that `google()` / JitPack are reachable.
- **Do not add upstream targets to `patches-list.json`** without syncing the matching Kotlin patch sources; metadata alone would produce broken patches. The [version advisor](../tools/version-advisor/README.md) reports upstream targets that still need syncing.
