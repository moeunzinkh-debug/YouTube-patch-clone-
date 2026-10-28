# Google/Gemini startup review against YouTube GmsCore support

## Shared strategy, separate app-specific implementation

YouTube's `patches/.../shared/misc/gms/GmsCoreSupportPatch.kt` uses vendor
`app.revanced`, hence `app.revanced.android.gms`, the same installed package
as the user's MicroG RE 7.3.0-dev.2. It coordinates Clone app, exact string
rewrites, GMS permissions/actions/authorities, spoofed identity metadata,
app-specific early returns, and an extension startup check.

The Gemini Google companion uses the same GmsCore package, but has different
startup code, signing identity, providers and process-name switches. YouTube's
fingerprints, certificate, startup extension, GNP hooks and early-return targets
must not be copied wholesale into Google. Both being Google products is not
proof of identical GMS dependencies or MicroG implementation coverage.

Google's current redirect intentionally preserves Binder service actions and
rewrites selected UI actions. YouTube rewrites the shared action catalog. This
is a difference to validate against MicroG's exported services and actual failed
calls, not a reason to blindly replace every Google action string.

## Concrete code risks fixed in local 0.1.4

The Google clone process-name hook previously invoked String.replace immediately
before each return from the process-name provider, without a null guard. The
original main-process caller explicitly handles a nullable provider result.
Changing null into an exception would violate that caller's original behavior.
The new hook skips replacement when the return value is null.

The register-expansion helper previously caught reflection failures and merely
printed a note, while injected code used scratch registers regardless. It now
fails closed, verifies the resulting register count, and selects two distinct
scratch registers that do not overlap the returned string. It will refuse to
publish invalid register references rather than emit a broken APK silently.

These are startup-safety defects/risks found by source review. Without a device
crash trace we do not claim either is the confirmed cause on the user's phone.

## Validation actually performed

Run 40617855885 compiled standalone `bundle.mpp` version 0.1.4, downloaded the
user's original inputs by SHA-256 (Google/base.apk and Google/base.1.apk), and
successfully applied/rebuilt both apps. APK tests were NOT skipped.

The additional Kotlin output check reads the patched Google DEX and requires:
- exactly two provider replacement calls and original return sites;
- a null guard on the same returned register before each replacement;
- non-overlapping, in-bounds scratch registers;
- guard branches landing after the replacement sequence.

Existing output checks also verify four Gemini redirects, cloned Google package,
manifest changes, and the new MicroG extended-access permission.

## Still outstanding

No Android device installation/launch/login/chat test has been performed here.
Google's original base APK requires a density split. Removing manifest requirements
does not reconstruct missing resources. The matching split must be handled and
signed consistently with the cloned base. A startup resource error, class loading
failure, permission problem, or unimplemented GMS API still requires device evidence.
Do not clear accounts or promise full compatibility based solely on CI results.

YouTube source, extension and root patch.mpp are unchanged. The old vendored
Gemini snapshot is also preserved; startup changes are local build overlays.
