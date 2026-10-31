# Instant Translate — experimental Morphe bundle

> **មិនទាន់បានសាកដំណើរការលើឧបករណ៍ទេ។** Bundle នេះសម្រាប់ Morphe Manager មិនមែន APK ទេ។ ការសាកលើ APK ចម្លង ការដំឡើង app, ការចូល microG និងការបកប្រែជាក់ស្ដែងមិនបានធ្វើ។ មិនអាចធានាថា premium ឬមុខងារទាំងអស់ដំណើរការបានទេ។
>
> **Release ថ្មី:** `bundle.mpp` និង checksum នៅ [pre-release Instant-translate](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/tag/Instant-translate) ជា `0.4.0-dev.1` ដែលដក Google translation fallback ចេញ។ APK និង split assets នៅក្នុង release មិនបានកែ ឬជំនួស។

## គោលដៅ និង patch list

គោលដៅ `com.spaceship.screen.textcopy`; release ដែលបានពិនិត្យជាឯកសារអានតែប៉ុណ្ណោះគឺ **v7.5.00307 (50350)**, `base.apk` SHA-256 `8cf8c697d2ce04350d2a7fc7d301751e8bb30cf98f298d288ba8b9bfe3f7b1b2`។ Patch សម្រាប់ SEA-LION ក៏រក្សាគោលដៅចាស់ **v7.5.00300 (50342)** ដែរ។ ទាំងអស់ជា experimental និងបិទជាមុន។

<details>
<summary>🌐 Instant Translate • 5 experimental patches</summary>

| ឈ្មោះក្នុង Morphe Manager | អ្វីដែល patch ធ្វើ និងដែនកំណត់ |
|---|---|
| `Translation fallback (SEA-LION, experimental)` | សាកផ្លូវបកប្រែដើមមុន។ បើជ្រើស SEA-LION ដោយខ្លួនឯង វាអាចសាកម្ដងទៀតលើចំណុចលទ្ធផលទទេដែលបានពិនិត្យ។ នៅ 50350 គឺ single-result path មួយ មិនមែនគ្រប់ផ្នែក ឬ batch ទេ។ លំនាំដើម **Original only**។ |
| `Settings Patch (SEA-LION, experimental)` | បន្ថែម **Settings → Settings Patch >** ជាមួយ dropdown **Original only / Sea-Lion Translate Ai** និង Name, URL, Model, Key។ មានអាស្រ័យលើ fallback patch។ UI ពិតមិនទាន់បានសាក។ |
| `Remove license check (experimental)` | សម្រាប់ 50350 បិទចំណុចចូល PairIP license check ពីរខាង client ដែលបានពិនិត្យ។ វាបន្ថយការការពារ license/integrity ហើយមិនបង្កើតការទិញ ឬជំនួសការផ្ទៀងផ្ទាត់ខាង server។ |
| `Unlock premium local gate (experimental)` | សម្រាប់ 50350 ប្ដូរ local entitlement gate ដែលបានពិនិត្យឲ្យត្រឡប់ true។ វាមិនបង្កើត subscription ឬកែ RevenueCat/Google records ទេ; មុខងារដែលអាស្រ័យលើ server អាចនៅតែបិទ។ មិនទាន់បញ្ជាក់មុខងារនីមួយៗ។ |
| `Official microG service visibility (experimental)` | សម្រាប់ 50350 បន្ថែម Android package visibility ចំពោះ `com.google.android.gms`។ វាមិនដំឡើង microG, មិនប្ដូរឈ្មោះសេវា និងមិនធានា Google login ឬ API គ្រប់មុខ។ |

</details>

## SEA-LION និងឯកជនភាព

| Field | Default |
|---|---|
| Name | `Sea-Lion Translate Ai` |
| URL | `https://api.sea-lion.ai/v1/` |
| Model | `aisingapore/Gemma-SEA-LION-v4-27B-IT` |
| Key | ទទេ — បញ្ចូល key ផ្ទាល់លើឧបករណ៍ |

