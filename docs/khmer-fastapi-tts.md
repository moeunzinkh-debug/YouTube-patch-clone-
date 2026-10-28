# Direct Khmer FastAPI speech: verified request contract

## Root cause

The deployed `/openapi.json` lists `POST /api/process-multi` but does not declare
its request body. Automatic discovery skipped it. Sending a JSON object with
`text` also returned HTTP 400, `No data provided`.

The public frontend `/script.js` establishes the actual wire contract:

```text
POST https://takumi0002-tts-kh.hf.space/api/process-multi
Content-Type: multipart/form-data; boundary=...

data = [{"text":"សួស្តី","voiceName":"piseth","speed":1.0,"pitch":0}]
autoSpeed = false
```

`data` is a **form field containing a JSON array**, not a top-level JSON body.
`voiceName` uses the backend alias `piseth`, not the Edge voice identifier.
The app now posts this form directly without fetching OpenAPI first.

The client requests a single natural-speed clip; the existing player handles
caption scheduling and playback rate/pitch. Do not include absolute video/SRT
start/end times in each request, as that could add unwanted server-side silence.
The default voice stays Piseth; this fix does not add a voice selection UI.

## Verification

A live multipart probe returned HTTP 200, `audio/mpeg`, 13,004 bytes.
FFprobe identified MP3, 24,000 Hz, duration 3.192 seconds. Evidence:
`docs/diagnostics/khmer-tts-synthesis.json`.

The JVM regression harness compiles the actual `KhmerTtsClient.java` against a
real org.json implementation and test doubles for Android-only helpers. It tests
UTF-8/escaping, multipart framing, direct POST routing, blank input, HTTP errors,
empty audio, and connection cleanup. On Ubuntu/JDK 21:

```sh
sudo apt-get install libandroid-json-java
bash tools/khmer-tts-tests/run.sh
# Optional live synthesis; sends one short Khmer test phrase to the server:
bash tools/khmer-tts-tests/run.sh --live /tmp/khmer-test.mp3
```

The diagnostic workflow also runs that actual Java client against the live
endpoint and validates its output using FFprobe. Audio is temporary, not checked
into Git. Diagnostic JSON records the tested source commit and results.

Android bundle compilation runs separately in CI. Device playback, synchronization,
server cold-start latency and extended-video reliability still require testing.
No published release assets are modified by this fix.
