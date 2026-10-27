# Gemini / MicroG RE patches — vendored snapshot v0.1.1

Cloned from [ryuya0124/gemini-microg-patches](https://github.com/ryuya0124/gemini-microg-patches),
tag [`v0.1.1`](https://github.com/ryuya0124/gemini-microg-patches/releases/tag/v0.1.1),
commit `cef25d12c71c33f555b52d8330c1ca886bf59ccc` (2026-09-06).

These are Morphe patches that make **Gemini** work with **microG RE**
(`app.revanced.android.gms`, ReVanced GmsCore 7.0.0) in the normal profile and in
Samsung Secure Folder / work profile (user 150). They target the **Google app and
the Gemini launcher**, not YouTube.

## ⚠️ Not part of `patch.mpp`

This directory is **reference/vendored source only**:

- It is **outside** every Gradle source set, so it is **not compiled** into this
  repository's `patch.mpp` (which stays a YouTube-only bundle).
- The upstream project builds with a standalone `kotlinc` + D8/R8 pipeline
  (`scripts/compile-patches.sh`, `scripts/build-mpp.sh`), not this repo's
  `app.morphe.patches` Gradle plugin. Its patches also refuse to run on any APK
  version other than the two profiles recorded in `docs/versions/`.
- To actually patch, add the **upstream repository as a separate Morphe Manager
  source** (`https://morphe.software/add-source?github=ryuya0124/gemini-microg-patches`)
  or import the upstream `.mpp` (`gemini-microg-patches-0.1.1.mpp`) as a Local source.
  `patches-bundle.json` here is a copy of the upstream descriptor for reference;
  Morphe Manager reads the one on the *upstream default branch*, not this copy.

> Do **not** select patches from this source and from `YouTube Patch Clone`
> (or Morphe Patches) in the same patching session — see the
> `MORPHE_BRANDING.TXT` note in [`docs/gemini-microg-patches.md`](../../docs/gemini-microg-patches.md).

## Supported targets (exact, verified by the upstream author)

| App | Package | Version | Version code |
| --- | --- | --- | --- |
| Google App (AGSA) | `com.google.android.googlequicksearchbox` | `17.54.18.ve.arm64` | `301800642` |
| Gemini launcher | `com.google.android.apps.bard` | `1.0.958859967` | `332` |
| microG RE | `app.revanced.android.gms` | `7.0.0` | — |

Input APK SHA-256 hashes and per-hook definitions live in `docs/versions/`.
Patches abort if `VersionHookRegistry` finds no verified profile for the input.

## The 13 patches

Grouped as in the README `<details>` tags of the parent repository.

- **MicroG RE / GmsCore:** `Google App Manifest Tweaks`,
  `GmsCore Bytecode Redirect (MicroG RE 7.0.0)`,
  `GmsCore Signature and Availability Bypass`, `MicroG Account Permissions`
- **Gemini launcher:** `Gemini Redirect to Cloned Google App`, `Gemini Standalone Support`
- **Google App clone:** `Google App Package Clone Support`,
  `Process Name Spoofing for Clone Support`
- **Work profile / Secure Folder:** `Bypass Work Profile Gemini Restriction`,
  `Allow Work Profile Gemini Eligibility`
- **Account sync (disabled by default, `default = false`):**
  `Account Switch Lock Bypass`, `Account Sync Binder Loop Fix`,
  `Account ID Fallback for Clone` — upstream keeps these off because forcing a
  fixed AccountId / Binder success caused login failure and sync loops.

## Requirements

- microG RE (`app.revanced.android.gms`) with a Google account signed in, in the
  same Android user/profile where Gemini runs. `app.revanced.gms.EXTENDED_ACCESS`
  is requested at Gemini startup.
- Official Morphe patches **1.41.0** `Clone app` patch with
  `updatePermissions=true` and `updateProviders=true` (Expert mode in Manager).
- Original, unmodified AGSA `17.54.18.ve.arm64` APK plus its `xxhdpi` split, and
  Gemini launcher `1.0.958859967` base APK. All three outputs must be signed with
  the same key.

## Provenance and licence

`SOURCE.json` lists every vendored file with its size and SHA-256. The upstream
repository publishes **no LICENSE file**; its README says it builds on Morphe
Desktop, Morphe patches and microG. This snapshot is kept for documentation and
offline reference only. For redistribution or reuse, check the upstream author's
terms — do not assume it is covered by this repository's GPLv3 `LICENSE` / `NOTICE`.
