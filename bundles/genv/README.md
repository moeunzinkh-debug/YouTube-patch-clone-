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

- គោលដៅតែមួយ៖ `com.ainate.ai.video.generate` **3.7.2**, version code **163**, Android 7.0+ (API 24)។ Selector MicroG ពិនិត្យ package/version, certificate ក្នុង signing block និងទម្រង់ methods/route literals មុនកែ។ វាបដិសេធ APK ដែល certificate ខុស ឬគ្មាន។ ការអាន certificate នេះមិនផ្ទៀងផ្ទាត់ signature គ្រីបតូរបស់ APK ទាំងមូលទេ ហើយក៏មិនមែនជាការផ្ទៀងផ្ទាត់ឯករាជ្យថាឯកសារមកពីអ្នកបង្កើតដែរ។
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

បើ input ជា APK ដែល Manager បាន patch និង sign ឡើងវិញរួច selector MicroG អាចបដិសេធ certificate ខុស។ ជ្រើស APK/split archive **ដើម** ហើយជ្រើស patches ដែលចង់បានទាំងពីរ ក្នុងការចុច Patch តែមួយ។ សារ error របស់ bundle `0.2.0-dev.1` មិនអាចបែងចែកថា certificate បាត់ ឬខុសទេ ដូច្នេះវាមិនបញ្ជាក់ថា input របស់អ្នកត្រូវបាន sign ឡើងវិញជាក់លាក់ទេ។

## ផ្លូវ Google Sign-In ទៅ MicroG RE

ការតាមដាន code ក្នុង base បង្ហាញថា Google Sign-In client ហៅ method ពិនិត្យសេវាដែល selector MicroG បានកែ។ នៅលើផ្លូវ interactive ធម្មតា selector ប្ដូរ action និង package ទៅ MicroG RE; វាមិនមែនជាភស្តុតាងថា guard បានជោគជ័យលើឧបករណ៍របស់អ្នក ឬថា GenV បានទទួល session ទេ។ បើ guard មិនទទួល package, signer ឬ sign-in components វាត្រឡប់ទៅ availability control flow ដើម ដែល routing literals ត្រូវបានប្ដូររួច។

ការសាកបន្ថែមលើ Android emulator API 24, 29 និង 35 ប្រើ **synthetic caller** និង parcel គ្មាន options/គណនី៖ caller ដែល package មិនត្រូវត្រូវបាន MicroG បដិសេធ ហើយ caller ដែលត្រូវបានបញ្ជូនទៅផ្ទាំងបន្ថែមគណនីរបស់ MicroG នៅពេលគ្មានគណនី។ វាប្រើ guard ពី MPP ពិត ប៉ុន្តែមិនបានរត់ GenV ឬសាក account chooser, OAuth, server និង Huawei ពិតទេ។ [របាយការណ៍សង្ខេប](microg-handoff.json)។

<a id="browser-sign-in"></a>
## លទ្ធភាព Google Sign-In តាម browser

