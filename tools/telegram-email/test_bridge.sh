#!/usr/bin/env bash
# Compile the real extension against minimal test-only Android/Telegram stubs.
# Synthetic data only; this does not call Telegram or test an Android device.
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
find "$root/tools/telegram-email/test-src" -name '*.java' -print | sort > "$work/sources.txt"
printf '%s\n' "$root/extras/telegram-email-experiment/extensions/extension/src/main/java/app/template/extension/telegram/EmailAlternative.java" >> "$work/sources.txt"
if command -v javac >/dev/null; then
  javac -encoding UTF-8 -d "$work/classes" @"$work/sources.txt"
elif [[ -n "${ECJ_JAR:-}" ]]; then
  "${JAVA:-java}" -cp "$ECJ_JAR" org.eclipse.jdt.internal.compiler.batch.Main \
    -17 -encoding UTF-8 -d "$work/classes" @"$work/sources.txt"
else
  echo 'A JDK or ECJ_JAR plus JAVA is required' >&2
  exit 1
fi
"${JAVA:-java}" -ea -cp "$work/classes" EmailAlternativeTest
