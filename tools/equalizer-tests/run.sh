#!/usr/bin/env bash
# Run the real extension controller against small Android API test doubles.
set -euo pipefail
root="$(cd "$(dirname "$0")/../.." && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
javac -d "$work" $(find "$root/tools/equalizer-tests/src" -name '*.java') \
  "$root/extensions/youtube/src/main/java/app/morphe/extension/youtube/patches/EqualizerPatch.java"
java -cp "$work" EqualizerControllerTest