ការចូល Google ក្នុង browser មិនធ្វើឱ្យ GenV ចូលគណនីដោយស្វ័យប្រវត្តិទេ៖ app ត្រូវទទួលលទ្ធផលតាម callback ដែល Google អនុញ្ញាត និងបញ្ចូលលទ្ធផលទៅក្នុង login/session ដែល GenV និង server ទទួលស្គាល់។ វិធីដែលសុវត្ថិភាពត្រូវការការផ្គូផ្គង OAuth client/redirect, ការការពារ state និង PKCE តាមប្រភេទ client ព្រមទាំងដំណើរការ token exchange ត្រឹមត្រូវ។ Google [រឹតបន្តឹង custom URI schemes សម្រាប់ Android](https://developers.googleblog.com/improving-user-safety-in-oauth-flows-through-new-oauth-custom-uri-scheme-restrictions/) ដោយសារហានិភ័យកម្មវិធីក្លែងបន្លំ។

ការពិនិត្យ APK **base ប៉ុណ្ណោះ** បានឃើញ Flutter Google Sign-In bridge និង resource `default_web_client_id` ប៉ុន្តែ **មិនឃើញ VIEW + BROWSABLE intent filter** សម្រាប់ browser callback ក្នុង manifest របស់ base នោះទេ។ Resource នេះមិនបញ្ជាក់ថាមាន redirect ដែលបានអនុញ្ញាត ឬថា server ទទួលស្គាល់ login តាម browser ឡើយ។ Native Flutter app (`libapp.so`) និង splits ពេញមិនមានក្នុង base ដូច្នេះមិនអាចសន្និដ្ឋានពីគ្រប់ផ្លូវ login របស់ app បានទេ។ [របាយការណ៍គ្មានគណនី ឬ token](browser-feasibility.json)។

**មិនទាន់មាន browser-login patch ទេ។** ត្រូវស្គាល់ផ្លូវ sign-in/callback ផ្លូវការដែល GenV គាំទ្រ ឬឱ្យម្ចាស់ GenV រៀបចំ OAuth និង callback សមស្របជាមុន; ការបើក URL ទៅ Google ប៉ុណ្ណោះមិនមែនជា login ដែលដំណើរការទេ។ កុំផ្ញើ password, authorization code, token ឬ client secret ដើម្បីស៊ើបអង្កេត។

## ពិនិត្យ username/password ក្នុង APK base

ការពិនិត្យ read-only នៃ base 3.7.2 បានរកឃើញពាក្យ `username` និង `password` ក្នុង DEX ប៉ុន្តែការតាមដាន method និង caller បង្ហាញថាវាស្របនឹង **Flutter text input/autofill configuration** មិនមែនជាភស្តុតាងនៃប្រព័ន្ធចុះឈ្មោះ ឬបង្កើត password របស់ GenV ទេ។ វាមាន keys/hints ដូចជា `autofill`, `hints`, `newPassword` និង `newUsername` ដែលស្របនឹង [source Flutter សាធារណៈ](https://github.com/flutter-team-archive/engine/blob/c97a0deccbc139a133fcb7830fc82d330568e4de/shell/platform/android/io/flutter/embedding/engine/systemchannels/TextInputChannel.java); hint ទាំងនេះមិនបញ្ជាក់ថាមានមុខងារកំណត់ password សម្រាប់គណនីទេ។

ក្នុងផ្នែកដែលបានស្កេន មិនឃើញ labels Firebase Auth ដែលបានកំណត់សម្រាប់ signup, password reset និង account linking ទេ។ ការបាត់ labels មិនបញ្ជាក់ថាមុខងារទាំងនោះមិនមានទេ៖ code អាចត្រូវបានប្ដូរឈ្មោះ ឬនៅក្នុងផ្នែកដែលបាត់។ សញ្ញាពាក្យ `login` ក្នុង Flutter assets ក៏មិនបញ្ជាក់ថាផ្លូវ login នោះអាចប្រើបានដែរ។

Base នេះគ្មាន native library រួមទាំង `libapp.so` ដែលផ្ទុក Flutter app code ហើយត្រូវការ splits ដូច្នេះមិនទាន់អាចបញ្ជាក់ថាមាន signup/reset ឬអាចភ្ជាប់ password ទៅ Google account បានទេ។ មិនបានរត់ app សាកគណនី ទាក់ទង server ឬកែ APK ដើមឡើយ។ [របាយការណ៍សញ្ញា និង method ដោយគ្មានទិន្នន័យគណនី](account-inspection.json)។

## ការសាក និងដែនកំណត់

- Morphe Desktop បានពិនិត្យ bundle និង patch ដាច់ដោយឡែក/រួមគ្នាលើច្បាប់ចម្លង base; DEX strings ផ្សេង និង Binder descriptors មិនត្រូវបានប្ដូរ។ APK ចុះហត្ថលេខាដោយ key ផ្សេងត្រូវបានបដិសេធ។ [License static report](patch-validation.json) · [MicroG static report](microg-static.json)។
- Morphe Manager 2.3.0-dev.3 emulator បាននាំចូល bundle និង patch base **មិនពេញលេញ** ដោយជ្រើសទាំងពីរ; DEX និង manifest លទ្ធផលត្រូវបានពិនិត្យ។ [Manager report](manager-smoke.json)។
- Morphe Manager **2.5.0 / Patcher 2.3.0**, Android 10 emulator x86_64 បាន patch និងរក្សាទុកដោយជ្រើស MicroG ប៉ុណ្ណោះ លើ release base និង archive សាកល្បងដែលមាន **base តែមួយ**; output ត្រូវបានពិនិត្យ ហើយ license selector មិនត្រូវបានអនុវត្ត។ វាមិនមែន split set ពេញ ឬ input របស់អ្នកទេ ហើយមិនបញ្ជាក់មូលហេតុ error របស់អ្នកទេ។ [លទ្ធផល CI](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/42534755374)។
- Android fixtures សាក PairIP counters និង guard ក្នុង extension ពិត ដោយគ្មានគណនី/បណ្ដាញ; guard ត្រូវបានសាកពេលគ្មាន package, package signer ខុស និង Morphe MicroG 7.3.0។ [PairIP report](android-smoke.json) · [API 24 guard](microg-guard-api24.json) · [API 35 guard](microg-guard-api35.json)។ នេះមិនមែន GenV ពិតទេ។
- **មិនទាន់បានសាក full split merge, បើក GenV ពិត, Google account chooser/OAuth, Firebase, server acceptance ឬ Huawei របស់អ្នកទេ។** បើនៅ error អាចមានហេតុពី OAuth package/signature restriction, Firebase/network, app server ឬ attestation; កុំសន្យាថា patch អាចដោះស្រាយទាំងនោះ។

ប្រភព៖ [`tools/genv/project`](../../tools/genv/project/) · [លទ្ធផល និង checksum](validation.json)
