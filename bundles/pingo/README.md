# Pingo AI patches (experimental)

Standalone Morphe bundle for the exact Pingo AI APK in the repository's `Pingo` pre-release.

## Exact target

- Package: `com.picoai.languageapp.android`
- Version: `5.4.8` (`941`)
- Minimum SDK: 26
- APK SHA-256: `1ef37fd47d97dae52318ea0a084652d375bccc277e394ab298ab9014234a1c57`
- Release asset: `Pingo_5.4.8.apk` (asset ID `742911905`, 72,566,868 bytes)

## Independent selectors

- **Remove license check** — disables the two reviewed PairIP client-side Play-license entry points (`checkLicense` and `initializeLicenseCheck`). It does not forge a successful Play response and does not create purchases or subscriptions.
- **Unlock all feature** — forces the reviewed Superwall SDK local `SubscriptionStatus.isActive()` and `Entitlement.isActive()` predicates to return true. This may suppress local paywall gates. It cannot create billing purchases, consumable credits, backend authorization, or unlock server-controlled AI features. Pingo's application logic is compiled as Hermes bytecode, so this selector is deliberately limited to the exact native local gates proven in the APK.

Both selectors are disabled by default and can be selected separately or together.

## Scope and validation

The APK was statically inspected and pinned before targeting. It is a React Native app with an 8.57 MB Hermes bytecode bundle, eight DEX files, PairIP, Google Play Billing, and Superwall. Generic SDK names or strings are not treated as proof of an application entitlement.

The build workflow applies each selector independently and both together to the exact release APK, then checks the rebuilt DEX methods. Static application does not prove live runtime behavior, server acceptance, credits, purchases, or feature availability; device testing is still required.
