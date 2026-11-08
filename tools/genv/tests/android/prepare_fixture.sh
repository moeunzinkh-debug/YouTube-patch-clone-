#!/usr/bin/env bash
# Create and patch a synthetic, counter-only PairIP-shaped fixture. This script
# contains no GenV APK or application code and never publishes an APK.
set -euo pipefail
work="${1:?temporary work directory required}"
bundle="${2:?source-matched MPP required}"
: "${ANDROID_HOME:?Android SDK required}"
: "${GH_TOKEN:?GitHub token required}"
mkdir -p "$work"/{tools,stubs,classes,dex,smali,smali-bad,deps}
tools="$(find "$ANDROID_HOME/build-tools" -mindepth 1 -maxdepth 1 -type d | sort -V | tail -1)"
platform="$(find "$ANDROID_HOME/platforms" -name android.jar | sort -V | tail -1)"
test -x "$tools/aapt2" && test -x "$tools/d8" && test -x "$tools/apksigner" && test -f "$platform"
base=tools/genv/tests/android

cat > "$work/smali-pom.xml" <<'XML'
<project xmlns="http://maven.apache.org/POM/4.0.0"><modelVersion>4.0.0</modelVersion><groupId>test</groupId><artifactId>genv-fixture</artifactId><version>1</version><dependencies><dependency><groupId>org.smali</groupId><artifactId>smali</artifactId><version>2.3.4</version></dependency></dependencies></project>
XML
mvn -q -f "$work/smali-pom.xml" dependency:copy-dependencies -DoutputDirectory="$work/deps"
javac -encoding UTF-8 -source 8 -target 8 -d "$work/stubs" "$base/stubs/com/pairip/licensecheck/LicenseClient.java"
javac -encoding UTF-8 -source 8 -target 8 -cp "$platform:$work/stubs" -d "$work/classes" "$base/src/test/genv/MainActivity.java"
mapfile -t java_classes < <(find "$work/classes" -name '*.class' | sort)
"$tools/d8" --min-api 24 --lib "$platform" --classpath "$work/stubs" --output "$work/dex" "${java_classes[@]}"
java -cp "$work/deps/*" org.jf.smali.Main assemble "$base/smali" -o "$work/smali/classes2.dex"

make_apk() {
    local manifest="$1" second_dex="$2" output="$3"
    "$tools/aapt2" link -I "$platform" --manifest "$manifest" -o "$output"
    (cd "$work/dex" && zip -q -j "$output" classes.dex)
    zip -q -j "$output" "$second_dex"
}
make_apk "$base/AndroidManifest.xml" "$work/smali/classes2.dex" "$work/fixture-unsigned.apk"

# Two incompatible inputs must be rejected by the patch itself, including a
# code change that still has the same method length, package and version.
sed 's/android:versionCode="163"/android:versionCode="164"/' "$base/AndroidManifest.xml" > "$work/wrong-version.xml"
make_apk "$work/wrong-version.xml" "$work/smali/classes2.dex" "$work/wrong-version.apk"
cp -R "$base/smali/." "$work/smali-bad/"
sed -i 's/if-eqz v0, :fresh_b/if-nez v0, :fresh_b/' "$work/smali-bad/com/pairip/licensecheck/LicenseClient.smali"
java -cp "$work/deps/*" org.jf.smali.Main assemble "$work/smali-bad" -o "$work/smali-bad/classes2.dex"
make_apk "$base/AndroidManifest.xml" "$work/smali-bad/classes2.dex" "$work/wrong-shape.apk"

gh release download v1.20.0-dev.1 --repo MorpheApp/morphe-desktop --pattern morphe-desktop-1.20.0-dev.1-all.jar --dir "$work/tools"
cli="$work/tools/morphe-desktop-1.20.0-dev.1-all.jar"
echo '20c2cf951373f4e47092a7c9312519ecfd4b2826ddc114b134e0ad503af53fdb  '"$cli" | sha256sum --check
run_patch() {
    java -Xmx3g -jar "$cli" patch "$1" --patches "$bundle" --exclusive -e 'Remove license check' \
        --bytecode-mode FULL --unsigned --result-file "$2" --out "$3"
}
run_patch "$work/fixture-unsigned.apk" "$work/result.json" "$work/patched-unsigned.apk" > "$work/patch.log" 2>&1
python3 - "$work/result.json" <<'PY'
import json,sys
r=json.load(open(sys.argv[1]))
assert r['success'] and not r['failedPatches'] and r['appliedPatches']==['Remove license check'], r
PY
if run_patch "$work/wrong-version.apk" "$work/wrong-version-result.json" "$work/wrong-version-output.apk" > "$work/wrong-version.log" 2>&1; then
    echo 'Wrong version code was accepted' >&2; exit 1
fi
grep -q 'supports only the reviewed GenV package, version 3.7.2 and build 163' "$work/wrong-version.log"
if run_patch "$work/wrong-shape.apk" "$work/wrong-shape-result.json" "$work/wrong-shape-output.apk" > "$work/wrong-shape.log" 2>&1; then
    echo 'Changed instruction shape was accepted' >&2; exit 1
fi
grep -q 'GenV initializeLicenseCheck implementation changed or is already patched' "$work/wrong-shape.log"

run_microg() {
    java -Xmx3g -jar "$cli" patch "$1" --patches "$bundle" --exclusive \
        -e 'Morphe MicroG Google sign-in support (experimental)' --bytecode-mode FULL --unsigned \
        --result-file "$2" --out "$3"
}
if run_microg "$work/wrong-version.apk" "$work/microg-wrong-version-result.json" "$work/microg-wrong-version-output.apk" > "$work/microg-wrong-version.log" 2>&1; then
    echo 'MicroG selector accepted the wrong version code' >&2; exit 1
fi
grep -q 'requires the reviewed GenV package, version 3.7.2 and build 163' "$work/microg-wrong-version.log"
if run_microg "$work/fixture-unsigned.apk" "$work/microg-wrong-shape-result.json" "$work/microg-wrong-shape-output.apk" > "$work/microg-wrong-shape.log" 2>&1; then
    echo 'MicroG selector accepted unrelated bytecode' >&2; exit 1
fi
grep -q 'GenV input signing certificate is absent or does not match the reviewed base APK' "$work/microg-wrong-shape.log"

keytool -genkeypair -noprompt -keystore "$work/disposable.jks" -storepass android -keypass android \
    -alias disposable -dname 'CN=Disposable synthetic PairIP test' -keyalg RSA -keysize 2048 -validity 2 >/dev/null 2>&1
for name in fixture patched; do
    "$tools/zipalign" -f -P 16 4 "$work/$name-unsigned.apk" "$work/$name-aligned.apk"
    "$tools/apksigner" sign --min-sdk-version 24 --ks "$work/disposable.jks" --ks-pass pass:android \
        --key-pass pass:android --out "$work/$name.apk" "$work/$name-aligned.apk"
    "$tools/apksigner" verify --min-sdk-version 24 "$work/$name.apk"
done
echo 'Synthetic fixture ready; mismatched version and bytecode correctly rejected.'
