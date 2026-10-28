#!/usr/bin/env bash
# Uses Ubuntu's real org.json implementation; Android-only classes have test doubles.
set -euo pipefail
root="$(cd "$(dirname "$0")/../.." && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
json_jar="${JSON_JAR:-/usr/share/java/com.android.json.jar}"
if [ ! -f "$json_jar" ]; then
  echo 'Install libandroid-json-java or set JSON_JAR to a real org.json jar.' >&2
  exit 1
fi
javac -cp "$json_jar" -d "$work" $(find "$root/tools/khmer-tts-tests/src" -name '*.java') \
  "$root/extensions/youtube/src/main/java/app/morphe/extension/youtube/patches/voiceovertranslation/KhmerTtsClient.java"
java -cp "$work:$json_jar" app.morphe.extension.youtube.patches.voiceovertranslation.KhmerTtsClientTest "$@"