- បើមិនជ្រើស SEA-LION ឬមានតម្លៃចាស់ `google`/តម្លៃមិនស្គាល់ bundle នេះប្រើ **Original only**; វាមិនបញ្ជូន fallback ទៅ Google ឬប្ដូរទៅ SEA-LION ស្ងាត់ៗទេ។ ការដកនេះ **មិនលុប Google services ដែល app ដើមប្រើដោយខ្លួនឯង**។
- បើបើក SEA-LION អត្ថបទបរាជ័យ និង API key ត្រូវផ្ញើទៅ HTTPS host ដែលបានកំណត់។ ប្រើតែ host ដែលអ្នកទុកចិត្ត; មិនបានសាកជាមួយ key ឬ model access ពិតទេ។ Key ត្រូវបានអ៊ិនគ្រីបដោយ Android Keystore និងរក្សាក្រៅ backup; កុំផ្ញើ key ក្នុង chat។ [ឯកសារ SEA-LION](https://docs.sea-lion.ai/guides/inferencing/api)។
- Endpoint ឬ model មិនមាន ការកំណត់ rate-limit និង network failure អាចធ្វើឲ្យ fallback បរាជ័យ។ វាមិនជួសជុល offline model ឬធានាការបកប្រែគ្រប់ផ្នែកទេ។

## microG

ប្រើ [microG GmsCore ផ្លូវការ](https://github.com/microg/GmsCore) ដាច់ដោយឡែក។ សម្រាប់កញ្ចប់ `com.google.android.gms`, ប្រព័ន្ធត្រូវគាំទ្រ signature spoofing ហើយ Play Services ដើមអាចជាន់កញ្ចប់ដូចគ្នា។ ពិនិត្យ self-check ក្នុង microG និងបន្ថែមគណនីតាម microG ដោយខ្លួនឯង; កុំចែករំលែកពាក្យសម្ងាត់ក្នុង chat។ microG មិនអនុវត្ត Google APIs ទាំងអស់ ហើយ sign-in ពិតក្នុង Instant Translate **មិនទាន់បានសាក**។ មើល [microG system requirements](https://github.com/microg/GmsCore/wiki) និង [installation guide](https://github.com/microg/GmsCore/wiki/Installation)។

## ការសាក និងប្រវត្តិ

- [bundle-build.json](bundle-build.json) រាយលទ្ធផល offline unit tests, ការពិនិត្យ `.mpp` និង `list-patches` របស់ Morphe Desktop ប៉ុណ្ណោះ។ វាមិនមែនជាលទ្ធផល patch APK ក្នុង Manager ឬតេស្ត runtime ទេ។
- `0.2.0-dev.1` ចាស់សម្រាប់ 50342 ត្រូវបាន Manager import, patch និង save នៅក្នុងតេស្តមុន; ទិន្នន័យ [manager-smoke.json](manager-smoke.json) និង [patch-validation.json](patch-validation.json) ជារបាយការណ៍ប្រវត្តិ **Google-enabled bundle ចាស់** មិនមែន bundle ថ្មីនេះទេ។
- ក្នុង emulator ការបើក APK ចាស់ដែល Manager patch/sign ធ្លាក់នៅ `bin.edisaputra.protector.LicenseActivity.verifyIntegrity`; control re-sign ដោយមិនកែ DEX/native ក៏ធ្លាក់។ [crash-check.json](crash-check.json) ជាលទ្ធផលចាស់សម្រាប់ 50342 ប៉ុណ្ណោះ។ មិនបានសាកថា 50350 បើកបាន ឬថា patch ថ្មីជួសជុល crash ទេ។
- ការពិនិត្យ release ថ្មីជា read-only static analysis ប៉ុណ្ណោះ; មិនបានកែ, sign, patch, ដំឡើង ឬជំនួស APK នៅ release។ ប្រភព APK និងការចូលគណនីមិនទាន់បញ្ជាក់ថាមានសុវត្ថិភាព; ប្រើតែឯកសារដែលអ្នកទុកចិត្ត។

[Repository bundle.mpp](bundle.mpp) · [SHA-256](bundle.mpp.sha256) · [Source](../../tools/instant-translate/project/) · [Pre-release](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/tag/Instant-translate)
