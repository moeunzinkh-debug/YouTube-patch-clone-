"""Command line interface for the YouTube version advisor."""

from __future__ import annotations

import argparse
import json
import sys

from . import VERSION
from .catalog import load_catalog, render_markdown, sync_catalog, write_docs
from .devices import DeviceDetectionError, detect_adb, search_devices
from .i18n import LANGS
from .recommend import analyze


def _print_json(payload) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def cmd_update(args: argparse.Namespace) -> int:
    result = sync_catalog(online=not args.offline, write=not args.check, timeout=args.timeout)
    catalog = result["catalog"]
    if args.write_docs:
        path = write_docs(catalog)
        print(f"Docs written to {path}")
    if args.json:
        _print_json(
            {
                "changed": result["changed"],
                "notModified": result["notModified"],
                "written": result["written"],
                "error": result["error"],
                "localVersion": catalog["local"]["patchVersion"],
                "upstreamVersion": catalog["upstream"]["patchVersion"],
                "added": [item["version"] for item in result["added"]],
                "removed": [item["version"] for item in result["removed"]],
                "checkedAt": result.get("checkedAt") or catalog["upstream"].get("checkedAt"),
                "markdown": render_markdown(catalog) if args.include_markdown else None,
            }
        )
        return 0
    print(f"Local patch bundle   : v{catalog['local']['patchVersion']} ({len(catalog['local']['versions'])} YouTube versions)")
    print(f"Upstream patch bundle: v{catalog['upstream']['patchVersion']} ({len(catalog['upstream']['versions'])} YouTube versions)")
    print(f"Upstream checked at  : {result.get('checkedAt') or catalog['upstream'].get('checkedAt', 'never')}")
    print(f"Catalog changed      : {'yes' if result['changed'] else 'no'}"
          + (" (dry run, not written)" if args.check else ""))
    if result["added"]:
        print("New upstream versions: " + ", ".join(item["version"] for item in result["added"]))
    if result["removed"]:
        print("Removed upstream     : " + ", ".join(item["version"] for item in result["removed"]))
    if result["error"]:
        print(f"Sync warning         : {result['error']}", file=sys.stderr)
    return 0


def cmd_versions(args: argparse.Namespace) -> int:
    catalog = load_catalog()
    source = catalog[args.channel]
    if args.json:
        _print_json({"channel": args.channel, "patchVersion": source["patchVersion"], "versions": source["versions"]})
        return 0
    print(f"Channel: {args.channel} | patch bundle v{source['patchVersion']} | checked {source.get('checkedAt', 'never')}")
    print(f"{'YouTube':<12} {'Min Android':<13} {'SDK':<5} {'Status':<13} Patches")
    for item in source["versions"]:
        status = "experimental" if item["experimental"] else "stable"
        print(f"{item['version']:<12} {item['androidMin']:<13} {item['minSdk']:<5} {status:<13} {item['patchCount']}")
    return 0


def cmd_devices(args: argparse.Namespace) -> int:
    devices = search_devices(args.query or "", limit=args.limit)
    if args.json:
        _print_json(devices)
        return 0
    print(f"{'ID':<26} {'Brand':<10} {'Model':<28} {'Android':<9} {'SDK':<4} {'ABI':<12} RAM")
    for device in devices:
        print(
            f"{device['id']:<26} {device['brand']:<10} {device['name'][:27]:<28} "
            f"{device['android']:<9} {device['sdk']:<4} {device['abi'][0]:<12} {device['ramGb']} GB"
        )
    return 0


def _payload_from_args(args: argparse.Namespace) -> dict:
    payload = {
        "deviceId": args.device_id,
        "model": args.model,
        "sdk": args.sdk,
        "android": args.android,
        "abi": args.abi,
        "density": args.density,
        "dpi": args.dpi,
        "ramGb": args.ram,
        "userAgent": args.user_agent,
        "platformVersion": args.platform_version,
    }
    if args.adb:
        try:
            payload.update(detect_adb(args.adb if args.adb != "auto" else None))
            payload["source"] = "adb"
        except DeviceDetectionError as error:
            print(f"ADB detection failed: {error}", file=sys.stderr)
            raise SystemExit(2) from error
    # Keep detected values even when a database model was also supplied.
    if payload.get("android") and not payload.get("sdk"):
        from .devices import sdk_from_android

        payload["sdk"] = sdk_from_android(payload["android"])
    return {key: value for key, value in payload.items() if value not in (None, "")}


