# SimSimi patches — experimental, separate from YouTube

This project targets **SimSimi 9.2.3** (`com.ismaker.android.simsimi`, version code
`1119001`, minimum API 24). The original input is `base.2.apk` in the `Simsimi`
release. No YouTube/Gemini source, bundle, release assets or recommended versions
are changed by this project.

**Do not treat this as a completed membership/ads/GMS bundle.** The first
implementation changes the app's shared `canShowAds` eligibility function. It is
not proven to remove every ad, and does not synthesize ad-completion events,
credit rewards, or grant server-side membership.

<details>
<summary>Experimental patch catalog (first implementation)</summary>

| Patch | Implementation | Validation |
|---|---|---|
| Disable ad eligibility (experimental) | Exact Hermes 96 function #6882, `canShowAds`: change its final true return to false; existing false return stays unchanged. | Exact-input transform tests and isolated bundle build run in CI. No on-device validation. |

</details>

## Requested feature status

| Feature | Status |
|---|---|
| Ad removal | Initial shared eligibility gate implemented; not a complete all-SDK ad remover. |
| Membership features (conversation slider, profile/cover images, sending photos, read receipts, items) | Not implemented. App has server membership update/entitlement paths; individual gates need analysis. |
| Daily bonus without rewarded videos | Not implemented. No fake ad reward or credit callbacks have been added. |
| GMS / MicroG RE compatibility | Not implemented. Native Firebase App Check, Google sign-in, Billing, and age-signal integrations need individual handling; renaming one service package is not sufficient. |
| Pull down to reload home/chat | Not implemented. Existing `onRefreshAction` and `reloadMainRouteNavigation` functions are identified but not yet wired to a new gesture. |

## Important installation constraint

The uploaded base declares `com.android.vending.splits.required=true` and has no
native `.so` libraries. Matching configuration/ABI split APKs (or a full `.apks`/
`.xapk` set) are needed for installation and device testing. The base alone is
sufficient for static mapping and the guarded Hermes transform tests, not proof
of a working installed app. Keep the required-splits flag intact: clearing it
would not create the missing libraries.

## Build and safety

- `tools/simsimi/prepare_build.py` creates a temporary isolated Morphe project.
- Patch sources live under `tools/simsimi/project`, outside the YouTube module.
- Input Hermes payload must match SHA-256
  `203256d3824cfbc449d110fca1601095ecf283f555079407d03a2f46ca0c7489`.
- Unsupported/already-modified inputs fail before writing resources.
- The transform changes one byte in the function, preserves code sizes/offsets,
  and recomputes the Hermes SHA-1 footer. It does not alter membership state.
- `build-simsimi-mpp.yml` builds only the separate experimental bundle; no
  automatic release publication or original APK upload is performed.

Read-only evidence: `docs/simsimi/apk-inventory.json`, `target-map.json`, and
`hermes-targets.json`. The Hermes parser is pinned to
P1sec/hermes-dec commit `2e796663e1fedb93dca51060797ebf3327b3fedb`.
