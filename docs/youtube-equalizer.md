# YouTube in-app equalizer (local bundle 1.48.2)

Select **Audio equalizer** when patching a supported original YouTube APK.
Open **YouTube → Morphe settings → Video → Audio equalizer**.
Start video playback, enable EQ, and refresh/reopen the dialog if the audio
session was not available yet. No app restart is required to apply gains.

- Band frequencies, number of bands, gain range and presets come from Android's
  Equalizer implementation, not a fixed fake five-band UI.
- Levels and enabled state persist in app-private preferences. Reset returns
  every band to flat (0 dB) without changing the enabled switch.
- The effect attaches only to the current positive YouTube audio session ID.
  Session 0 (global output) is never used. A new session releases the old effect
  and restores stored frequency gains. Disabling releases the effect.
- Unsupported engines/control conflicts show a status and do not intentionally
  stop playback. Positive gain, especially combined with Sound Boost or Stable
  Volume, can distort: test at low volume and avoid stacking gain effects.
- Audio offload/tunneling, Bluetooth, cast/remote playback and OEM audio engines
  can bypass or deny effects. This feature does not claim it processes cast audio.
- EQ preferences are separate from the existing settings import/export; they are
  not included in that export. UI text falls back to English if untranslated.

Tests compile the real controller against Android API test doubles to exercise
session replacement, global-session refusal, range clamping, persistence, presets,
reset, lost control and unsupported hardware. These tests do not prove audible
changes on hardware. CI compiles the Android extension and patch bundle; on-device
APK patching and listening tests remain required.

`patches-list.json`/Gradle describe the local 1.48.2 development bundle. The source
release descriptor remains pinned to published 1.48.1 until a separate release is
created; importing the new local patch.mpp is required to try this feature.

## Build evidence

Actions run **40624052185** passed, including 18 controller checks using test
doubles and the real extension source. The resulting bundle manifest declares
1.48.2 / Patcher 2.0.0. Local verification checked bundle SHA-256, the compiled
EqualizerPatchKt, and EqualizerPreference/Android audiofx code in youtube.mpe.
Existing Khmer voice-over DEX checks still pass. No audible hardware validation
or APK fingerprint match is claimed from these compilation checks alone.
