# Gemini-only patch targets and verification gate

This workstream targets exactly:

| Component | Required version | Evidence status |
| --- | --- | --- |
| Google App | `17.6.59.ve.arm64` | Awaiting original APK/base and required splits |
| Gemini | `1.0.995038376` | Awaiting original APK/base and required splits |
| MicroG RE | `7.3.0` | Awaiting APK and package/signature verification |

These are active implementation targets, not optional discovery candidates.
Older profiles in the upstream snapshot must not replace these targets or be
copied under a new version name. Google `17.6.59` is preserved exactly as supplied,
not rewritten to `17.60.59` or `17.54.18`.

## Separation

- Gemini metadata, tests and scheduled discovery live under
  `tools/gemini-version-advisor/` and `update-gemini-versions.yml`.
- Do not edit YouTube source, recommendations, release descriptor or `patch.mpp`
  for this workstream.
- A future Gemini compiled artifact must have its own build, manifest, release
  descriptor and compatibility list. No combined YouTube/Gemini bundle.
- The current upstream snapshot remains reference-only, outside Gradle source
  sets. It is not yet a compiled Gemini patch product. Upstream license permission
  remains unresolved before build/redistribution integration.

## Evidence required before marking verified

1. Obtain original APKs (and required splits) for the exact three versions.
2. Extract package name, versionName, versionCode, signing certificate and SHA-256.
3. Inspect DEX/resources; implement exact-version hooks and expected match counts.
   Do not reuse obfuscated Google hooks from a different version without analysis.
4. Build a standalone Gemini patch bundle and patch the exact APK inputs with the
   documented Clone app prerequisite; confirm hooks and output signatures.
5. Test install, launch, MicroG account login, Gemini replies and process restart
   on a device; test work profile separately if claimed supported.
6. Record logs and hashes, then publish verified recommendations. Until these
   gates pass, automatic discovery cannot promote a target to verified.

Current result: target configuration and metadata checks completed;
APK, patch-build and device verification are blocked on the missing inputs.

## Gemini launcher port completed — 2026-10-27

The user-uploaded Gemini APK `1.0.995038376` / code `345` was inspected
and patched successfully with the local `0.1.2` bundle. Both Gemini patches and
APK rebuild passed; the output has four redirected references, no remaining
original Google package constants, and the expected manifest changes.
See `../bundles/gemini/validation.json` and `patch-result.json`.
This supersedes the earlier missing-input/build-blocked status for Gemini only.
Google/MicroG target validation and device login/chat tests remain pending.
Download/use `../bundles/gemini/gemini-target.mpp`, not the legacy reference build.
