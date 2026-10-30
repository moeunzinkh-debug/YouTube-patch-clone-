# Instant Translate — experimental Morphe patch

នេះជា **bundle ដាច់ដោយឡែក** សម្រាប់ Morphe Manager មិនមែន APK និងមិនប្ដូរ YouTube ឬ bundle ផ្សេងៗ។ កំណែនេះជា **ការសាកល្បង**៖ មិនទាន់បញ្ជាក់ថាគ្រប់ផ្នែក គ្រប់គូភាសា ឬគ្រប់ model ដំណើរការទេ។

> **កុំទាន់ដំឡើងសម្រាប់ប្រើប្រាស់៖** APK ដែលបាន patch និង sign ថ្មីដោយ Morphe Desktop បើកមិនឡើងក្នុង emulator; stack trace ឈប់នៅ `bin.edisaputra.protector.LicenseActivity.verifyIntegrity`។ ការសាក fallback មិនទាន់ឈានដល់ការបកប្រែទេ។ Manager អាច patch និង Save បាន ប៉ុន្តែ APK ដែល Manager បង្កើត **មិនទាន់សាកបើក**។ ការសាកដោយ re-sign និង align APK ដើម (មិនកែ DEX ឬ native libraries) ក៏ជួប stack trace ដូចគ្នា។ កូដក្នុង `verifyIntegrity` ជា native ដូច្នេះមិនទាន់បញ្ជាក់មុខងារខាងក្នុងទាំងអស់។

## Patch list

<details>
<summary>🌐 Instant Translate • 1 patch (ជ្រើសដោយខ្លួនឯង)</summary>

| ឈ្មោះក្នុង Manager | ជម្រើសដើម | មុខងារ |
|---|---|---|
| `Translation fallback (Google, experimental)` | **បិទ** | រក្សាផ្លូវបកប្រែដើម ហើយព្យាយាមប្រើ Google ជំនួស នៅចំណុចលទ្ធផលទទេ ឬធាតុដែលបរាជ័យដែលបានពិនិត្យ។ វាមិនផ្លាស់ប្ដូរលទ្ធផលដែលជោគជ័យ ហើយមិនធានាថា error ឬការព្យួរគ្រប់ប្រភេទនឹងត្រូវបានចាប់ទេ។ |

</details>

គោលដៅតែ `com.spaceship.screen.textcopy` **v7.5.00300 (50342)**, Android 10+ (minSdk 29)។ បណ្ណាល័យ native ក្នុង APK ដែលបានពិនិត្យមានតែ **arm64-v8a**។ Patch ពិនិត្យរចនាសម្ព័ន្ធ DEX មុនកែ និងបដិសេធប្រសិនបើមិនត្រូវនឹង build ដែលបានពិនិត្យ។

## ឯកជនភាព និងដែនកំណត់

- ពេល fallback ត្រូវបានប្រើ អត្ថបទដែលបរាជ័យ **រួមទាំងអត្ថបទលើអេក្រង់** ត្រូវបានផ្ញើតាម HTTPS ទៅ `translate.googleapis.com`។ អត្ថបទស្ថិតក្នុង POST body មិនមែន URL; extension មិនសរសេរអត្ថបទ ឬ response ក្នុង log ទេ។ Google និង OS/បណ្ដាញនៅតែអាចដំណើរការ ឬកត់ត្រាទិន្នន័យ។ កុំប្រើជាមួយអត្ថបទសម្ងាត់ បើអ្នកមិនចង់ចែករំលែកវា។
- Google endpoint `client=gtx` **មិនមានឯកសារគាំទ្រផ្លូវការ** និងមិនប្រើ API key។ វាត្រូវការ internet អាចឆ្លើយតប 429, ប្ដូរ ឬឈប់ដំណើរការ។ បើ fallback បរាជ័យ វារក្សាផ្លូវបរាជ័យដើម ជំនួសការក្លែងលទ្ធផល។
- នេះ **មិនជួសជុល offline model ឬ online model ដើមនីមួយៗទេ**។ ប្រសិនបើផ្លូវ offline ទៅដល់ចំណុច fallback ដែលបាន patch ការសាកជំនួសនឹងប្រើ internet; បើគ្មាន internet វាមិនអាចផ្ដល់ Google result បាន។ មិនទាន់បញ្ជាក់ថាផ្នែក offline និងគ្រប់ផ្នែកប្រើចំណុច fallback នេះទេ។
- ដែនកំណត់ការសាកជំនួស៖ អត្ថបទមួយមិនលើស 8,192 តួ; batch ដែលអាចត្រួតពិនិត្យលំដាប់បានមិនលើស 24 ធាតុ។ មាន timeout និង queue កំណត់; សំណើដែលមិនត្រូវលក្ខខណ្ឌរក្សាផ្លូវដើម។ ភាសាដែល Google មិនគាំទ្រអាចបរាជ័យ។

