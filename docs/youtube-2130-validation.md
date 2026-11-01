# YouTube 21.30.216 development bundle validation

## Compiled bundle

- Bundle: [`patch.mpp`](../patch.mpp), version `2.0.0-dev.1`, Patcher `2.0.0`.
- SHA-256: `1ad416a7ce886dca2b8131e82f7c59c6e86bca1d1c30352eefe6b77f5bad1775` ([checksum](../patch.mpp.sha256)).
- [Build and listing workflow](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/41296407900): Android patch-code DEX and extension DEX built; 166 upstream YouTube JVM tests passed. The generated manifest and Morphe Desktop listings agree on 110 YouTube and 5 generic selectors, including all four new selectors. The normal list exposes stable `21.30.216`, and the experimental list also exposes `21.43.523` and `21.42.241`.
- The bundle verifier checks for the custom EQ, FastAPI Khmer TTS, SEA-LION configuration, and the four new extension classes. This proves their presence, not their device behavior.

## Manager recommendation

[Morphe Manager 2.3.0-dev.3 on an Android 15 emulator](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/41297041561) imported this local bundle and visibly marked **21.30.216 Recommended**. That run did not finish patch application because its UI automation failed to focus the patch-search field; it is not evidence of a Manager patch or app runtime.

## Desktop patch-application smoke test

[Actions run 41296853854](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/41296853854) used Morphe Desktop `1.20.0-dev.1` to patch YouTube `21.30.216` without forcing compatibility. **109 selected patches succeeded**, including `Download post images`, `Search comments`, `Translate posts`, `Niconico comments`, `Audio equalizer`, and `Voice over translation`. The rebuilt APK passed archive and signing verification.

The temporary stock APK was extracted from a pinned third-party module archive and independently checked: package `com.google.android.youtube`, version `21.30.216`, min SDK 29, SHA-256 `3775a15129dcc4e5b80fc17b7e0841b7fdd1ca89a6e72baa798806f666c74d02`, with valid rotated Google signing certificates `3d7a1223019aa39d9ea0e3436ab7c0896bfb4fb679f4de5fe7c23f326c8f994a` and `5aad2bee6db95d17e05a08d7d1e64c10a1511879154483916b6ae6c7fd9cb0c6`. Neither APK was installed, launched, committed, or uploaded.

## Limits

An offline patch-application smoke test is not a device runtime test. The new UI, player layout/spacing, Android 9 fallback, FastAPI playback, SEA-LION access, and live chat/translation services require actual device and network validation. The public release and source descriptor remain at v1.49.0; this development bundle has not been published as a new release.