def cmd_recommend(args: argparse.Namespace) -> int:
    from .devices import profile_from_payload

    try:
        profile = profile_from_payload(_payload_from_args(args))
    except DeviceDetectionError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    result = analyze(profile, load_catalog(), args.channel)
    if args.json:
        _print_json(result)
        return 0
    lang = args.lang
    device = result["device"]
    best = result["recommendation"]
    print(f"Phone      : {device['name']} ({device['model']}) | Android {device['android']} / SDK {device['sdk']}")
    print(f"CPU / DPI  : {device['primaryAbi']} | {device['density']} | RAM {device['ramGb'] or '?'} GB")
    print(f"Channel    : {args.channel} (patch bundle v{result['patchVersion']})")
    print()
    if best is None:
        print(result["noCompatibleReason"][lang])
        return 1
    status = "EXPERIMENTAL" if best["experimental"] else "STABLE"
    print(f"==> Recommended YouTube {best['version']}  [{status}]  score {best['score']}")
    for item in best["reasons"]:
        print(f"    - {item[lang]}")
    print()
    print("APK guidance:")
    for item in result["apk"]["advice"]:
        print(f"    - {item[lang]}")
    print()
    print(f"All supported versions for this phone ({result['compatibleCount']} compatible):")
    print(f"{'YouTube':<12} {'Status':<14} {'Score':<7} Compatible")
    for option in result["options"]:
        status = "experimental" if option["experimental"] else "stable"
        print(f"{option['version']:<12} {status:<14} {option['score'] if option['compatible'] else '-':<7} {'yes' if option['compatible'] else 'no'}")
    if result["updateAvailable"]:
        print()
        print(result["notes"][1][lang] if len(result["notes"]) > 1 else "")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    from .server import serve

    return serve(
        host=args.host,
        port=args.port,
        refresh_hours=args.refresh_hours,
        startup_refresh=not args.no_startup_refresh,
        online=not args.offline,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="youtube-advisor",
        description="Auto-update supported YouTube versions and find the one that fits a phone model.",
    )
    parser.add_argument("--version", action="version", version=f"youtube-version-advisor {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    update = sub.add_parser("update", help="refresh the version catalog from upstream")
    update.add_argument("--offline", action="store_true", help="rebuild from the local manifest only")
    update.add_argument("--check", action="store_true", help="do not write any file (dry run)")
    update.add_argument("--write-docs", action="store_true", help="also regenerate docs/youtube-versions.md")
    update.add_argument("--include-markdown", action="store_true", help="include rendered markdown in JSON output")
    update.add_argument("--timeout", type=float, default=20, help="network timeout in seconds (default 20)")
    update.add_argument("--json", action="store_true", help="machine-readable output")
    update.set_defaults(handler=cmd_update)

    versions = sub.add_parser("versions", help="list supported YouTube versions")
    versions.add_argument("--channel", choices=("local", "upstream"), default="local")
    versions.add_argument("--json", action="store_true")
    versions.set_defaults(handler=cmd_versions)

    devices = sub.add_parser("devices", help="search the phone-model database")
    devices.add_argument("query", nargs="?", help="brand, name, or model code (e.g. SM-A546B)")
    devices.add_argument("--limit", type=int, default=12)
    devices.add_argument("--json", action="store_true")
    devices.set_defaults(handler=cmd_devices)

    recommend = sub.add_parser("recommend", help="analyze which YouTube version fits a phone")
    recommend.add_argument("--model", help="phone model name or code, e.g. 'Galaxy A54 5G' or 'SM-A546B'")
    recommend.add_argument("--device-id", help="exact device id from the database")
    recommend.add_argument("--sdk", help="Android SDK level (overrides the database)")
    recommend.add_argument("--android", help="Android version, e.g. 13 (converted to SDK)")
    recommend.add_argument("--abi", help="comma-separated CPU ABIs")
    recommend.add_argument("--density", help="screen density bucket, e.g. xxhdpi")
    recommend.add_argument("--dpi", help="screen density in DPI")
    recommend.add_argument("--ram", dest="ram", help="RAM in GB")
    recommend.add_argument("--user-agent", help="parse a phone user agent string")
    recommend.add_argument("--platform-version", help="Android version reported by userAgentData")
    recommend.add_argument("--adb", nargs="?", const="auto", metavar="SERIAL", help="auto-detect from a connected phone")
    recommend.add_argument("--channel", choices=("local", "upstream"), default="local")
    recommend.add_argument("--lang", choices=LANGS, default="en")
    recommend.add_argument("--json", action="store_true")
    recommend.set_defaults(handler=cmd_recommend)

    serve_parser = sub.add_parser("serve", help="start the bilingual web advisor")
    serve_parser.add_argument("--host", default="0.0.0.0")
    serve_parser.add_argument("--port", type=int, default=8000)
    serve_parser.add_argument("--refresh-hours", type=float, default=6, help="automatic refresh interval (0 disables)")
    serve_parser.add_argument("--no-startup-refresh", action="store_true")
    serve_parser.add_argument("--offline", action="store_true", help="never contact GitHub")
    serve_parser.set_defaults(handler=cmd_serve)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.handler(args) or 0)