## APK ដែលបានពិនិត្យ

[Pre-release `Instant-translate`](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/tag/Instant-translate) មាន `Instant.Translate-v7.5.00300-com.spaceship.screen.textcopy.apk`, SHA-256 `f341a1b174bda7b5d1c95cb2fc84da238228a116844069ee962220acaf1e4e4c`។ APK signature ផ្ទៀងផ្ទាត់ថាឯកសារត្រូវនឹង signer ខ្លួនវា (certificate SHA-256 `a3f608b5c58f687d8768c378fea8e2f06426715a36194656beaddd39400ede8d`) ប៉ុន្តែ **មិនបញ្ជាក់ថាជា APK ផ្លូវការរបស់អ្នកបង្កើត** ទេ។ ត្រូវប្រើ APK ពីប្រភពដែលអ្នកទុកចិត្ត មុនផ្ដល់សិទ្ធិ overlay/screen capture ឬបញ្ចូលទិន្នន័យឯកជន។ ការ patch/sign ថ្មីមិនធ្វើឱ្យប្រភព APK មានសុវត្ថិភាពដោយស្វ័យប្រវត្តិឡើយ។

## របៀបប្រើ

1. ទាញយក [`bundle.mpp`](bundle.mpp) និងពិនិត្យ [SHA-256](bundle.mpp.sha256) ប្រសិនបើចង់។ ក្នុង **Morphe Manager → Sources → + → Local**, ជ្រើស `.mpp` ហើយចុច Add។ នេះជា local source មិន update ដោយស្វ័យប្រវត្តិ។
2. ក្នុង **Sources**, បើក **Instant Translate patches (experimental)** ហើយបើក **Experimental app versions**។ នៅ **Settings**, បើក **Expert mode** ដើម្បីជ្រើស patch ដែលបិទជាមុន។
3. នៅ **Apps → Instant Translate**, ជ្រើស `v7.5.00300`, ចុច **No, I already have it** ហើយជ្រើស APK ពេញពី pre-release ខាងលើ។ ពិនិត្យការព្រមានអំពី version និងប្រភព មុនបន្ត។
4. ក្នុង patch list បើក **Translation fallback (Google, experimental)** ដោយខ្លួនឯង បន្ទាប់ពីយល់ពីការផ្ញើអត្ថបទទៅ Google រួចចុច **Patch** និង Save/Install តាម Manager។
5. APK ដែល Manager sign ថ្មីអាចមិនអាច update ពី app ចាស់ដែលមាន signing key ខុស។ ប្រសិនបើត្រូវលុប app ចាស់ សូមបម្រុងទុកទិន្នន័យជាមុន ព្រោះការលុបអាចលបទិន្នន័យក្នុងឧបករណ៍។

## អ្វីដែលបានសាក

- [Actions 41073349766](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/41073349766) build `.mpp` និងបានប្រើ **Morphe Desktop 1.20.0-dev.1** ជ្រើស patch លើ APK ដែល hash ត្រូវនឹងខាងលើ។ [លទ្ធផល DEX](patch-validation.json) បង្ហាញ hooks បី និងថា native retry/result-combiner ដែលបានពិនិត្យនៅដដែល។
- [Actions 41074061125](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/41074061125) នាំចូល bundle ក្នុង **Morphe Manager 2.3.0-dev.3** លើ Android 15 emulator, បើក experimental versions និងជ្រើស patch ដែលបិទជាមុន។ Manager patch និង Save បានជោគជ័យ; signature, hooks និង arm64 libraries ក្នុង APK លទ្ធផលត្រូវបានពិនិត្យ។ [លទ្ធផល Manager](manager-smoke.json)។ តេស្តនេះមិនបានបើក app ឬបញ្ជាក់ការបកប្រែទេ។
- APK ដើមបានបើកលើ Android 15 x86_64 emulator ដែលមាន `libndk_translation` សម្រាប់ arm64។ [ការសាក patched APK 41078192479](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/41078192479) បង្ហាញ crash នៅ `verifyIntegrity`; [ការសាក re-sign ដោយមិនកែ DEX/native libraries 41079548999](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/41079548999) បង្ហាញ crash ដូចគ្នា។ លទ្ធផលលើ emulator មិនអាចជំនួសការសាកលើទូរសព្ទរបស់អ្នកបានទេ។ មូលហេតុដើមនៃ “Translation failed” មិនទាន់បញ្ជាក់។

Bundle SHA-256: `0fc40a4c52f8b4807a41a8e42f0198f7e3566eb0fed702fc6bfdb11de3589b66`។ ប្រភព patch នៅ [`tools/instant-translate/project`](../../tools/instant-translate/project/) និង workflow build នៅ [`.github/workflows/build-instant-translate-mpp.yml`](../../.github/workflows/build-instant-translate-mpp.yml)។ មិនបានបង្កើត release ថ្មី ឬបន្ថែម bundle ទៅ pre-release ទេ។
