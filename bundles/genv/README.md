# GenV — Morphe patches សាកល្បង

នេះជា bundle `.mpp` ដាច់ដោយឡែកសម្រាប់ **Morphe Manager** មិនមែន APK សម្រាប់ដំឡើងផ្ទាល់ទេ។ Bundle ក្នុង repository ជា **0.2.0-dev.1**; asset `GenV-patches-v0.1.0-dev.1.mpp` ដែលមានស្រាប់នៅ [GenV pre-release](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/tag/GenV) នៅតែជា **license patch ប៉ុណ្ណោះ**។ មិនបានប្ដូរ release ឬ APK ដើមទេ។

<details>
<summary>🎬 GenV • 2 experimental patches</summary>

| ឈ្មោះក្នុង Manager | ជម្រើសដើម | មុខងារ និងដែនកំណត់ |
|---|---|---|
| `Remove license check` | បើក | បញ្ឈប់ PairIP client-side license entry points ពីរដែលបានពិនិត្យ។ វាមិនផ្ដល់ purchases, subscriptions, server entitlement ឬរំលង server/Play Integrity attestation ទេ។ |
| `Morphe MicroG Google sign-in support (experimental)` | បិទ | បញ្ជូន Google Sign-In និងផ្លូវសេវាដែលបានពិនិត្យទៅ `app.revanced.android.gms` របស់ Morphe MicroG-RE ដោយរក្សា package GenV ដដែល។ វាជាការសាកល្បង មិនមែនការធានា login ទេ។ |

</details>

## ភាពឆបគ្នា និងអ្វីដែលបានពិនិត្យ

