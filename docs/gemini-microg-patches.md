# Gemini / MicroG RE patches — cloned source & tags

Upstream: [ryuya0124/gemini-microg-patches](https://github.com/ryuya0124/gemini-microg-patches) —
*Morphe patches for Gemini with microG and Samsung Secure Folder support*.
Vendored tag: **`v0.1.1`** (commit `cef25d12c71c33f555b52d8330c1ca886bf59ccc`, 2026-09-06).
Local copy: [`extras/gemini-microg-patches/`](../extras/gemini-microg-patches/README.md).

## What these patches do

They let the **Gemini** app run on devices without Google Play Services by using
**microG RE** (`app.revanced.android.gms`, ReVanced GmsCore **7.0.0**), both in the
normal Android profile and inside **Samsung Secure Folder / work profile (user 150)**.
The Google app (`com.google.android.googlequicksearchbox`) is cloned to
`com.google.android.googlequicksearchbox.morphe` and Gemini is redirected to it.

Solved by the 13 patches: launching the cloned Google app from Gemini, microG account
sync/sign-in and first-run permission prompts, crashes from process-name mismatch,
account-sync loops, work-profile web redirects and the "not available" error `(19)`.

## ✅ MicroG RE support

| Item | Value |
| --- | --- |
| microG package | `app.revanced.android.gms` (ReVanced GmsCore / **microG RE**) |
| Verified version | `7.0.0` |
| Extended access permission | `app.revanced.gms.EXTENDED_ACCESS` (requested at Gemini startup) |
| Signature spoof metadata | `app.revanced.android.gms.SPOOFED_PACKAGE_NAME`, `…SPOOFED_PACKAGE_SIGNATURE`, `app.revanced.MICROG_PACKAGE_NAME` |
| Redirected GMS surface | 221 actions, 6 authorities, 17 permissions (`config/reference/gms-constants.json`) |

`GmsCore Bytecode Redirect (MicroG RE 7.0.0)` rewrites the GMS package name,
permissions and provider authorities inside the Google app;
`GmsCore Signature and Availability Bypass` forces `SUCCESS`/`true` for signature
and availability checks. `Google App Manifest Tweaks` adds microG visibility and
the spoofing metadata to `AndroidManifest.xml`.

## Verified targets (exact — patches refuse anything else)

| App | Package | Version | Version code | Input SHA-256 |
| --- | --- | --- | --- | --- |
| Google App (AGSA) | `com.google.android.googlequicksearchbox` | `17.54.18.ve.arm64` | `301800642` | base `ec2483a9…f2325`, xxhdpi split `772c1b02…2a9f` |
| Gemini launcher | `com.google.android.apps.bard` | `1.0.958859967` | `332` | base `d080d9d1…9ef6` |
| microG RE | `app.revanced.android.gms` | `7.0.0` | — | installed separately |

Full hashes, hook definitions, expected match counts and validation records:
[`extras/gemini-microg-patches/docs/versions/`](../extras/gemini-microg-patches/docs/versions/README.md).
`VersionHookRegistry.requireProfile(...)` aborts patching when the input
`packageName`/`versionName`/`versionCode` has no verified profile — there is **no
generic fallback** for newer Google/Gemini versions.

## The 13 patches (README `<details>` tags)

| Group | Patches |
| --- | --- |
| 🔐 MicroG RE / GmsCore (4) | `Google App Manifest Tweaks`, `GmsCore Bytecode Redirect (MicroG RE 7.0.0)`, `GmsCore Signature and Availability Bypass`, `MicroG Account Permissions` |
| 🤖 Gemini launcher (2) | `Gemini Redirect to Cloned Google App`, `Gemini Standalone Support` |
| 📦 Google App clone (2) | `Google App Package Clone Support`, `Process Name Spoofing for Clone Support` |
| 💼 Work profile / Secure Folder (2) | `Bypass Work Profile Gemini Restriction`, `Allow Work Profile Gemini Eligibility` |
| 👤 Account sync (3, **off by default**) | `Account Switch Lock Bypass`, `Account Sync Binder Loop Fix`, `Account ID Fallback for Clone` |

The last three are `default = false` on purpose: forcing a fixed `AccountId` or a
fake Binder success caused login failure and infinite sync loops upstream. Leave
them off unless you are debugging that exact problem.

The README block is generated — after updating the vendored snapshot run:

```bash
python3 tools/generate-gemini-catalog.py
python3 tools/generate-patch-catalog.py     # YouTube catalog (unchanged)
```

## Tags / ស្លាក

New annotated tags point at the revision that vendors the snapshot. They are
**labels**, not separate builds:

| Tag | Meaning |
| --- | --- |
| `gemini-v0.1.1` | Vendored upstream release snapshot (13 patches, 19 source/profile files) |
| `gemini-1.0.958859967` | Verified Gemini launcher target (`com.google.android.apps.bard`) |
| `google-17.54.18.ve.arm64` | Verified Google App target (`com.google.android.googlequicksearchbox`) |
| `microg-re-7.0.0` | Verified microG RE version these patches redirect to |

Existing `v1.48.1` / `youtube-*` tags still describe the **YouTube** bundle.

## How to actually use them

1. **This clone does not compile them into `patch.mpp`.** The vendored directory is
   outside all Gradle source sets, so the YouTube bundle is unchanged. Upstream uses
   a standalone `kotlinc` + D8 pipeline, targets different apps, and hard-requires
   two exact APK versions.
2. In Morphe Manager add the **upstream repo as a separate Remote source**:
   `https://morphe.software/add-source?github=ryuya0124/gemini-microg-patches`
   (or download `gemini-microg-patches-0.1.1.mpp` from the
   [upstream release](https://github.com/ryuya0124/gemini-microg-patches/releases/tag/v0.1.1)
   and add it via Sources → Local).
3. Install microG RE `app.revanced.android.gms` **7.0.0** in the same profile/user
   as Gemini and sign in to a Google account. Grant the first-run account and
   `app.revanced.gms.EXTENDED_ACCESS` prompts.
4. Use original, unmodified AGSA `17.54.18.ve.arm64` (+ xxhdpi split) and Gemini
   launcher `1.0.958859967` APKs. All three outputs must be re-signed with the
   **same key** as any existing installation.
5. Select the official Morphe patches **1.41.0** `Clone app` patch with options
   `updatePermissions=true` and `updateProviders=true` (Expert mode).
6. Do **not** select the YouTube patch set for Google/Gemini. Upstream explicitly
   requires its custom Gemini patches **plus** the official `Clone app` patch;
   follow that specific combination, not two overlapping full patch sets.
   This is different from applying both full YouTube sources, which produced
   the `MORPHE_BRANDING.TXT` collision in the earlier YouTube session.
   End-to-end Android Manager use is not verified by upstream; its local build
   scripts handle the Google split and same-key signing workflow.


Samsung note: ADB cannot launch an Activity inside Secure Folder
(`am start --user 150` is refused); open Gemini manually there after installing.

## Known limits

- Only the two exact versions above are supported. New Google/Gemini releases need
  new hook profiles (`VersionHookRegistry`) and re-verification on a device.
- Gemini Live, voice, device-assistant settings, full-device reboot and other
  Google versions are **not** verified by upstream.
- A change to Google/Gemini server behaviour can break it at any time.
- Upstream publishes **no LICENSE file**. The vendored copy is unmodified reference
  source only; see [`extras/gemini-microg-patches/NOTICE`](../extras/gemini-microg-patches/NOTICE).
  Do not assume our GPLv3 licence covers it, and do not redistribute it as part of
  the compiled bundle.

## Refreshing the snapshot

```bash
tmp=$(mktemp -d)
curl -sSL https://codeload.github.com/ryuya0124/gemini-microg-patches/tar.gz/refs/tags/<new-tag> | tar -xz -C "$tmp" --strip-components=1
# copy src/main/kotlin, docs/versions, config/reference, patches-bundle.json
# update SOURCE.json (upstream_tag / commit / file hashes), the docs above and the README badges
python3 tools/generate-gemini-catalog.py
```

Verify every file hash in `SOURCE.json` before committing:

```bash
python3 - <<'PY'
import hashlib, json, pathlib
p = pathlib.Path('extras/gemini-microg-patches')
d = json.loads((p/'SOURCE.json').read_text())
for f in d['files']:
    assert hashlib.sha256((p/f['path']).read_bytes()).hexdigest() == f['sha256'], f['path']
print('all', len(d['files']), 'vendored files verified')
PY
```
