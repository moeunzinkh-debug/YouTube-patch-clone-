# Gemini + Google standalone bundle — local 0.1.4

Use **`bundle.mpp`** (identical to `gemini-target.mpp`) for:

| Component | Exact inspected input | Validation |
| --- | --- | --- |
| Gemini launcher | 1.0.995038376 / code 345 | Both patches, rebuild, output DEX and manifest passed |
| Google App | 17.6.59.ve.arm64 / code 301698282 | Eight default custom patches + official Clone app and rebuild passed; output manifest checked |
| MicroG RE | 7.3.0-dev.2 / code 255070302 | APK inspected; app.revanced.android.gms package and EXTENDED_ACCESS declaration confirmed |

MicroG is installed separately, not patched by this bundle. No login/chat/device
runtime validation is claimed. CI does not prove that missing split resources
are present or that an APK installs/launches on a phone.

## Manager / patching

1. Import `bundle.mpp`; ensure the source version is **0.1.4**, not 0.1.1/0.1.2.
2. For Gemini's original base APK, use the two default Gemini patches.
3. For Google's original base APK, use the eight default Google patches plus
   official **Clone app** (tested with upstream's pinned official Morphe 1.41.0
   bundle). Set `updatePermissions=true` and `updateProviders=true`; leave
   Clone app's package name at its default. Expected output package:
   `com.google.android.googlequicksearchbox.morphe`.
4. Leave the three account workaround patches disabled. They were not ported,
   are not runtime verified, and must not be enabled for this target.
5. The Google input requires a density split (`base__density`). Obtain the split
   from the exact same original app bundle. Adapt its package for the clone and
   sign it with the **same key** as the patched base before installing together.
   Removing manifest split requirements cannot recreate missing resources.
6. Install the user's MicroG RE 7.3.0-dev.2 ARM64 build separately, complete its
   account setup, then test the Google clone and Gemini. Signing/install and
   device runtime behavior still need verification. Do not uninstall existing
   apps or accounts without backing up data and checking signing compatibility.

Do not use a full YouTube bundle as a replacement for the official Clone app
prerequisite. YouTube source/configuration/root `patch.mpp` are not part of this
workstream and have not been modified.

## Compatibility implementation

Exact source profiles are in `tools/gemini-apk/overlay/` and are applied to a fresh
pinned upstream checkout. Original vendored files remain unchanged. Google hooks
were resolved from actual DEX evidence (`docs/google-target-hooks.txt`), not by
renaming obfuscated classes blindly. The MicroG permission is changed only for
Google 17.6.59; legacy profiles retain their original permission.

The historical patch name `GmsCore Bytecode Redirect (MicroG RE 7.0.0)` is retained
from upstream. For the new Google profile the target package is still
`app.revanced.android.gms`, with the new fully qualified extended-access permission.
This label is not evidence of runtime compatibility with either MicroG version.

## Evidence and artifacts

- `patch-result.json`: Gemini execution/rebuild results.
- `validation.json`: Gemini output DEX (four redirects) and manifest validation.
- `google-patch-result.json`: all nine selected Google patches passed.
- `google-validation.json`: Google clone manifest/package/permission checks.
- `bundle.mpp.sha256`: checksum for the new compiled JVM + Android DEX bundle.
- `gemini-reference.mpp`: legacy unmodified v0.1.1; **do not use for these inputs**.

This is a local version 0.1.4, not an upstream release. No upstream release URL or
public download descriptor is published. Source attribution is retained; upstream
has no declared license, so resolve permission before redistribution.

## Build workflow repair (current status)

The workflow now runs on `main` and `arena/**` when build inputs change, and can
also be dispatched manually. Concurrent branch updates are fetched/rebased before
retrying publication; conflicts are never overwritten with a force push.

The uploaded `Gemini/base.apk` and `Google/base.apk` release inputs are currently
unavailable. Compilation still runs, but real-APK tests are explicitly marked
`not-run-inputs-missing` in `build-status.json`. The artifact contains that status
alongside the bundle and checksum, not historical APK reports presented as a new
validation. Existing patch-result/validation files retain earlier historical
results; consult their associated run and the current `build-status.json`.

To require a full fresh APK test, restore both exact release assets and manually
run the workflow with `require_apk_tests=true`. Missing inputs then fail clearly;
a failed patch/rebuild or output verification also fails the build. No missing
input is treated as a successful APK test. Device/runtime tests remain separate.

## Startup hardening — local 0.1.4

Process-name sanitization now preserves null and verifies scratch register safety.
Run 40617855885 executed BOTH real-APK test paths and an additional output DEX
check of null guards, register indices and branch targets. Both apps patched and
rebuilt successfully; device startup/login remains unverified.
The reuploaded inputs are now resolved by digest even when Gemini is named
`base.1.apk` under release `Google`; the earlier missing-input note above is historical.
See [source comparison and review](../../docs/gemini-startup-review.md).
