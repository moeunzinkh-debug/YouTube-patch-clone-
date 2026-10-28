# Experimental direct-Translate fork (development)

This is an **experimental overlay**, not the upstream release. `apply_overlay.py` first verifies the 913-file upstream `extras/gboard-patches/` tree, then creates a temporary copy and adds the files in `overlay/`. It admits one additional opt-in Morphe patch while retaining the 43 upstream registrations and explicitly registers its runtime ABI calls. It never modifies the pinned source tree or the upstream MPP. The source is GPL v3; see the upstream [LICENSE](../../extras/gboard-patches/LICENSE), [NOTICE](../../extras/gboard-patches/NOTICE), and original project [Gboard-patches](https://github.com/jasonwu1994/Gboard-patches).

Target: **only** `com.google.android.inputmethod.latin`, version name `18.5.4.993608717-release-arm64-v8a`, version code `176049702`. The patch validates the exact native provider, request, callback, method prototypes and selected bytecode references before rewriting. Matching signatures are not proof that a different APK is safe or that the Android runtime works. An initial `dev.1` build was withdrawn after an illegal cross-class private-field read was found; `dev.2` uses an accessor inside the owning class and the CI fixture verifies that the readiness hook no longer reads the private field directly.

## What changes

* Only the existing Gboard Translate UI callback (`kli`) routed through the reviewed Google cloud provider (`kjx`) is intercepted. Native language selectors, input handling, callback rendering and the existing throttle remain. Health-check callbacks are not replaced. Source `auto` is supported; translated segments are joined and the detected language is passed to the native callback.
* The selected Translate text is sent in an HTTPS **POST body** directly to `translate.googleapis.com/translate_a/single` with `client=gtx`. The endpoint is undocumented, unsupported, can rate-limit or change, and requires a network. The code does not log request text, credentials, URLs or response bodies; Google and the network/OS may still process or record traffic. HTTP redirects are disabled; timeouts and input/response limits are enforced. Errors return Gboard's native status-1 response. There is no fallback to another service or automatic retry.
* Native `Lkka` can select an Android system/offline provider. For the Translate UI callback alone, the patch routes through its Google cloud provider where that provider has the reviewed type. Thus **this fork overrides offline routing for that UI**. Its readiness change bypasses cloud health-status failure only when the controller exists, is not stopped and the reviewed Google provider exists. Other readiness decisions and non-UI callback routing remain native. The original behavior in all app/device states is not proven.
* Each new native input invalidates prior work, including empty edits. Weak references to the exact request/callback pair prepared by the native UI prevent a delayed native throttle callback from starting a new HTTP request after another edit or keyboard closure. Queued/stale results are discarded. An HTTP request already sent cannot be unsent. If the exact runtime reflection bindings unexpectedly fail for a still-current request, the bridge returns to Gboard's original provider code; the preceding wrapper/readiness changes still apply. The implementation cannot guarantee all privacy behavior without device testing.

## Validation and build

`python3 tools/gboard-translate/test_fixture.py` runs offline tests of the temporary binary-manifest fixture. Java unit tests cover UTF-8 POST encoding, language codes, multi-segment JSON, 429/redirect/error handling, and callback/cancellation behavior with controlled fake connections and native classes. An opt-in CI probe uses the Java client to POST fixed synthetic English→Khmer, Khmer→English, and auto→Khmer phrases; its outcome is reported separately and is not an Android test. The GitHub workflow builds a temporary fork, runs the runtime ABI inventory and selected extension tests, checks Morphe Desktop's listing, then applies the **actual** MPP to a fixture derived from a SHA-pinned *third-party prepatched and renamed* exact-version APK. Only the fixture's binary manifest package string is changed to let Morphe select the real patch; this does **not** make it a stock Google-signed APK. The patched fixture and input APK are never published. `validation.json` records the actual CI outcome if a build succeeds.

No original Google-signed APK application, Android keyboard runtime, actual user-network check, or security audit has been performed. Synthetic English↔Khmer/auto requests received HTTP 200 in a separate GitHub runner; that does not establish device availability or fix the unknown cause of the original failure.

Development build (Java 21, Android SDK and authorized Morphe Packages access required):

```sh
python3 tools/gboard-translate/apply_overlay.py /tmp/gboard-direct-source
cd /tmp/gboard-direct-source
./gradlew :patches:test --tests '*runtimeabi.*' :patches:buildAndroid generatePatchesList --no-daemon
./gradlew :extensions:extension:testDebugUnitTest --tests '*directtranslate.*' --no-daemon
```

The fork is distributed separately as the experimental [Gboard Direct Translate dev.2 pre-release](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/tag/Gboard-Direct-Translate-v4.0.0-dev.2). It does not replace `Gboard-v4.0.0`, the original upstream bundle, YouTube or SimSimi.
