#!/usr/bin/env python3
"""Probe an undocumented Google Translate endpoint using only synthetic text.

This is a diagnostic, not a guarantee that the endpoint is supported by Google
or reachable from a user's device. It deliberately does not accept user text.
"""

import json
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

ENDPOINT = "https://translate.googleapis.com/translate_a/single"
CASES = (
    {"source": "en", "target": "km", "text": "Hello world", "method": "GET"},
    {"source": "km", "target": "en", "text": "សួស្តី", "method": "GET"},
    {"source": "auto", "target": "km", "text": "How are you?", "method": "POST"},
)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        return None


def run_case(opener, sample):
    params = {"client": "gtx", "sl": sample["source"], "tl": sample["target"], "dt": "t"}
    data = None
    if sample["method"] == "POST":
        data = urlencode({"q": sample["text"]}).encode("utf-8")
    else:
        params["q"] = sample["text"]
    request = Request(ENDPOINT + "?" + urlencode(params), data=data,
                      headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"})
    result = {"source": sample["source"], "target": sample["target"], "method": sample["method"], "status": "error"}
    try:
        with opener.open(request, timeout=20) as response:
            result["http_status"] = response.status
            body = response.read(1024 * 1024 + 1)
        if len(body) > 1024 * 1024:
            raise ValueError("Response exceeds one MiB")
        payload = json.loads(body.decode("utf-8"))
        if not isinstance(payload, list) or not payload or not isinstance(payload[0], list):
            raise ValueError("Unexpected JSON response shape")
        pieces = [row[0] for row in payload[0] if isinstance(row, list) and row and isinstance(row[0], str)]
        translated = "".join(pieces).strip()
        if not translated:
            raise ValueError("Empty translation")
        result.update(status="ok", sample_translation=translated)
    except HTTPError as error:
        result["http_status"] = error.code
        result["error"] = "HTTP error"
    except (URLError, ValueError, OSError) as error:
        result["error"] = type(error).__name__
    return result


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: probe_google_translate.py OUTPUT.json")
    opener = build_opener(ProxyHandler({}), NoRedirect())
    results = [run_case(opener, sample) for sample in CASES]
    report = {
        "endpoint": ENDPOINT,
        "client": "gtx",
        "api_status": "undocumented and unsupported; availability and rate limits may change",
        "input": "fixed synthetic test phrases only; no user data",
        "environment": "GitHub Actions runner; not the user's Android device",
        "results": results,
    }
    Path(sys.argv[1]).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
