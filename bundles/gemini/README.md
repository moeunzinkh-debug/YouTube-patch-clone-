# Gemini / Google bundle — 0.2.0

**`bundle.mpp` is the active bundle.** `gemini-target.mpp` is an identical alias.
The former 0.1.x/reference binaries and duplicate experimental workflow were
removed from the current tree. Git history retains the previous versions.

## Active implementation

Google process identity is now handled by `ProcessIdentityPatch.kt`: rewrite
process strings and their same-method hash comparisons to the cloned package,
while keeping the real Android process-name provider unchanged. The old
`ProcessNameSanitizePatch` is deleted from the build checkout before compilation.
Only one process strategy is compiled. The patch name still says experimental
because successful device launch has not been established.

This replaces the **process strategy**, not every supporting patch. Existing
version-specific Google/Gemini GMS, manifest and account-permission patches are
retained. The original vendored upstream snapshot remains reference-only for
provenance; it is not an alternate active bundle.

## Exact inputs

- Google 17.6.59.ve.arm64 / code 301698282.
- Gemini 1.0.995038376 / code 345.
- MicroG RE 7.3.0-dev.2 (`app.revanced.android.gms`), installed separately.

Build workflow: `.github/workflows/build-gemini-mpp.yml`.
Evidence: `build-status.json`, `process-validation.txt`, patch-result and
validation JSON files. APK validation is separate from Android runtime testing.
The output DEX comparison verifies the native provider stays unchanged, 40
process strings are renamed, and two process hash constants are updated.

## Device testing

Import this bundle only (source version 0.2.0); deselect older custom sources.
Start from original APKs. For Google, also select official Clone app with
`updatePermissions=true`, `updateProviders=true` and default package name.
Expected clone: `com.google.android.googlequicksearchbox.morphe`.
Leave the three account workaround patches off. Use matching density splits
from the original Google bundle and consistent base/split signing.
Test Google launch first, then Gemini/account/chat. Do not erase app/account data
to force installation. No device crash fix or end-to-end compatibility is claimed.

YouTube code and root patch.mpp are unchanged. Attribution/license notices for
upstream remain applicable; upstream snapshot permission is still unresolved.
