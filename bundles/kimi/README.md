# Kimi AI — experimental Morphe patch

នេះជា **patch bundle ដាច់ដោយឡែក** សម្រាប់ Morphe Manager មិនមែន APK សម្រាប់ដំឡើងដោយផ្ទាល់ទេ ហើយមិនប្ដូរ YouTube, Gboard, SimSimi ឬ Telegram bundles។ Local source មិន update ដោយស្វ័យប្រវត្តិ។

## Patch list

<details>
<summary>🌙 Kimi AI • 1 patch</summary>

| ឈ្មោះក្នុង Manager | ជម្រើសដើម | អ្វីដែលធ្វើ |
|---|---|---|
| `Remove license check` | បើក | ដាក់ `return` នៅដើម `LicenseClient.checkLicense(Context)` និង `initializeLicenseCheck()` ដើម្បីមិនចាប់ផ្ដើម PairIP Play license check ដែលបានពិនិត្យ **ក្នុង client**។ មិនក្លែងលទ្ធផលអាជ្ញាបណ្ណជោគជ័យ និងមិនបង្កើតសិទ្ធិប្រើប្រាស់ ឬ subscription នៅ server ទេ។ |

</details>

Patch កំណត់គោលដៅតែ package **`com.moonshot.kimichat`**, version **3.1.5**, version code **381**។ វាពិនិត្យ build និងរចនាសម្ព័ន្ធកូដសំខាន់ៗមុនកែ; APK version ឬ code ផ្សេងអាចមិន match។ វាជា **experimental**: មិនទាន់បញ្ជាក់ថាការបើក app, login ឬការឆែកផ្សេងនៅ runtime/server ដំណើរការឬទេ។

## ការពិនិត្យ Kimi Release ដែលអ្នកផ្ដល់

[Release `Kimi`](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/tag/Kimi) មាន `Kimi.v.3.1.5.b.381.minSDK26.MultiPatch.apks`, SHA-256 `7000c991b9e745ccd1d1ecffaff71c2295094cb4a7fce213d3ce1d3310050304`។ វាជាឯកសារ split៖ `base.apk`, `split_config.arm64_v8a.apk` និង `split_config.xxhdpi.apk`; package និង version code ស្របគ្នា។ `base.apk` រាយ minSdk 26 (Android 8.0+) និង targetSdk 36។ Archive នេះមានតែ arm64 ABI; ត្រូវមានឧបករណ៍ arm64 ដែលត្រូវគ្នាសម្រាប់ដំណើរការជាក់ស្ដែង។ [លទ្ធផលពិនិត្យ release និង hash របស់ splits](release-inspection.json)។

