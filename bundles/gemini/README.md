# Standalone Gemini bundle

## Local Gemini launcher port — 0.1.2

`gemini-target.mpp` adds an exact profile for **Gemini 1.0.995038376,
version code 345**, based on the user's original APK:

SHA-256: `bfa9b10060a1c0e8a1c3f2b01cd513f74a53b364ab9bdb1bca02ae103de3f7e5`.

The profile requires exactly **four** Google package string replacements.
Unsupported versions still fail closed. The isolated build applies the two
compatible Gemini patches to the real input and verifies the patched DEX and
manifest. See `validation.json` and `patch-result.json` after a successful build.
These are build/static checks, not device runtime verification.

Use **gemini-target.mpp**, not the older **gemini-reference.mpp**, for this APK.
Refresh/remove the old Manager source so the selected source shows version 0.1.2.
Select Gemini Redirect to Cloned Google App and Gemini Standalone Support.

This launcher port does not implement or verify Google 17.6.59.ve.arm64 or
MicroG RE 7.3.0. Login/replies on the Huawei device still require runtime testing
and a correctly patched/cloned companion Google app. The upstream documented
Clone app prerequisite and consistent signing across base/splits still apply.
Do not assume removing split requirements restores resources absent from base.

## Legacy reference artifact

`gemini-reference.mpp` is the unchanged upstream v0.1.1 build, with the older
Google 17.54.18.ve.arm64 / Gemini 1.0.958859967 / MicroG RE 7.0.0 profiles.
It does not support Gemini code 345.

## Provenance and isolation

Upstream source is pinned to `cef25d12c71c33f555b52d8330c1ca886bf59ccc`.
Local overlays live in `tools/gemini-apk/`; the vendored snapshot is unchanged.
Upstream declares no license: preserve attribution and resolve permission before
redistribution. No public release is created by the workflow.
YouTube code, manifests, recommendations and root `patch.mpp` are untouched.
