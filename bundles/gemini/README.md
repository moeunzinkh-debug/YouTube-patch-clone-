# Standalone Gemini reference build

`gemini-reference.mpp` is compiled from upstream v0.1.1, commit
`cef25d12c71c33f555b52d8330c1ca886bf59ccc`. It is NOT a port to the current targets.

- Reference profiles: Google 17.54.18.ve.arm64, Gemini 1.0.958859967, MicroG RE 7.0.0.
- Current project targets: Google 17.6.59.ve.arm64, Gemini 1.0.995038376, MicroG RE 7.3.0.
- The current targets remain unsupported by this reference bundle.
- Compilation and patch discovery do not establish APK/device compatibility.
- Upstream declares no license. Preserve attribution; no public release is
  created by this workflow. Resolve permission before redistribution.
- YouTube's sources, manifest, descriptor and root patch.mpp are not used or edited.

Build workflow: `.github/workflows/build-gemini-mpp.yml`. It uses a separate
checkout of the pinned upstream source and its own pinned toolchain. Results
include a SHA-256 checksum and the upstream patch discovery listing.
