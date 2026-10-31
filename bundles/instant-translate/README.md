# Instant Translate — experimental Morphe patches

> **មិនទាន់រួចរាល់សម្រាប់ដំឡើងប្រើប្រាស់។** APK ដែលបាន patch/sign ដោយ Morphe Desktop ពីមុន បើកធ្លាក់ក្នុង emulator នៅ `bin.edisaputra.protector.LicenseActivity.verifyIntegrity`។ ការសាក re-sign និង align APK ដើមដោយមិនកែ DEX ឬ native libraries ក៏ជួប stack trace ដូចគ្នា។ Bundle ថ្មី **រក្សា check ដើម**; កូដក្នុង check នេះជា native ហើយមុខងារខាងក្នុងមិនទាន់ដឹងទាំងអស់។ មិនទាន់បញ្ជាក់ថា APK ដែល patch ដោយ bundle ថ្មីអាចបើក ឬបកប្រែបានទេ។

នេះជា bundle `.mpp` ដាច់ដោយឡែកសម្រាប់ **Morphe Manager** មិនមែន APK ហើយមិនកែ YouTube ឬ bundle ផ្សេងៗ។ គោលដៅដែលបានពិនិត្យតែ `com.spaceship.screen.textcopy` **v7.5.00300 (50342)**, Android 10+ (minSdk 29); APK មាន native libraries សម្រាប់ arm64-v8a តែប៉ុណ្ណោះ។ រចនាសម្ព័ន្ធ DEX ត្រូវបានពិនិត្យមុន patch។

## Patch list

<details>
<summary>🌐 Instant Translate • 2 experimental patches (បិទជាមុន)</summary>

| ឈ្មោះក្នុង Morphe Manager | មុខងារ |
|---|---|
| `Translation fallback (Google, experimental)` | សាកការបកប្រែដើមមុន; នៅចំណុចលទ្ធផលទទេ ឬធាតុបរាជ័យដែលបានពិនិត្យ សាក provider ដែលបានជ្រើស។ ជម្រើសដើមគឺ Google; មិនធានាថាចាប់ exception ឬការព្យួរគ្រប់ប្រភេទទេ។ |
| `Settings Patch (SEA-LION, experimental)` | បន្ថែម **Settings → Settings Patch >** និង dropdown **Original only / Google fallback / Sea-Lion Translate Ai**។ បើក patch ទីមួយជាអាស្រ័យ។ Settings មានប្រអប់ Name, URL, Model និង Key។ UI ក្នុង APK ពិតមិនទាន់បានសាកបើក។ |

</details>

**SEA-LION defaults**

| Field | Default |
|---|---|
| Name | `Sea-Lion Translate Ai` |
| URL | `https://api.sea-lion.ai/v1/` |
| Model | `aisingapore/Gemma-SEA-LION-v4-27B-IT` |
| Key | ទទេ — អ្នកបញ្ចូល API key ផ្ទាល់លើឧបករណ៍ |

នៅពេលជ្រើស **Sea-Lion Translate Ai**, Settings ត្រូវសុំការបញ្ជាក់មុនរក្សាទុក។ SEA-LION ជា **fallback** បន្ទាប់ពីផ្លូវដើមបរាជ័យ មិនមែនជំនួសរាល់លទ្ធផលជោគជ័យដើមទេ។ ជ្រើស **Original only** ដើម្បីមិនប្រើ fallback ឬ **Google fallback** ដើម្បីត្រឡប់ទៅ Google។ បើ SEA-LION បរាជ័យ វាមិនប្ដូរទៅ Google ដោយស្វ័យប្រវត្តិទេ។

## API និងឯកជនភាព

