# Experimental Google/Gemini bundle 0.2.0

This is an isolated **first-stage process identity experiment**, NOT a complete
replacement GmsCore engine. The stable 0.1.4 bundle remains in bundles/gemini/.

The old process provider sanitization is removed. This version keeps the real
Android process name and rewrites matching process strings and hash literals in
their methods. Switch payloads containing process hash keys are rejected rather than
partially rewritten; unrelated enum/id switches are left intact. Existing version-specific GMS mappings and other baseline patches are
retained to isolate this experiment. No claim of a device crash fix is made.

Design reference: MrHuaweiFan/GmsCore-Patches Google app process-string/hash
strategy. This implementation is local; no external app-specific class names or
version claims are reused. Read docs/gemini-startup-review.md for baseline context.

Use only the exact original Google 17.6.59.ve.arm64/code 301698282 and Gemini
1.0.995038376/code 345 inputs. Official Clone app prerequisite still applies.
Google density splits and consistent base/split signing remain necessary.
Never mix the stable and experimental custom bundles in one patch session.
Do not erase account data to try this. Runtime login/chat/launch remain untested.

## Actual test result

Run 40620366179 completed successfully. Both exact uploaded APKs were patched
and rebuilt. Output comparison verified **40 process string references and two
hash constants**, with the original `Ldgtr;->b()` provider instructions/registers
unchanged. `process-validation.txt` records this result. SHA-256 verified locally.

For device testing, select ONLY the experimental custom bundle plus the official
Clone app prerequisite for Google. Start from original APKs, never repatch an
already modified APK. Verify the source version is 0.2.0, then test Google before
Gemini. Keep backups and use consistent signing; do not delete accounts/app data
just to force installation. Google density split integration remains outstanding.
A successful CI patch/rebuild does not establish that either app launches.
