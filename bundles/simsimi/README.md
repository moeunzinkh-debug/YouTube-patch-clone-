# SimSimi patches — experimental, separate from YouTube

**Morphe patch bundle:** [`bundle.mpp`](bundle.mpp), **0.2.0-dev.1**, 41,923 bytes.
Targets **SimSimi 9.2.3** (`com.ismaker.android.simsimi`, code `1119001`, API 24+).
Import this separate `.mpp` into Morphe Manager and select the SimSimi APK. These
are real selectable patches, not a standalone Python APK patcher. Do not replace
the root YouTube `patch.mpp` with this bundle.

<details>
<summary>SimSimi • 4 selectable experimental patches</summary>

| Exact patch name | Default | What it changes / limits |
|---|---|---|
| Disable ad eligibility (experimental) | On | Changes the shared Hermes `canShowAds` gate to false. Not proof every SDK ad is removed; does not simulate rewarded-video completion. |
| Unlock membership UI (client only, experimental) | On | Returns a cloned membership status with `hasMembership=true` for local UI gates. Conversation controls, profile/cover images and photo controls may still require server authorization. Does not grant server items, read receipts, billing, or daily rewards. |
| Pull down to restart chat (experimental) | On | Injects an Activity touch observer and React reload extension. Pull from the top 96dp down at least 160dp; ignores focused text input/scrolled content, cancels multitouch and debounces. Enabled only on the **English Conversation list**, identified by its visible heading and room-list section. Disabled inside chat rooms and on unknown screens. Requests React runtime reload, not process termination or a data-only list refresh; unsaved state may be lost. New screen restriction not yet device-tested. |
| MicroG RE service routing (experimental) | **Off, opt-in** | Routes exact native GMS package literals to `app.revanced.android.gms`; adds package visibility and `EXTENDED_ACCESS`. Requires separately installed compatible MicroG RE. This is partial routing, **not full GMS compatibility** or an implementation of missing APIs. |

</details>

The user reports the existing features working on their device. This does not
independently verify server entitlements, full GMS coverage or the newly added
Conversation-only screen restriction.

## Requested feature status

- **Ads:** shared eligibility gate implemented; complete ad/reward-SDK removal unverified.
- **Membership:** local UI gates implemented, not backend entitlements. All items,
  read receipts and individual server-controlled features are **not unlocked** by proof.
- **Daily bonus without rewarded video:** no dedicated bypass implemented; no
  fabricated reward callbacks or server credit grants.
- **MicroG RE:** native routing implemented; sign-in, Firebase App Check,
  signatures, attestation, Billing and other API compatibility remain unverified.
- **Swipe down:** corrected to the Conversation list in your screenshot, not inside chat rooms. Screen matching is currently English-only and fails closed for other layouts/languages.

## Verification — actual MPP application passed

[Actions run 40653945775](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/40653945775)
built the isolated bundle, ran exact-input Hermes JVM tests and the 12-check Java
gesture harness plus 8 Conversation screen checks, then **applied the actual `.mpp` to the original APK using Morphe
Desktop v1.19.1 / Morphe Patcher**, explicitly enabling the optional MicroG patch.
Static validation of that output APK confirmed:

- Combined ads + membership Hermes payload SHA-256:
  `7738259ce661f707f9ac95a44854a0ca7972cf7f6f2a9654fb7170323cba6812`.
- MainActivity dispatch hook and injected pull-refresh runtime in output DEX.
- **66** native literals routed to MicroG RE, with permission/package visibility.
- Original required-splits metadata retained.

See [`morphe-validation.json`](morphe-validation.json) and
[`build-status.json`](build-status.json). This is engine/output validation,
**not an Android Manager UI, installation, device runtime, backend entitlement or
full GMS compatibility test**. No SimSimi release has been published.

Bundle SHA-256:
`52980e1bccdcc22b1b146b1f73a9498f404b0c079f494871a871b703aee8ad51`.
Local archive/checksum verification:
`python3 tools/simsimi/verify_bundle.py bundles/simsimi/bundle.mpp`.

## Installation constraint

The supplied `Simsimi/base.2.apk` declares
`com.android.vending.splits.required=true` and has no native `.so` libraries.
Installation/device testing needs its matching ABI/configuration splits; the
base APK alone is not a complete installable app. Removing that flag would not
create the missing libraries. The current bundle deliberately preserves it.

## Build and safety

- Sources: `tools/simsimi/project`; isolated build: `prepare_build.py`;
  workflow: `.github/workflows/build-simsimi-mpp.yml`.
- Original Hermes SHA-256 is guarded:
  `203256d3824cfbc449d110fca1601095ecf283f555079407d03a2f46ca0c7489`.
- Guarded, composable Hermes transforms preserve sizes/offsets and recompute the
  SHA-1 footer. Membership status is cloned rather than rewriting cached state.
- Native patching preserves superclass touch dispatch; does not kill the app.
- MicroG routing leaves service actions, API hosts and class names unchanged;
  does not fabricate service availability or bypass signature/attestation checks.
- Evidence: `docs/simsimi/apk-inventory.json`, `target-map.json`, `hermes-targets.json`.
  Hermes parser pinned to P1sec/hermes-dec
  `2e796663e1fedb93dca51060797ebf3327b3fedb`.
- YouTube/Gemini bundles and original APK release assets remain untouched.
