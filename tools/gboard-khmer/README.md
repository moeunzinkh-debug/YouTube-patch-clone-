# Experimental Gboard Khmerlish overlay

This builds a separate Morphe `.mpp` from the verified `jasonwu1994/Gboard-patches` v4.0.0 source plus the existing Direct Translate overlay. The new selectable patch adds an off-by-default switch under Gboard **Patches** settings. The vendored upstream tree and existing published bundles/releases are not modified.

## Offline data and attribution

The compressed, byte-for-byte dataset `data/eng_khm_data.txt.gz` decompresses to SHA-256 `20158d40982b4860c2072038f751610b22815983d7be445021e2bcbe04501550`. It comes from [`Chhunneng/khmer-text-transliteration`](https://github.com/Chhunneng/khmer-text-transliteration/tree/fe8028f10296ba6299bebec5cea42b471a56dc0f) commit `fe8028f10296ba6299bebec5cea42b471a56dc0f`, `khmer_text_transliteration/data/raw/eng_khm_data.txt`. Copyright (c) 2025 Chrea Chanchhunneng; MIT license reproduced at [`overlay/patches/src/main/resources/gboard-khmer/LICENSE.txt`](overlay/patches/src/main/resources/gboard-khmer/LICENSE.txt), included in the MPP and copied with the dictionary into the patched APK.

`build_dictionary.py` deterministically filters to lowercase single-token Latin spellings and Khmer-script values. It drops single-letter and ambiguous entries, then applies the explicit examples/common spellings in `data/overrides.tsv`; the reviewed `o` → `អូន` is the only one-letter exception. The output has **24,506 exact matches**, not a contextual language model. User text is processed temporarily in memory, but is not persisted, logged or transmitted; no words are learned. Check with `python3 tools/gboard-khmer/build_dictionary.py --check`.

## Operation and safety

The feature sees a word boundary after normal typing, and only edits a word previously observed in the same input session. It rechecks editor focus, cursor and the exact suffix before a batched edit. It leaves unknown/ambiguous entries unchanged, and only joins a space it inserted itself between consecutive converted words. It ignores passwords, email/URL/numeric/no-suggestions and no-personalized-learning fields. A failed insertion triggers best-effort restoration; arbitrary editor implementations can still misbehave. There is no network component in the Khmerlish implementation.

Gboard can autocorrect a Roman word before the feature sees the space, in which case the feature safely skips it. Disable Gboard autocorrect for testing. This experiment targets only version name `18.5.4.993608717-release-arm64-v8a` and code `176049702`; new versions require a fresh review of the obfuscated lifecycle methods. Device and stock-Gboard behavior must be validated separately from algorithm tests and patching the already-patched third-party fixture.

To create the isolated source tree locally (requires the upstream Android/Gradle/Morphe packages toolchain):

```sh
python3 tools/gboard-khmer/test_khmer.py -v
python3 tools/gboard-khmer/apply_overlay.py /tmp/gboard-khmer-source
cd /tmp/gboard-khmer-source
./gradlew :patches:test --tests '*runtimeabi.*' :patches:buildAndroid generatePatchesList
./gradlew :extensions:extension:testDebugUnitTest --tests '*khmerlish.*'
```

See [`bundles/gboard-khmer/README.md`](../../bundles/gboard-khmer/README.md) for usage, limitations, and the experimental bundle after a successful build. No APK is committed or released by the workflow.
