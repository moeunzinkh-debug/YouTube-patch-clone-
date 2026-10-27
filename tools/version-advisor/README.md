# YouTube Version Advisor / អ្នកណែនាំកំណែ YouTube

**English:** A small, dependency-free tool that (1) keeps the list of supported YouTube versions up to date automatically from the upstream Morphe patch bundle, and (2) analyses a phone's Android SDK level, CPU ABI, screen density and RAM to recommend the YouTube version — and the right APK variant — that fits that phone.

**ខ្មែរ៖** ឧបករណ៍តូចមួយដែល (១) ធ្វើបច្ចុប្បន្នភាពបញ្ជីកំណែ YouTube ដែលគាំទ្រដោយស្វ័យប្រវត្តិពី upstream Morphe patch bundle និង (២) វិភាគកម្រិត Android SDK, CPU ABI, ដង់ស៊ីតេអេក្រង់ និង RAM របស់ទូរសព្ទ ដើម្បីណែនាំកំណែ YouTube និងប្រភេទ APK ដែលសាកសមជាមួយម៉ូដែលទូរសព្ទរបស់អ្នកប្រើប្រាស់។

> This repository contains **patch sources**, not a YouTube app or APK. The advisor never downloads, hosts or modifies YouTube APKs — it only tells you which supported version/variant to patch.

---

## Quick start

```bash
# 1. Refresh the catalog from upstream (also regenerates docs/youtube-versions.md)
python3 tools/version-advisor/run.py update --write-docs

# 2. Find out which version fits a phone
python3 tools/version-advisor/run.py recommend --model "Galaxy A54 5G" --lang km
python3 tools/version-advisor/run.py recommend --model SM-A546B --json

# 3. Start the bilingual web UI (English + ខ្មែរ) on http://localhost:8000
python3 tools/version-advisor/run.py serve --host 0.0.0.0 --port 8000
```

Requires Python 3.9+ and nothing else — the server uses only the standard library.

## How the automatic update works

| Where | What happens |
| --- | --- |
| `run.py update` | Reads this repo's `patches-list.json`, fetches `MorpheApp/morphe-patches` `patches-list.json` through the GitHub contents API (conditional `If-None-Match` ETag request), extracts every `com.google.android.youtube` target and writes `data/supported-versions.json` + `docs/youtube-versions.md`. |
| `.github/workflows/update-youtube-versions.yml` | Runs the update every 6 hours, on pushes to the manifest/tool, and on manual dispatch. It commits the generated catalog + docs only when the content actually changes. |
| `run.py serve` | Refreshes the catalog once in the background at startup and then every `--refresh-hours` (default 6). The browser re-reads `/api/state` every 5 minutes, so new upstream versions appear without a reload. |
| `POST /api/refresh` / the **Check upstream** button | Triggers an on-demand refresh immediately. |

Two channels are tracked so the tool never recommends something the checked-in patch sources cannot build:

* **local** — versions declared by this repository's `patches-list.json` (default for recommendations, safe).
* **upstream** — the newest upstream targets. New versions appear as “needs sync” in the UI and in the `changes.added` diff.

If GitHub is unreachable, the last known good catalog is kept and `upstream.syncError` explains why; nothing is overwritten with empty data. Set `GITHUB_TOKEN` (or `GH_TOKEN`) for a higher API rate limit. `ADVISOR_UPSTREAM_OWNER`, `ADVISOR_UPSTREAM_REPO` and `ADVISOR_UPSTREAM_REF` can point the sync at a fork.

> ⚠️ Updating the **catalog** is not the same as porting **patch code**. Targets are metadata; adding a new target to `patches-list.json` without syncing the matching Kotlin patch implementations from upstream would produce broken patches. That source sync stays a reviewed, manual step.

## How the phone-model analysis works

