"""Bilingual (English / Khmer) message templates used by the advisor.

Every reason returned by the analyzer carries both languages so the web UI can
switch language instantly without another request.
"""

from __future__ import annotations

LANGS = ("en", "km")

MESSAGES: dict[str, dict[str, str]] = {
    "stable": {
        "en": "Stable target: not flagged as experimental by the patch bundle.",
        "km": "គោលដៅស្ថិរភាព៖ មិនត្រូវបានដាក់ស្លាកជាពិសោធន៍ដោយកញ្ចប់ patch ទេ។",
    },
    "experimental": {
        "en": "Experimental target: newer, but it can crash on some devices.",
        "km": "គោលដៅពិសោធន៍៖ ថ្មីជាង ប៉ុន្តែអាចគាំងលើឧបករណ៍មួយចំនួន។",
    },
    "newest": {
        "en": "Newest compatible YouTube release in this channel.",
        "km": "ជាកំណែ YouTube ថ្មីបំផុតដែលឆបគ្នាក្នុងបណ្ណាល័យនេះ។",
    },
    "older": {
        "en": "{n} release(s) behind the newest compatible version.",
        "km": "នៅពីក្រោយកំណែថ្មីបំផុតដែលឆបគ្នាចំនួន {n}។",
    },
    "sdk_ok": {
        "en": "Needs Android {android} (SDK {sdk})+; your phone has Android {deviceAndroid} (SDK {deviceSdk}).",
        "km": "ត្រូវការ Android {android} (SDK {sdk}) ឡើងទៅ; ទូរសព្ទរបស់អ្នកមាន Android {deviceAndroid} (SDK {deviceSdk})។",
    },
    "sdk_fail": {
        "en": "Needs Android {android} (SDK {sdk})+; your phone only has SDK {deviceSdk}.",
        "km": "ត្រូវការ Android {android} (SDK {sdk}) ឡើងទៅ; ទូរសព្ទរបស់អ្នកមានត្រឹម SDK {deviceSdk}។",
    },
    "sdk_exact": {
        "en": "Your phone only just meets the minimum; an older stable build may feel smoother.",
        "km": "ទូរសព្ទរបស់អ្នកទើបតែគ្រប់លក្ខខណ្ឌអប្បបរមា; កំណែស្ថិរភាពចាស់ជាងអាចដំណើរការរលូនជាង។",
    },
    "headroom": {
        "en": "Your phone is {n} SDK level(s) above the minimum, so there is a safe margin.",
        "km": "ទូរសព្ទរបស់អ្នកខ្ពស់ជាងកម្រិតអប្បបរមា {n} SDK ដូច្នេះមានសុវត្ថិភាពគ្រប់គ្រាន់។",
    },
    "low_ram": {
        "en": "Low-memory phone ({ram} GB RAM): older stable builds and fewer patches usually run better.",
        "km": "ទូរសព្ទមានអង្គចងចាំតិច ({ram} GB RAM)៖ កំណែស្ថិរភាពចាស់ជាង និង patch តិច ជាធម្មតាដំណើរការបានល្អជាង។",
    },
    "no_compatible": {
        "en": "No supported YouTube version runs on this phone (lowest requirement: SDK {minSdk}).",
        "km": "គ្មានកំណែ YouTube ណាដែលគាំទ្រដំណើរការលើទូរសព្ទនេះទេ (តម្រូវការទាបបំផុត៖ SDK {minSdk})។",
    },
    "apk_nodpi": {
        "en": "Download the 'nodpi' / universal YouTube APK (not a bundle or split APK).",
        "km": "ទាញយក YouTube APK ប្រភេទ 'nodpi' / universal (មិនមែន bundle ឬ split APK ទេ)។",
    },
    "apk_abi": {
        "en": "If the site only offers split APKs, pick the {abi} native-library variant.",
        "km": "ប្រើគេហទំព័រផ្តល់តែ split APK សូមជ្រើសប្រភេទបណ្ណាល័យ {abi}។",
    },
    "apk_density": {
        "en": "Match the {density} screen-density variant when one is offered.",
        "km": "ជ្រើសប្រភេទដង់ស៊ីតេអេក្រង់ {density} ប្រើមានផ្តល់ជូន។",
    },
    "apk_go": {
        "en": "This looks like an Android Go / 32-bit phone: use the armeabi-v7a build if arm64 fails.",
        "km": "ទូរសព្ទនេះទំនងជា Android Go / 32-bit៖ ប្រើកំណែ armeabi-v7a ប្រើ arm64 មិនដំណើរការ។",
    },
    "apk_gms": {
        "en": "This device ships without Google Play services; sign-in may need microG.",
        "km": "ឧបករណ៍នេះមិនមាន Google Play services ទេ; ការចូលគណនីអាចត្រូវការ microG។",
    },
    "detect_guess": {
        "en": "Phone details were auto-detected. Confirm your Android version in Settings if unsure.",
        "km": "ព័ត៌មានទូរសព្ទត្រូវបានរកឃើញដោយស្វ័យប្រវត្តិ។ សូមពិនិត្យកំណែ Android ក្នុង Settings ប្រើមិនប្រាកដ។",
    },
    "channel_local": {
        "en": "Recommendations use this repository's checked-in patch sources (v{version}).",
        "km": "អនុសាសន៍ប្រើប្រាស់ប្រភព patch ដែលមានក្នុង repository នេះ (v{version})។",
    },
    "channel_upstream": {
        "en": "Showing upstream v{version}. These targets are not in this repository's patch sources yet.",
        "km": "បង្ហាញពី upstream v{version}។ គោលដៅទាំងនេះមិនទាន់មានក្នុងប្រភព patch របស់ repository នេះទេ។",
    },
    "update_available": {
        "en": "Upstream added {n} newer YouTube version(s): {versions}. Sync the patch sources before patching with them.",
        "km": "Upstream បានបន្ថែមកំណែ YouTube ថ្មីចំនួន {n}: {versions}។ សូមធ្វើបច្ចុប្បន្នភាពប្រភព patch មុនប្រើ។",
    },
    "no_update": {
        "en": "This repository already tracks every YouTube version supported upstream.",
        "km": "Repository នេះមានគ្រប់កំណែ YouTube ដែល upstream គាំទ្រហើយ។",
    },
}


def render(code: str, lang: str = "en", **params) -> str:
    """Render a message template, falling back to English for unknown codes."""
    entry = MESSAGES.get(code)
    if entry is None:
        return code
    template = entry.get(lang, entry["en"])
    try:
        return template.format(**params)
    except (KeyError, IndexError):
        return template


def reason(code: str, **params) -> dict:
    """Return a reason object containing both languages and its parameters."""
    return {
        "code": code,
        "params": params,
        "en": render(code, "en", **params),
        "km": render(code, "km", **params),
    }
