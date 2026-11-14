#!/usr/bin/env python3
"""Inspect one public BigTree episode with Chrome DevTools Protocol.

The report intentionally strips query values, cookies, headers and response bodies.
Only playback-relevant URL shapes, bridge calls and short JavaScript contexts remain.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit, urlunsplit

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

TARGET = "https://xstree.com/vplay/35835512.html"
MEDIA_RE = re.compile(r"(?:\.m3u8|\.mpd|\.mp4|\.m4v|\.webm|\.mov|\.ts|\.m4s|videoplayback|video|media|play)", re.I)
CONTEXT_RE = re.compile(r"nativePlayerOpen|setMediaInfo|\.m3u8|\.mpd|\.mp4|clearKeys|bbtsKey|ykKey|manifest", re.I)


def safe_url(value: str) -> dict[str, object]:
    try:
        parsed = urlsplit(value)
        return {
            "url": urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", "")),
            "query_keys": sorted({key for key, _ in parse_qsl(parsed.query, keep_blank_values=True)}),
        }
    except Exception:
        return {"url": "<invalid>"}


def sanitize(value):
    if isinstance(value, dict):
        return {str(key): sanitize(item) for key, item in value.items() if str(key).lower() not in {"cookie", "headers", "authorization"}}
    if isinstance(value, list):
        return [sanitize(item) for item in value[:50]]
    if isinstance(value, str):
        if value.startswith(("http://", "https://")):
            return safe_url(value)
        try:
            parsed = json.loads(value)
            if isinstance(parsed, (dict, list)):
                return {"parsed_json": sanitize(parsed)}
        except Exception:
            pass
        return value[:1000]
    return value


def contexts(text: str, limit: int = 40) -> list[str]:
    result = []
    for match in CONTEXT_RE.finditer(text):
        value = re.sub(r"\s+", " ", text[max(0, match.start() - 180):match.end() + 260]).strip()
        # Strip complete URL query values even when embedded in JavaScript.
        value = re.sub(r"https?://[^\s\"'<>]+", lambda found: safe_url(found.group(0))["url"], value)
        if value not in result:
            result.append(value[:700])
        if len(result) >= limit:
            break
    return result


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: inspect_episode.py OUTPUT.json")
    output = Path(sys.argv[1])
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--autoplay-policy=no-user-gesture-required")
    options.add_argument("--window-size=412,915")
    options.add_argument("--lang=zh-CN")
    options.add_argument("--user-agent=Mozilla/5.0 (Linux; Android 15; Pixel 8 Build/AP3A.241105.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/131.0.0.0 Mobile Safari/537.36 BigTree/1.14")
    options.set_capability("goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"})
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(45)
    driver.execute_cdp_cmd("Network.enable", {"maxTotalBufferSize": 100_000_000, "maxResourceBufferSize": 10_000_000})
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": r"""
      window.__bigtreeBridgeCalls=[];
      const bridgeDefaults={
        getData:'', readClipboard:'', takeSharedText:'', getAudioRoute:'{}', listLocalMedia:'{"items":[]}',
        speechAvailable:false, pickMedia:false, getAppInfo:'{"version":"1.14","versionCode":10,"platform":"android"}'
      };
      window.Android=new Proxy({}, {get:function(target,name){
        if(name==='then')return undefined;
        return function(){
          const args=Array.prototype.slice.call(arguments);
          window.__bigtreeBridgeCalls.push({name:String(name),args:args});
          return Object.prototype.hasOwnProperty.call(bridgeDefaults,name)?bridgeDefaults[name]:undefined;
        };
      }});
    """})
    responses: dict[str, dict] = {}
    requests: dict[str, dict] = {}
    script_contexts: list[str] = []
    errors: list[str] = []

    def drain() -> None:
        for entry in driver.get_log("performance"):
            try:
                event = json.loads(entry["message"])["message"]
                method, params = event["method"], event.get("params", {})
                if method == "Network.requestWillBeSent":
                    request = params.get("request", {})
                    url = request.get("url", "")
                    requests[params.get("requestId", url)] = {**safe_url(url), "method": request.get("method"), "type": params.get("type")}
                elif method == "Network.responseReceived":
                    response = params.get("response", {})
                    url = response.get("url", "")
                    request_id = params.get("requestId", url)
                    responses[request_id] = {
                        **safe_url(url), "status": int(response.get("status", 0)),
                        "mime": response.get("mimeType", ""), "type": params.get("type"),
                        "from_service_worker": bool(response.get("fromServiceWorker")),
                    }
                    if params.get("type") == "Script" or "javascript" in response.get("mimeType", ""):
                        try:
                            body = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id}).get("body", "")
                            for value in contexts(body):
                                if value not in script_contexts:
                                    script_contexts.append(value)
                        except Exception as exc:
                            errors.append("script_body_unavailable:" + type(exc).__name__)
            except Exception as exc:
                errors.append("performance_event:" + type(exc).__name__)

    try:
        try:
            driver.get(TARGET)
        except Exception as exc:
            errors.append("navigation:" + type(exc).__name__)
        for round_index in range(6):
            time.sleep(5)
            try:
                driver.execute_script(r"""
                  document.querySelectorAll('video').forEach(function(video){video.muted=true;video.play().catch(function(){});});
                  if(arguments[0]===1){
                    var words=/播放|立即播放|观看|继续|play|watch/i;
                    Array.from(document.querySelectorAll('button,a,[role="button"]')).filter(function(el){return words.test((el.innerText||el.title||el.getAttribute('aria-label')||'').trim());}).slice(0,3).forEach(function(el){try{el.click();}catch(e){}});
                  }
                """, round_index)
            except Exception as exc:
                errors.append("interaction:" + type(exc).__name__)
            drain()
        try:
            bridge_calls = driver.execute_script("return window.__bigtreeBridgeCalls||[]")
            page = driver.execute_script("return {title:document.title,text:(document.body&&document.body.innerText||'').slice(0,5000),html:document.documentElement.outerHTML.slice(0,200000),scripts:Array.from(document.scripts).map(s=>s.src||'<inline>'),frames:Array.from(document.querySelectorAll('iframe,frame')).map(f=>f.src)}")
        except Exception as exc:
            errors.append("page_snapshot:" + type(exc).__name__)
            bridge_calls, page = [], {}
        drain()
        inline_contexts = contexts(str(page.get("html", "")))
        media = []
        for item in list(responses.values()) + list(requests.values()):
            if MEDIA_RE.search(str(item.get("url", ""))) or str(item.get("mime", "")).startswith(("video/", "audio/", "application/vnd.apple.mpegurl", "application/dash+xml")):
                if item not in media:
                    media.append(item)
        report = {
            "target": TARGET,
            "observed_final_url": safe_url(driver.current_url),
            "page_title": page.get("title", ""),
            "page_text": page.get("text", ""),
            "bridge_calls": sanitize(bridge_calls),
            "frames": [safe_url(value) for value in page.get("frames", []) if value],
            "scripts": [safe_url(value) if value != "<inline>" else {"url": value} for value in page.get("scripts", [])],
            "media_and_playback_requests": media,
            "javascript_playback_contexts": (script_contexts + inline_contexts)[:80],
            "network_summary": {"requests": len(requests), "responses": len(responses)},
            "browser_console": [{"level": item.get("level"), "message": item.get("message", "")[:1000]} for item in driver.get_log("browser")[:100]],
            "inspection_errors": sorted(set(errors)),
            "scope": "Headless Chrome/CDP observation with a recording Android bridge. Query values, headers, cookies and response bodies are not retained. Playback and Android-device behavior remain unverified.",
        }
    finally:
        driver.quit()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"bridge_calls": len(report["bridge_calls"]), "media_requests": len(report["media_and_playback_requests"]), "contexts": len(report["javascript_playback_contexts"]), "network": report["network_summary"]}))


if __name__ == "__main__":
    main()
