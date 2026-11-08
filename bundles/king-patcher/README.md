# King-Patcher — Morphe bundle សាកល្បង

Bundle នេះបន្ថែម tools ពីរទៅក្នុងបញ្ជី **Create Modified APK File** របស់ King-Patcher ដើម្បីកែ APK **កម្មវិធីផ្សេង** ដែលអ្នកជ្រើស។ វាជា `.mpp` សម្រាប់ Morphe Manager មិនមែន APK សម្រាប់ដំឡើងផ្ទាល់ទេ។ វាមិនជំនួស bundle របស់ YouTube ឬ app ផ្សេងៗទេ។

[ទាញយក bundle បច្ចុប្បន្នពី repository](bundle.mpp) · [SHA-256](bundle.mpp.sha256) · [លទ្ធផល build](validation.json) · [Manager](manager-smoke.json) · [Android](android-smoke.json)

**កំណែថ្មី `0.1.0-dev.2` មិនទាន់បានបន្ថែមទៅ pre-release ទេ**។ [pre-release](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/tag/King-Patcher) នៅមាន bundle `0.1.0-dev.1` ចាស់ និង APK ដើម។

**គោលដៅតែមួយគត់:** King-Patcher `12.10.10` / version code `1980`, package `ru.jgaiecip.osuojvyxe`; APK ដើមក្នុង [pre-release King-Patcher](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/tag/King-Patcher) មាន SHA-256 `e37e25e0fdb2ea92a1592eec7251488d235136e85d5f4e8400f74f8910f40222`។ កុំប្រើ APK ដែលបាន patch រួចជាធាតុបញ្ចូល។ Tools ទាំងនេះត្រូវការ Android 6 / API 23 ឬខ្ពស់ជាងនេះ។

<details>
<summary>មុខងារ និងដែនកំណត់</summary>

- **Remove license (new Google Play LVL method)** ក្នុង Manager បន្ថែម menu **Remove license check (automatic)** ក្នុង King។ វាស្កេន DEX ក្នុង APK លើទូរស័ព្ទ ហើយពិនិត្យទាំង classic LVL ដែលមិន obfuscate និង PairIP client ដែលមានរចនាសម្ព័ន្ធដូច Kimi 3.1.5 ដែលបានពិនិត្យ។ បើទាំងពីរត្រូវគ្នា វាកែទាំងពីរ; បើមិនស្គាល់ ឬ pattern មិនពេញលេញ វាបញ្ឈប់ដោយមិនបង្កើត APK។ នេះមិនមែនវិធី universal: custom/obfuscated/native checks, Play Integrity, billing និង server-side entitlement មិនត្រូវបានគាំទ្រ ហើយ checks ផ្សេងអាចនៅសល់។ GenV មិនទាន់បានសាក។
- **Remove insignificant things (manual UI selection)** — អ្នកជ្រើស compiled layout និងធាតុមួយៗដោយដៃសម្រាប់ APK នីមួយៗ។ វាកំណត់ធាតុ XML ទាំងនោះជា `GONE` ដើម្បីលាក់ មិនលុបកូដឬធានាថាមុខងារខាងក្រោយបាត់ទេ។ វាមិនកែ Compose, WebView, view បង្កើតដោយកូដ ឬ resource format ដែលមិនស្គាល់ទេ។ Layout variant ផ្សេងត្រូវជ្រើសដោយឡែក។ ឈ្មោះ layout/ID អាចមើលពិបាក ហើយការលាក់ធាតុចាំបាច់អាចធ្វើឱ្យអេក្រង់ប្រើមិនបាន។

</details>

## របៀបប្រើ

1. ទាញយក [`bundle.mpp`](bundle.mpp) កំណែ `0.1.0-dev.2`។ ក្នុង Morphe Manager ចូល **Sources → Add patch source → Local** ហើយជ្រើសឯកសារនេះ។ Local source ចាស់មិន update ស្វ័យប្រវត្តិ; ដក ឬបិទ source ចាស់ដើម្បីកុំច្រឡំ។ បើចាំបាច់ បើក **Experimental app versions** សម្រាប់ source ថ្មី។
2. ជ្រើស APK ដើម King-Patcher ដែលមានកំណែ និង hash ខាងលើ បន្ទាប់មកបើក selectors មួយ ឬទាំងពីរ ហើយ patch។ ពួកវាបិទជាមុន ដូច្នេះត្រូវជ្រើសដោយចេតនា។
3. បន្ទាប់ពីដំឡើង King ដែលបាន patch សូមចូល **Create Modified APK File → Remove license check (automatic)**។ ជ្រើស APK គោលដៅ ហើយចុច **Create modified APK**; King ស្កេនក្នុងឧបករណ៍ និងបង្ហាញថាបានរកឃើញ method អ្វី។ សម្រាប់ UI ត្រូវជ្រើស layout និង elements មុនបង្កើត APK។
4. ពេលរក្សាទុក សូមជ្រើស **ឯកសារថ្មីផ្សេងពី APK ដើម** ហើយទុកច្បាប់ចម្លងដើម និងទិន្នន័យបម្រុង។ File providers ខ្លះអាចបង្ហាញ URI ខុសគ្នាសម្រាប់ឯកសារតែមួយ ដូច្នេះការការពារកុំឱ្យសរសេរជាន់មិនអាចធានាបានគ្រប់ករណីទេ។

## ការប្រុងប្រយ័ត្ន

- គាំទ្រតែ **APK តែមួយ**; មិនគាំទ្រ APK splits, `.apks` ឬ `.xapk`។ Base APK ដែលមិនមានសញ្ញា `split` ក៏អាចនៅតែត្រូវការ splits ផ្សេងទៀត។
- APK King ដែល Morphe ចុះហត្ថលេខាថ្មី ប្រហែលមិនអាច update ជំនាន់ដើមដោយផ្ទាល់។ ការលុប app អាចបាត់ទិន្នន័យ; សូម backup មុន។
- APK គោលដៅត្រូវចុះហត្ថលេខាថ្មីដោយ key ក្នុង Android Keystore របស់ King ដែលបាន patch; វាមិនអាច update app ដែលហត្ថលេខាខុសដោយផ្ទាល់។ Key នេះអាចបាត់បើលុប King ឬ clear data ដូច្នេះការអាប់ដេត APK ដែលបានបង្កើតអាចមិនអាចធ្វើបាន។
- សាកល្បងលើច្បាប់ចម្លង និង app ដែលអ្នកមានសិទ្ធិកែ។ កុំលុប app សំខាន់ ឬគ្មាន backup ដើម្បីសាកល្បង។

## ស្ថានភាពតេស្ត

- សូមមើល [validation](validation.json), [Manager report](manager-smoke.json) និង [Android report](android-smoke.json) សម្រាប់លទ្ធផល និង hash របស់ bundle ដែលបានសាក។
- Bundle នេះនៅសាកល្បង; GenV ពិត, ទូរស័ព្ទពិត និងការចូលតាមម៉ឺនុយ King ពេញលេញមិនទាន់បានសាក។ ការរកឃើញ pattern មិនធានាថា app នឹងដំណើរការ ឬថា license checks ទាំងអស់ត្រូវបានដកចេញទេ។ APK ដើមនៅក្នុង pre-release មិនត្រូវបានកែ ឬជំនួស។
