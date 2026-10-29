# Telegram-only patch source and provenance

This is a **modified, separately built subset**, not the upstream multi-app MPP and not an official Telegram or Morphe product.

- Upstream: [rushiranpise/morphe-patches](https://github.com/rushiranpise/morphe-patches), stable tag [`v1.23.1`](https://github.com/rushiranpise/morphe-patches/releases/tag/v1.23.1), commit [`92c0fca0ae103a419c7fc61f9c5b8b38b7d6b82a`](https://github.com/rushiranpise/morphe-patches/tree/92c0fca0ae103a419c7fc61f9c5b8b38b7d6b82a).
- The 17 files in `extras/telegram-upstream/patches/src/main/kotlin/app/template/patches/telegram/` are copied verbatim. Four shared certificate, Firebase, installer and signature helpers, two extension classes, and the necessary build files are also copied verbatim. The complete Git-blob identities are pinned in `upstream-source-manifest.json` and checked by `tools/telegram/prepare_build.py`.
- The temporary build selects only the three Telegram compatibility definitions, makes four generic shared helpers **anonymous dependencies** rather than standalone selectable patches, and changes the project metadata, version, and extension build script. The named Telegram patch implementation files are not altered.
- The `SignatureHookApp` extension credits [ApkSignatureKillerEx](https://github.com/L-JINBIN/ApkSignatureKillerEx); the extension uses [LSPosed HiddenApiBypass 4.3](https://github.com/LSPosed/AndroidHiddenApiBypass), [Apache-2.0](hiddenapibypass-LICENSE.txt). See upstream [LICENSE](../../extras/telegram-upstream/LICENSE) and [NOTICE](../../extras/telegram-upstream/NOTICE). No official branding or endorsement is implied.
- `bundles/telegram/upstream-patches.json` contains only the 15 relevant metadata records from the upstream tag; it is not the upstream project's complete patch list.

Build in CI or on a machine with Java 21, Android SDK, and the Gradle/Morphe package repositories available:

```sh
python3 tools/telegram/test_telegram_subset.py
python3 tools/telegram/prepare_build.py /tmp/telegram-patches-build
cd /tmp/telegram-patches-build
./gradlew :patches:buildAndroid --no-daemon
```

The build recipe and actual verification status are documented in `bundles/telegram/validation.json` after CI succeeds. Copying upstream code or loading an MPP is not evidence of successful installation, Telegram login, live push, premium entitlement, or device behavior. No Telegram APK is distributed by this repository.
