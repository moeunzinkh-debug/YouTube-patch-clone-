# Gemini / Google / MicroG RE version recommendations

> Gemini-only project targets. No shared YouTube compatibility or release configuration.
> កំណែគោលដៅមិនមែនជាកំណែដែលបានផ្ទៀងផ្ទាត់ទេ។

| App | Active patch target | Verified recommendation | Target status |
| --- | --- | --- | --- |
| Google App | `17.6.59.ve.arm64` | `pending APK and runtime verification` | unverified |
| Gemini | `1.0.995038376` | `pending APK and runtime verification` | unverified |
| MicroG RE | `7.3.0` | `pending APK and runtime verification` | unverified |

The active targets are user-pinned and are never replaced with older upstream versions.
Legacy source snapshot `v0.1.1` is reference material, not verification of these targets.
Do not combine independently discovered versions as a verified working set.
New upstream profile filenames are discovery metadata, not compatibility proof.
MicroG release numbers are not auto-promoted: this snapshot declares only its pinned version.

## Upstream discovery

Checked upstream commit: `d1c8a2008901634ece533e53d6b1caa66226ac18`.
- Google App: 17.54.18.ve.arm64
- Gemini: 1.0.958859967
- MicroG RE: no app profile published

## Automatic updates

GitHub Actions checks every six hours and on manual dispatch. Failures leave the catalog unchanged.
Run `python3 tools/gemini-version-advisor/update.py` online or add `--offline` for local-only generation.
Targets are configured in `tools/gemini-version-advisor/targets.json`.
Updating recommendations requires a reviewed source snapshot, exact APK profiles/hashes and runtime validation.
This job never edits the vendored source, builds Gemini patches, downloads APKs, or claims device testing.