- បង្កើត key តាម [SEA-LION API documentation](https://docs.sea-lion.ai/guides/inferencing/api) រួចបញ្ចូលក្នុង app; **កុំផ្ញើ key ក្នុង chat ឬ commit ទៅ repository**។ ឯកសារផ្លូវការបង្ហាញ OpenAI-compatible `POST /v1/chat/completions` និង `Authorization: Bearer …`។ Model ដែលអ្នកស្នើត្រូវបានកំណត់ជាលំនាំដើម ប៉ុន្តែ **មិនទាន់បញ្ជាក់ថាមានសម្រាប់ key របស់អ្នក**; អាចកែ Model ក្នុង Settings បាន។ មិនបានសាក API ពិតដោយ key របស់អ្នកទេ។
- ពេល fallback ត្រូវបានប្រើ អត្ថបទដែលបរាជ័យ (រួមទាំងអត្ថបទលើអេក្រង់) ត្រូវបានផ្ញើទៅ provider ដែលបានជ្រើស។ សម្រាប់ SEA-LION, API key ផ្ញើជា Authorization header ទៅ host ក្នុង URL។ URL ត្រូវជា HTTPS; app បង្ហាញ host សម្រាប់បញ្ជាក់ ហើយមិនបន្ត redirect ដោយស្វ័យប្រវត្តិ។ **ប្ដូរ URL តែទៅ host ដែលអ្នកទុកចិត្ត**។ សូមពិនិត្យ [លក្ខខណ្ឌ និងគោលការណ៍ឯកជនភាព SEA-LION](https://docs.sea-lion.ai/guides/inferencing/api) ហើយកុំផ្ញើអត្ថបទសម្ងាត់បើមិនចង់ចែករំលែក។
- Key ត្រូវបានបាំងក្នុងប្រអប់ និងរក្សាទុកជាទិន្នន័យអ៊ិនគ្រីប AES-GCM ដោយ Android Keystore ក្នុង `noBackupFilesDir`។ Key មិនត្រូវបានដាក់ក្នុង URL ឬ log ដោយ extension ទេ; **Clear key** លុប key ក្នុងឧបករណ៍ និងប្ដូរទៅ Original only ប្រសិនបើ SEA-LION ត្រូវបានជ្រើស។ វាមិនការពារពីឧបករណ៍ដែលត្រូវបាន root ឬ APK ដែលមិនគួរឱ្យទុកចិត្តទេ។
- SEA-LION ត្រូវការ internet; កូតា តម្លៃ និង model អាស្រ័យលើគណនី និង provider។ Extension កំណត់អតិបរមា 9 សំណើក្នុងមួយនាទីក្នុង process មួយ; server អាចបដិសេធមុននេះ ឬឆ្លើយ 429។ AI អាចបកប្រែខុស ឬបង្កើតចម្លើយមិនត្រឹមត្រូវ។ លទ្ធផលដែលត្រូវកាត់ដោយ token limit ត្រូវបានបដិសេធ មិនបង្ហាញជាការបកប្រែពេញលេញទេ។
- Google `client=gtx` ជា endpoint ក្រៅផ្លូវការ មិនប្រើ key; វាអាច rate-limit ប្ដូរ ឬឈប់ដំណើរការ។ សម្រាប់ provider ទាំងពីរ fallback បរាជ័យនឹងរក្សាផ្លូវបរាជ័យដើម។ នេះ **មិនជួសជុល offline model ឬ model ដើម** ហើយមិនទាន់បញ្ជាក់ការគ្របដណ្ដប់គ្រប់ផ្នែក ឧបករណ៍ និងគូភាសា។
- ដែនកំណត់៖ អត្ថបទមួយមិនលើស 8,192 UTF-16 code units; batch ដែលអាចផ្ទៀងផ្ទាត់លំដាប់បានមិនលើស 24 ធាតុ។ មាន timeout និង queue កំណត់។

## APK ដែលបានពិនិត្យ

[Pre-release `Instant-translate`](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/tag/Instant-translate) មាន `Instant.Translate-v7.5.00300-com.spaceship.screen.textcopy.apk`, SHA-256 `f341a1b174bda7b5d1c95cb2fc84da238228a116844069ee962220acaf1e4e4c`។ Signature របស់ APK បានផ្ទៀងផ្ទាត់ (certificate SHA-256 `a3f608b5c58f687d8768c378fea8e2f06426715a36194656beaddd39400ede8d`) ប៉ុន្តែ **មិនបញ្ជាក់ថា signer ជាអ្នកបង្កើតផ្លូវការ** ទេ។ ប្រើតែ APK ដែលអ្នកទុកចិត្ត មុនផ្ដល់សិទ្ធិ overlay/screen capture ឬបញ្ចូល key និងព័ត៌មានឯកជន។

## ការជ្រើសក្នុង Manager (នៅពេលបញ្ហាបើក app ត្រូវបានដោះស្រាយ)

1. Import [`bundle.mpp`](bundle.mpp) ជា **Local source** ក្នុង Morphe Manager; វាមិន update ដោយស្វ័យប្រវត្តិ។ បើក **Experimental app versions** និង **Expert mode**។
2. ជ្រើស `Instant Translate` v7.5.00300 និង APK ដែល hash ត្រូវខាងលើ។ បើក patch ទាំងពីរដោយខ្លួនឯង បន្ទាប់ពីយល់ពីការផ្ញើអត្ថបទ និង key ទៅ provider រួចចុច Patch/Save។
3. ក្នុង app, **Settings → Settings Patch > → Sea-Lion Translate Ai**; ពិនិត្យ Name/URL/Model, បញ្ចូល key ផ្ទាល់ និងបញ្ជាក់ host។ កុំទាន់អនុវត្តរហូតដល់បញ្ហា integrity ខាងលើត្រូវបានដោះស្រាយ។
4. APK ដែល Manager sign ថ្មីប្រហែលមិនអាច update app ចាស់ដែលមាន signing key ខុស។ បើត្រូវលុប app ចាស់ សូមបម្រុងទុកទិន្នន័យជាមុន។

## អ្វីដែលបានសាក

- [Actions 41145411759](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/41145411759)៖ 15 offline unit tests លើ transport, provider routing និង fallback; គ្មាន API key ពិត ឬ live SEA-LION request។
- [Actions 41146254914](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/41146254914)៖ សាក dialog ដាច់ដោយឡែកក្នុង Android emulator ដោយ key ក្លែងក្លាយ; ពិនិត្យ dropdown, defaults, ការរក្សាទុក encrypted និងលុប key និង routing ទៅ provider ក្លែងក្លាយ។ តេស្តនេះ **មិនមែន** ជាការបើក Settings ក្នុង APK ពិត ឬ request ទៅ SEA-LION ទេ។
- [Actions 41147046177](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/41147046177) build bundle, list patch ទាំងពីរ និងប្រើ Morphe Desktop patch APK ដែលបាន pin; [លទ្ធផល DEX](patch-validation.json) បញ្ជាក់ hooks, ការរក្សា register របស់ Settings row និង integrity call ដើម។ Static checks **មិនបញ្ជាក់ runtime** ទេ។
- [Actions 41147402818](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/41147402818) បាន import bundle នេះ, ជ្រើស patch ទាំងពីរ និង patch/save APK ដោយ Morphe Manager 2.3.0-dev.3។ [របាយការណ៍ Manager](manager-smoke.json) ផ្ទៀងផ្ទាត់ DEX, signing និង native libraries ប៉ុន្តែ **មិនបានបើក app ឬសាកបកប្រែ** ទេ។
- APK ដើមបើកលើ Android 15 x86_64 emulator ដែលមាន ARM64 translation។ [ការសាក patched APK មុន](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/41078192479) និង [ការសាក re-sign ដោយមិនកែ DEX/native libraries](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/41079548999) បានជួប `verifyIntegrity` crash។ មូលហេតុដើមនៃ “Translation failed” មិនទាន់បញ្ជាក់។

[Bundle SHA-256](bundle.mpp.sha256) · ប្រភពនៅ [`tools/instant-translate/project`](../../tools/instant-translate/project/)។ Bundle និង checksum ត្រូវបានបន្ថែមទៅ [pre-release `Instant-translate` ដែលមានស្រាប់](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/tag/Instant-translate); មិនបានបង្កើត release ថ្មីទេ។
