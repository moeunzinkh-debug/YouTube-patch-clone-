# Experimental Gboard Khmerlish overlay

This builds a separate Morphe `.mpp` from the verified `jasonwu1994/Gboard-patches` v4.0.0 source plus the existing Direct Translate overlay. The new selectable patch adds an off-by-default switch under Gboard **Patches** settings. The vendored upstream tree and existing published bundles/releases are not modified.

## Offline data and attribution

The compressed, byte-for-byte dataset `data/eng_khm_data.txt.gz` decompresses to SHA-256 `20158d40982b4860c2072038f751610b22815983d7be445021e2bcbe04501550`. It comes from [`Chhunneng/khmer-text-transliteration`](https://github.com/Chhunneng/khmer-text-transliteration/tree/fe8028f10296ba6299bebec5cea42b471a56dc0f) commit `fe8028f10296ba6299bebec5cea42b471a56dc0f`, `khmer_text_transliteration/data/raw/eng_khm_data.txt`. Copyright (c) 2025 Chrea Chanchhunneng; MIT license reproduced at [`overlay/patches/src/main/resources/gboard-khmer/LICENSE.txt`](overlay/patches/src/main/resources/gboard-khmer/LICENSE.txt), included in the MPP and copied with the dictionary into the patched APK.

`build_dictionary.py` deterministically filters to lowercase single-token Latin spellings and Khmer-script values. It drops single-letter and ambiguous entries, then applies the explicit examples/common spellings in `data/overrides.tsv`; the reviewed `o` → `អូន` is the only one-letter exception. The output has **24,506 exact matches**, not a contextual language model. Typing is processed temporarily in memory and is not automatically learned, logged or transmitted. Users can explicitly save personal pairs as described below. Check with `python3 tools/gboard-khmer/build_dictionary.py --check`.

## Operation and safety

The automatic setting sees a word boundary after normal typing, and only edits a word previously observed in the same input session. It rechecks editor focus, cursor and the exact suffix before a batched edit. It leaves unknown/ambiguous entries unchanged, and only joins a space it inserted itself between consecutive converted words.

The separate toolbar icon opens an offline Khmerlish panel without enabling the automatic setting. Its lower input drives live replacement of the panel's own output in the host app. It overlays the measured Gboard `keyboard_holder`, rather than the full IME decor (which may cover the app but have untouchable regions); it refuses to open if the holder is absent or too small. The panel's simplified QWERTY/symbol keyboard is separate from normal Gboard, and closing it restores the normal view and accessibility state. The output writer verifies the current editor, collapsed cursor and exact prior output before replacing anything.

Both modes ignore passwords, email/URL/numeric/no-suggestions and no-personalized-learning fields. A failed insertion triggers best-effort restoration; arbitrary editor implementations can still misbehave. There is no network component in the Khmerlish implementation.

## Personal dictionary and word guide

In **Gboard settings → Patches → Khmerlish → Personal Dictionary & Documents**, search the bundled and personal spellings by Khmerlish or Khmer. The **Personal** tab adds, edits, renames and deletes explicit word pairs. One key is a single `a`–`z` token (case-insensitive, at most 32 characters); a value contains Khmer text (at most 128 characters, no line breaks or tabs). Personal entries take precedence over bundled entries in both conversion modes; deleting an override restores the bundled spelling if present. This is a separate dictionary, not Gboard's personal dictionary.

Import UTF-8 `.txt`, `.tsv` or `.csv`: one pair per line as `khmerlish,ខ្មែរ` or `khmerlish<TAB>ខ្មែរ`. An optional `khmerlish,khmer` header, `#` comments and quoted fields are accepted; PDF, DOCX, spreadsheets, multiword Latin keys and malformed or duplicate rows are not. An import may contain at most 5,000 entries and 2.5 MB; the total personal dictionary is limited to 5,000. The entire file is validated off the UI thread before an atomic merge. Existing personal entries are preserved by default; replacing conflicts requires explicit confirmation, and stale previews fail without modifying the data. Export creates a UTF-8 TSV file for backup.

Only deliberately saved/imported pairs are stored in the app-private, credential-protected, **no-backup** directory. They are not synced or included in automatic Android backup; export before uninstalling, clearing Gboard data, or replacing a package. Import/export uses the Android file picker only when the user requests it. If private storage is locked or unavailable, Khmerlish conversion fails closed until the next input session can reload it; the ordinary keyboard remains available. The snapshot is refreshed at input start and after a local edit. No typed host-app text is automatically collected.

Gboard can autocorrect a Roman word before the automatic mode sees the space, in which case the feature safely skips it. Disable Gboard autocorrect for testing. This experiment targets only version name `18.5.4.993608717-release-arm64-v8a` and code `176049702`; new versions require a fresh review of the obfuscated lifecycle methods. Device and stock-Gboard behavior must be validated separately from algorithm tests and patching the already-patched third-party fixture.

To create the isolated source tree locally (requires the upstream Android/Gradle/Morphe packages toolchain):

```sh
python3 tools/gboard-khmer/test_khmer.py -v
python3 tools/gboard-khmer/apply_overlay.py /tmp/gboard-khmer-source
cd /tmp/gboard-khmer-source
./gradlew :patches:test --tests '*runtimeabi.*' :patches:buildAndroid generatePatchesList
./gradlew :extensions:extension:testDebugUnitTest --tests '*khmerlish.*'
```

The Android workflow uses the actual MPP in a disposable, re-signed third-party-derived hybrid on an emulator. It exercises the toolbar and normal typing and attempts the personal CRUD, guide and import/export flow with synthetic text. This is not stock Gboard or a physical-device test. The workflow can finish green even when its emulator step fails; inspect [`android-smoke.json`](../../bundles/gboard-khmer/android-smoke.json), its `emulator_action_outcome`, the individual checks and its bundle SHA rather than the job color. The hybrid and synthetic test helpers are never distributed.

See [`bundles/gboard-khmer/README.md`](../../bundles/gboard-khmer/README.md) for usage, limitations, and the experimental bundle after a successful build. No APK is committed or released by the workflow.
