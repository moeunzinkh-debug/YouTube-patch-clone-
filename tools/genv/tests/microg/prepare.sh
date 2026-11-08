#!/usr/bin/env bash
# Build disposable, synthetic probes; the guard DEX is taken from the MPP.
set -euo pipefail
work="${1:?temporary work directory required}"
bundle="${2:?source-matched MPP required}"
: "${ANDROID_HOME:?Android SDK required}"
base=tools/genv/tests/microg
mkdir -p "$work"/{stubs,probe-classes,probe-dex,fake-classes,fake-dex}
tools="$(find "$ANDROID_HOME/build-tools" -mindepth 1 -maxdepth 1 -type d | sort -V | tail -1)"
platform="$(find "$ANDROID_HOME/platforms" -name android.jar | sort -V | tail -1)"
test -x "$tools/aapt2" && test -x "$tools/d8" && test -x "$tools/apksigner" && test -f "$platform"

javac -encoding UTF-8 -source 8 -target 8 -cp "$platform" -d "$work/stubs" "$base/stubs/app/morphe/extension/genv/MicroGGuard.java"
javac -encoding UTF-8 -source 8 -target 8 -cp "$platform:$work/stubs" -d "$work/probe-classes" "$base/src/test/genv/microg/ProbeActivity.java"
mapfile -t probe_classes < <(find "$work/probe-classes" -name '*.class' | sort)
"$tools/d8" --min-api 24 --lib "$platform" --classpath "$work/stubs" --output "$work/probe-dex" "${probe_classes[@]}"
unzip -p "$bundle" extensions/genv.mpe > "$work/probe-dex/classes2.dex"
test -s "$work/probe-dex/classes2.dex"

mapfile -t fake_java < <(find "$base/fake" -name '*.java' | sort)
javac -encoding UTF-8 -source 8 -target 8 -cp "$platform" -d "$work/fake-classes" "${fake_java[@]}"
mapfile -t fake_classes < <(find "$work/fake-classes" -name '*.class' | sort)
"$tools/d8" --min-api 24 --lib "$platform" --output "$work/fake-dex" "${fake_classes[@]}"

"$tools/aapt2" link -I "$platform" --manifest "$base/probe-manifest.xml" -o "$work/probe-unsigned.apk"
(cd "$work/probe-dex" && zip -q -j "$work/probe-unsigned.apk" classes.dex classes2.dex)
"$tools/aapt2" link -I "$platform" --manifest "$base/fake-manifest.xml" -o "$work/fake-unsigned.apk"
(cd "$work/fake-dex" && zip -q -j "$work/fake-unsigned.apk" classes.dex)

keytool -genkeypair -noprompt -keystore "$work/disposable.jks" -storepass android -keypass android \
    -alias disposable -dname 'CN=Disposable offline guard fixture' -keyalg RSA -keysize 2048 -validity 2 >/dev/null 2>&1
for name in probe fake; do
    "$tools/zipalign" -f -P 16 4 "$work/$name-unsigned.apk" "$work/$name-aligned.apk"
    "$tools/apksigner" sign --min-sdk-version 24 --ks "$work/disposable.jks" --ks-pass pass:android \
        --key-pass pass:android --out "$work/$name.apk" "$work/$name-aligned.apk"
    "$tools/apksigner" verify --min-sdk-version 24 "$work/$name.apk"
done
echo 'Synthetic probe and wrong-signer fake ready; guard DEX extracted from the MPP.'
