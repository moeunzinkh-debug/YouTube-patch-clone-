#!/usr/bin/env bash
# Create disposable synthetic target and instrumentation APKs and a re-signed
# copy of the user-supplied King APK. Never modify or publish the input APK.
set -euo pipefail
work="${1:?private work directory required}"
bundle="${2:?built MPP required}"
mkdir -p "$work"/{tools,fixture-res,fixture-classes,fixture-dex,harness-assets,harness-classes,harness-dex}
: "${ANDROID_HOME:?Android SDK required}"
: "${GH_TOKEN:?GitHub token required}"
tools="$(find "$ANDROID_HOME/build-tools" -mindepth 1 -maxdepth 1 -type d | sort -V | tail -1)"
platform="$(find "$ANDROID_HOME/platforms" -name android.jar | sort -V | tail -1)"
test -x "$tools/aapt2" && test -x "$tools/d8" && test -x "$tools/apksigner" && test -f "$platform"

# Same short-lived key signs the King copy and instrumentation so Android can
# load the test runner into the target process. It is unrelated to output keys.
keytool -genkeypair -noprompt -keystore "$work/disposable.jks" -storepass android -keypass android \
  -alias disposable -dname 'CN=Disposable King emulator harness' -keyalg RSA -keysize 2048 -validity 2 >/dev/null 2>&1
sign() {
  "$tools/apksigner" sign --min-sdk-version 23 --ks "$work/disposable.jks" --ks-pass pass:android \
    --key-pass pass:android --out "$2" "$1"
}

base=tools/king-patcher/tests/android
"$tools/aapt2" compile --dir "$base/fixture/res" -o "$work/fixture-res/compiled.zip"
"$tools/aapt2" link -I "$platform" --manifest "$base/fixture/AndroidManifest.xml" \
  -o "$work/fixture-res/unsigned.apk" "$work/fixture-res/compiled.zip"
mapfile -t fixture_sources < <(find "$base/fixture/src" -name '*.java' | sort)
javac -encoding UTF-8 -source 8 -target 8 -cp "$platform" -d "$work/fixture-classes" "${fixture_sources[@]}"
mapfile -t fixture_classes < <(find "$work/fixture-classes" -name '*.class' | sort)
"$tools/d8" --min-api 23 --lib "$platform" --output "$work/fixture-dex" "${fixture_classes[@]}"
cp "$work/fixture-res/unsigned.apk" "$work/fixture-res/with-dex.apk"
(cd "$work/fixture-dex" && zip -q -j "$work/fixture-res/with-dex.apk" classes.dex)
"$tools/zipalign" -f -P 16 4 "$work/fixture-res/with-dex.apk" "$work/fixture-res/aligned.apk"
sign "$work/fixture-res/aligned.apk" "$work/fixture.apk"
"$tools/apksigner" verify --min-sdk-version 23 "$work/fixture.apk"
cp "$work/fixture.apk" "$work/harness-assets/fixture.apk"

"$tools/aapt2" link -I "$platform" --manifest "$base/harness/AndroidManifest.xml" \
  -A "$work/harness-assets" -o "$work/harness-unsigned.apk"
mapfile -t harness_sources < <(find "$base/harness/src" -name '*.java' | sort)
javac -encoding UTF-8 -source 8 -target 8 -cp "$platform" -d "$work/harness-classes" "${harness_sources[@]}"
mapfile -t harness_classes < <(find "$work/harness-classes" -name '*.class' | sort)
"$tools/d8" --min-api 23 --lib "$platform" --output "$work/harness-dex" "${harness_classes[@]}"
(cd "$work/harness-dex" && zip -q -j "$work/harness-unsigned.apk" classes.dex)
"$tools/zipalign" -f -P 16 4 "$work/harness-unsigned.apk" "$work/harness-aligned.apk"
sign "$work/harness-aligned.apk" "$work/harness.apk"

# The original release asset is read-only; only a private, temporary copy is patched.
gh release download King-Patcher --pattern 'King.Patcher_12.10.10.apk' --dir "$work/tools"
input="$work/tools/King.Patcher_12.10.10.apk"
echo 'e37e25e0fdb2ea92a1592eec7251488d235136e85d5f4e8400f74f8910f40222  '"$input" | sha256sum --check
gh release download v1.20.0-dev.1 --repo MorpheApp/morphe-desktop --pattern morphe-desktop-1.20.0-dev.1-all.jar --dir "$work/tools"
cli="$work/tools/morphe-desktop-1.20.0-dev.1-all.jar"
echo '20c2cf951373f4e47092a7c9312519ecfd4b2826ddc114b134e0ad503af53fdb  '"$cli" | sha256sum --check
java -Xmx4g -jar "$cli" patch "$input" --patches "$bundle" --exclusive \
  -e 'Remove license (new Google Play LVL method)' -e 'Remove insignificant things (manual UI selection)' \
  --bytecode-mode FULL --unsigned --result-file "$work/patch-result.json" --out "$work/king-unsigned.apk" \
  > "$work/patch.log" 2>&1
python3 - "$work/patch-result.json" <<'PY'
import json,sys
result=json.load(open(sys.argv[1]));assert result['success'] and not result['failedPatches'], result
assert {'Remove license (new Google Play LVL method)', 'Remove insignificant things (manual UI selection)'} <= set(result['appliedPatches'])
PY
"$tools/zipalign" -f -P 16 4 "$work/king-unsigned.apk" "$work/king-aligned.apk"
sign "$work/king-aligned.apk" "$work/king.apk"
"$tools/apksigner" verify --min-sdk-version 23 "$work/king.apk"
echo 'Prepared disposable emulator fixtures; no APK is uploaded or published.'