**ការព្រមានសំខាន់៖** APK ទាំងបីមាន signature ត្រឹមត្រូវ និងដូចគ្នា ប៉ុន្តែជា **Android test key សាធារណៈ** (certificate SHA-256 `a40da80a59d170caa950cf15c18c454d47a39b26989d8b640ecd745ba71bf5dc`) មិនមែនភស្តុតាងថា Moonshot បានចុះហត្ថលេខាទេ។ វាត្រូវនឹង [AOSP test certificate](https://github.com/aosp-mirror/platform_build/blob/master/target/product/security/testkey.x509.pem); [AOSP ព្រមានថា test keys ទាំងនេះសម្រាប់ development ប៉ុណ្ណោះ](https://github.com/aosp-mirror/platform_build/blob/master/target/product/security/README) ហើយ private key អាចរកបានជាសាធារណៈ ដូច្នេះនរណាក៏អាច sign APK ដោយ key នេះបាន។ ប្រភព និងការកែប្រែខាងក្នុងមិនត្រូវបានផ្ទៀងផ្ទាត់; **កុំទុកចិត្ត APK នេះជាមួយពាក្យសម្ងាត់ ឬទិន្នន័យឯកជន**។ ការ patch/sign ឡើងវិញមិនសម្អាតកូដដែលអាចត្រូវបានកែឡើយ។ ប្រើ APK ពីប្រភពដែលអ្នកទុកចិត្ត និងផ្ទៀងផ្ទាត់ហត្ថលេខាអ្នកបង្កើត មុនបញ្ចូលទិន្នន័យ។

## របៀបប្រើ

1. ទាញយក [`bundle.mpp`](bundle.mpp) ទៅទូរស័ព្ទ។ ក្នុង **Morphe Manager → Sources → + → Local**, ជ្រើស `.mpp` ហើយចុច Add។ នេះជាប្រភព local មិនមែន release ថ្មីទេ។
2. នៅ **Sources**, បើក card **Kimi patches (experimental)** ហើយបើក **Experimental app versions** សម្រាប់ source នេះ។ បើចង់ពិនិត្យ patch ជាក់លាក់ សូមបើក **Settings → Expert mode** ផងដែរ។
3. នៅ **Apps → Kimi AI**, ជ្រើស 3.1.5 និង **No, I already have it**, រួចជ្រើសឯកសារ `.apks` ពេញ។ Manager 2.3.0-dev.3 រួម split archive មុន patch; កុំប្រើ `base.apk` តែឯងសម្រាប់ការដំឡើង ព្រោះវាខ្វះ arm64 libraries និង config split។ File picker ខ្លះអាចស្នើសិទ្ធិចូលឯកសារ។ ប្រសិនបើ Manager ព្រមានពី version ឬ signature សូមពិនិត្យការព្រមាន មិនគួរបន្តប្រសិនបើអ្នកមិនទុកចិត្ត APK។
4. ក្នុង patch list ពិនិត្យថា **Remove license check** ត្រូវបានជ្រើស រួចចុច **Patch** និងរក្សាទុក/ដំឡើងលទ្ធផលតាម Manager។
5. APK ដែល Manager ចុះហត្ថលេខាថ្មីអាចមិនអាច update ពី app ដែលមាន key ខុសគ្នា។ ប្រសិនបើត្រូវលុប app ចាស់ សូម **បម្រុងទុកទិន្នន័យជាមុន** ព្រោះការលុបអាចលុបទិន្នន័យក្នុងឧបករណ៍។

## លទ្ធផល និងដែនកំណត់

- [Actions 40981249799](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/40981249799) build `.mpp` ឯករាជ្យ និងផ្ទៀងផ្ទាត់ថា **Morphe Desktop 1.20.0-dev.1** មើលឃើញ patch មួយសម្រាប់ version នេះ។ Desktop បានអនុវត្ត patch លើ `base.apk` ក្នុង archive ដែលមាន hash ខាងលើ។
- ការប្រៀបធៀប DEX មុន/ក្រោយបានឃើញ `return-void` នៅចំណុច PairIP ទាំងពីរ; `Application.attachBaseContext`, provider call site និង Tencent license method ដែលបានត្រួតពិនិត្យនៅដដែល។ លទ្ធផលលម្អិត៖ [validation.json](validation.json) និង [patch-validation.json](patch-validation.json)។
- [Actions 40984792665](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/40984792665) បាននាំចូល `.mpp` ក្នុង **Morphe Manager 2.3.0-dev.3** លើ Android 15 x86_64 emulator, បើក Experimental app versions និងប្រើ `.apks` ពេញ។ Manager បានរួម splits, ជ្រើស patch នេះតែមួយ និងបង្ហាញថា patch បានជោគជ័យ។ APK ដែល Manager រក្សាទុកបានផ្ទៀងផ្ទាត់ signature និង DEX; មាន arm64 libraries 21។ មើល [manager-smoke.json](manager-smoke.json)។
- APK សម្រាប់ arm64 **មិនបានដំឡើង ឬបើកលើ emulator x86_64 នេះទេ**។ មិនបានផ្ទៀងផ្ទាត់ runtime លើទូរសព្ទ, login, server attestation ឬ paid features; ការសាក patch ជោគជ័យមិនធានាថា app នឹងដំណើរការទេ។

Bundle SHA-256: `829ba0f34c76130ead69483f3da7c11ec3c3df7402601843a7473be27cf3c145` ([checksum](bundle.mpp.sha256))។ ប្រភព patch នៅ [`tools/kimi/project`](../../tools/kimi/project/) និង workflow build នៅ [`.github/workflows/build-kimi-mpp.yml`](../../.github/workflows/build-kimi-mpp.yml)។