1. **Detection** — the web UI reads the browser user agent plus `navigator.userAgentData` high-entropy hints (`model`, `platformVersion`, `architecture`, `bitness`). On the CLI, `--adb` reads `ro.build.version.sdk`, `ro.product.cpu.abilist`, `ro.sf.lcd_density`, etc. from a USB-connected phone. Users can also pick one of 69 bundled models (`data/devices.json`) or type every value manually; manual values always override guesses.
2. **Compatibility** — every supported version has a `minSdk` (Android API level) and a stability flag. A version is compatible when `device.sdk >= minSdk`.
3. **Scoring** — newer is better, but a stable build always outranks a newer experimental build; exact-minimum SDK and <3 GB RAM get small penalties. Every option carries bilingual reason codes (`stable`, `sdk_ok`, `sdk_fail`, `headroom`, `sdk_exact`, `low_ram`, …), so the recommendation is explainable rather than a black box.
4. **APK guidance** — `nodpi`/universal APK is recommended, with the device's primary ABI (`arm64-v8a`, `armeabi-v7a`, …) and density bucket (`hdpi`…`xxxhdpi`) for split APKs. Android Go / 32-bit and no-GMS devices get extra warnings.

Example result (Galaxy A54 5G, Android 13 / SDK 33): newest compatible `21.40.161` (experimental), recommended `21.20.405` (stable, min SDK 28), APK `nodpi` + `arm64-v8a` + `xxhdpi`.

## CLI reference

```bash
run.py update [--offline] [--check] [--write-docs] [--json] [--timeout 20]
run.py versions [--channel local|upstream] [--json]
run.py devices "SM-A546B" [--limit 12] [--json]
run.py recommend --model "Galaxy A54 5G" [--sdk 33] [--abi arm64-v8a] \
                 [--density xxhdpi] [--ram 6] [--adb [SERIAL]] \
                 [--user-agent "..."] [--channel local|upstream] \
                 [--lang en|km] [--json]
run.py serve [--host 0.0.0.0] [--port 8000] [--refresh-hours 6] [--offline]
```

`--adb` example:

```bash
python3 tools/version-advisor/run.py recommend --adb --lang km
```

## Web API

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/api/state` | GET | catalog + device database + server/refresh status |
| `/api/health` | GET | liveness + auto-refresh status |
| `/api/devices?q=...` | GET | model search |
| `/api/detect` | POST | user-agent/high-entropy hints → normalized device profile |
| `/api/recommend` | POST | device fields + `channel` → full bilingual analysis |
| `/api/refresh` | POST | on-demand upstream sync, returns the new catalog |

All responses are JSON with both `en` and `km` text for reasons. The UI uses only same-origin relative URLs, so it works behind the Arena live-preview proxy.

## Adding a phone model

Append an entry to `data/devices.json`:

```json
{
  "id": "brand-model", "brand": "Brand", "name": "Model name",
  "models": ["MODEL-CODE"], "aliases": ["Short name"],
  "android": "13", "sdk": 33, "abi": ["arm64-v8a", "armeabi-v7a"],
  "density": "xxhdpi", "dpi": 450, "ramGb": 6, "year": 2023,
  "tags": []
}
```

Tags: `low-ram`, `go32` (Android Go / 32-bit), `no-gms` (no Google Play services). Values are indicative factory/major-upgrade specs only; the UI always lets the user override them.

## Tests

```bash
python3 -m unittest discover -s tools/version-advisor/tests -v
```

Covers manifest parsing, version ordering, channel diffing, offline sync, model lookup, user-agent and SDK parsing, density/ABI selection, recommendation scoring for new/old/unsupported phones, bilingual reasons, and the HTTP API.

## Files

```
tools/version-advisor/
├── advisor/            # catalog, devices, recommend, i18n, cli, server (stdlib only)
│   ├── catalog.py      # upstream sync + ETag cache + markdown docs
│   ├── devices.py      # device DB lookup, UA/ADB detection, profile merge
│   ├── recommend.py    # explainable compatibility scoring
│   ├── i18n.py         # English / Khmer reason templates
│   ├── cli.py          # update / versions / devices / recommend / serve
│   └── server.py       # threaded HTTP server + JSON API
├── data/               # devices.json + generated supported-versions.json
├── web/                # index.html, app.js, styles.css, favicon.svg
├── tests/              # unittest suite
└── run.py              # entry point
```