- គោលដៅតែមួយ៖ `com.ainate.ai.video.generate` **3.7.2**, version code **163**, Android 7.0+ (API 24)។ Selector MicroG ពិនិត្យ package/version, certificate ក្នុង signing block និងទម្រង់ methods/route literals មុនកែ។ វាបដិសេធ APK ដែល certificate ខុស ឬគ្មាន។ ការផ្គូផ្គង certificate នេះមិនមែនជាការផ្ទៀងផ្ទាត់ឯករាជ្យថាឯកសារមកពីអ្នកបង្កើតទេ។
- ពិនិត្យ release base ដែលមាន SHA-256 `f50a9d162a5802ce30ba842c09d08c8c2b2c816dc439eb1b8c0346aa71501d2e` និង APK signer SHA-1 `be4c81d3869d726ea9f0229ab937f2e11ab1ccc7` (មិនមែន source-stamp signer)។ MicroG អាចប្រើ package/ស្នាមហត្ថលេខា GenV ដើមដែលបានពិនិត្យសម្រាប់ OAuth ប៉ុន្តែ Google ឬ server អាចនៅតែបដិសេធ។
- ត្រូវដំឡើង [MorpheApp MicroG-RE](https://github.com/MorpheApp/MicroG-RE) ដោយឡែក។ ការសាកប្រើ signer របស់ release **7.3.0**; certificate ដូចគ្នាក៏បានឃើញនៅ release arm64 **7.2.2**។ Availability guard ត្រួតពិនិត្យ package, signer និង sign-in components; វាមិនទទួលស្គាល់ MicroG build ដែលមាន signer ផ្សេង។ នៅ Android 9+ វាសួរ Package Manager អំពី signing lineage; Android 7–8 ប្រើ signature API ចាស់។ លទ្ធផលនៅតែអាស្រ័យលើ Package Manager និង signature spoofing របស់ឧបករណ៍។
- Patch ប្ដូរតែ strings/action/account/provider ដែលបានពិនិត្យ និង package visibility ក្នុង manifest; មិនប្ដូរ Binder descriptors ឬ package GenV ទេ។ វាមិនបន្ថែម server របស់ patch ឬទទួល password/token ទេ; login ដំណើរការតាម MicroG និង Google។ ការគាំទ្រ Firebase, notifications និងសេវា GMS ផ្សេងៗមិនត្រូវបានធានា។

## សំខាន់៖ APK ក្នុង release មិនទាន់ពេញលេញ

[GenV release](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/tag/GenV) មានតែ `GenV_3.7.2.apk` base ដែលប្រកាសថា **ត្រូវការ splits** ហើយគ្មាន native libraries។ កុំរំពឹងថា base នោះអាចដំណើរការជា app ពេញដោយឯកឯង។ ត្រូវការ base និង splits ទាំងអស់ដែលត្រូវគ្នា (រួម ABI/device configuration) ពីប្រភពទុកចិត្ត មាន package/version និង signer ត្រឹមត្រូវ។ ការរួម splits ពេញមិនទាន់បានសាក; បើ Manager មិនអាចរក certificate ដើមក្រោយ merge patch នឹងបដិសេធជាជាងទាយ។ [ព័ត៌មានពិនិត្យ](release-inspection.json)។

## របៀបប្រើ

1. ទាញយក [`bundle.mpp`](bundle.mpp) និង [checksum](bundle.mpp.sha256) ពី repository/ឯកសារដែលបានផ្ដល់ក្នុង session នេះ។ ក្នុង Manager ចូល **Sources → Add patch source → Local** ហើយជ្រើស bundle។ Local source មិន update ស្វ័យប្រវត្តិ។
2. ជ្រើស **GenV patches (experimental)** ក្នុង Sources រួចបើក **Experimental app versions**។ បើចង់ជ្រើស patch ផ្ទាល់ បើក **Settings → Expert mode** ផង។
3. នៅ **Apps → GenV → No, I already have it**, ជ្រើស APK/split archive ពេញលេញដែលត្រូវនឹងគោលដៅខាងលើ។ ការសាក patch base ដាច់ដោយឡែកមិនបំពេញ splits ដែលបាត់ទេ។
4. បើក **Morphe MicroG Google sign-in support (experimental)**; អាចជ្រើស ឬដក `Remove license check` ដោយឡែក។ ចុច **Patch**។ ប្រើ MicroG ដែលមានគណនីរួច; មិនចាំបាច់លុប MicroG ឬ YouTube ដែលកំពុងដំណើរការ។
5. Manager ចុះហត្ថលេខា APK ឡើងវិញ ដូច្នេះវាអាចមិនអាច update លើ app ដើមដែលមាន key ផ្សេង។ បម្រុងទុកទិន្នន័យមុននឹងពិចារណាលុប app ចាស់ ព្រោះការលុបអាចធ្វើឱ្យបាត់ទិន្នន័យ។

## ការសាក និងដែនកំណត់

- Morphe Desktop បានពិនិត្យ bundle និង patch ដាច់ដោយឡែក/រួមគ្នាលើច្បាប់ចម្លង base; DEX strings ផ្សេង និង Binder descriptors មិនត្រូវបានប្ដូរ។ APK ចុះហត្ថលេខាដោយ key ផ្សេងត្រូវបានបដិសេធ។ [License static report](patch-validation.json) · [MicroG static report](microg-static.json)។
- Morphe Manager emulator បាននាំចូល bundle និង patch base **មិនពេញលេញ** ដោយជ្រើសទាំងពីរ; DEX និង manifest លទ្ធផលត្រូវបានពិនិត្យ។ [Manager report](manager-smoke.json)។
- Android fixtures សាក PairIP counters និង guard ក្នុង extension ពិត ដោយគ្មានគណនី/បណ្ដាញ; guard ត្រូវបានសាកពេលគ្មាន package, package signer ខុស និង Morphe MicroG 7.3.0។ [PairIP report](android-smoke.json) · [API 24 guard](microg-guard-api24.json) · [API 35 guard](microg-guard-api35.json)។ នេះមិនមែន GenV ពិតទេ។
- **មិនទាន់បានសាក full split merge, បើក GenV ពិត, Google account chooser/OAuth, Firebase, server acceptance ឬ Huawei របស់អ្នកទេ។** បើនៅ error អាចមានហេតុពី OAuth package/signature restriction, Firebase/network, app server ឬ attestation; កុំសន្យាថា patch អាចដោះស្រាយទាំងនោះ។

ប្រភព៖ [`tools/genv/project`](../../tools/genv/project/) · [លទ្ធផល និង checksum](validation.json)
