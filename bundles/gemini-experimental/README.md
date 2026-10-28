# Experimental Google/Gemini bundle 0.2.0

This is an isolated **first-stage process identity experiment**, NOT a complete
replacement GmsCore engine. The stable 0.1.4 bundle remains in bundles/gemini/.

The old process provider sanitization is removed. This version keeps the real
Android process name and rewrites matching process strings and hash literals in
their methods. Methods with switch payloads are rejected rather than partially
rewritten. Existing version-specific GMS mappings and other baseline patches are
retained to isolate this experiment. No claim of a device crash fix is made.

Design reference: MrHuaweiFan/GmsCore-Patches Google app process-string/hash
strategy. This implementation is local; no external app-specific class names or
version claims are reused. Read docs/gemini-startup-review.md for baseline context.

Use only the exact original Google 17.6.59.ve.arm64/code 301698282 and Gemini
1.0.995038376/code 345 inputs. Official Clone app prerequisite still applies.
Google density splits and consistent base/split signing remain necessary.
Never mix the stable and experimental custom bundles in one patch session.
Do not erase account data to try this. Runtime login/chat/launch remain untested.
