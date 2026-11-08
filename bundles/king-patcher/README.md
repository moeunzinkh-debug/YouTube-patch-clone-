# King-Patcher — Morphe bundle សាកល្បង

Bundle នេះបន្ថែម tools ពីរទៅក្នុងបញ្ជី **Create Modified APK File** របស់ King-Patcher ដើម្បីកែ APK **កម្មវិធីផ្សេង** ដែលអ្នកជ្រើស។ វាជា `.mpp` សម្រាប់ Morphe Manager មិនមែន APK សម្រាប់ដំឡើងផ្ទាល់ទេ។ វាមិនជំនួស bundle របស់ YouTube ឬ app ផ្សេងៗទេ។

[ទាញយក bundle.mpp](bundle.mpp) · [SHA-256](bundle.mpp.sha256) · [លទ្ធផល build](validation.json) · [Manager](manager-smoke.json) · [Android](android-smoke.json)

**គោលដៅតែមួយគត់:** King-Patcher `12.10.10` / version code `1980`, package `ru.jgaiecip.osuojvyxe`; APK ដើមក្នុង [pre-release King-Patcher](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/tag/King-Patcher) មាន SHA-256 `e37e25e0fdb2ea92a1592eec7251488d235136e85d5f4e8400f74f8910f40222`។ កុំប្រើ APK ដែលបាន patch រួចជាធាតុបញ្ចូល។ Tools ទាំងនេះត្រូវការ Android 6 / API 23 ឬខ្ពស់ជាងនេះ។

<details>
<summary>មុខងារ និងដែនកំណត់</summary>

- **Remove license (new Google Play LVL method)** — វិធីថ្មីដាច់ដោយឡែកពីមុខងារ license ដើមរបស់ King។ វាគាំទ្រតែ classic Google Play LVL ដែលមាន `com.android.vending.licensing.LicenseChecker` និង callback ដែលមិនបានប្ដូរឈ្មោះ ហើយត្រូវនឹង ABI ដែលបានកំណត់។ វាមិនគាំទ្រការត្រួតពិនិត្យ custom/obfuscated/native, Play Integrity, billing ឬ server-side license ទេ។ បើរកមិនឃើញ pattern ត្រឹមត្រូវ វាគួរបញ្ឈប់ជំនួសការស្មាន។
- **Remove insignificant things (manual UI selection)** — អ្នកជ្រើស compiled layout និងធាតុមួយៗដោយដៃសម្រាប់ APK នីមួយៗ។ វាកំណត់ធាតុ XML ទាំងនោះជា `GONE` ដើម្បីលាក់ មិនលុបកូដឬធានាថាមុខងារខាងក្រោយបាត់ទេ។ វាមិនកែ Compose, WebView, view បង្កើតដោយកូដ ឬ resource format ដែលមិនស្គាល់ទេ។ Layout variant ផ្សេងត្រូវជ្រើសដោយឡែក។ ឈ្មោះ layout/ID អាចមើលពិបាក ហើយការលាក់ធាតុចាំបាច់អាចធ្វើឱ្យអេក្រង់ប្រើមិនបាន។

</details>

## របៀបប្រើ

1. ក្នុង Morphe Manager ចូល **Sources → Add patch source → Local** ហើយជ្រើស `bundle.mpp` នៃថតនេះ។ បើចាំបាច់ បើក **Experimental app versions** សម្រាប់ source នេះ។
2. ជ្រើស APK ដើម King-Patcher ដែលមានកំណែ និង hash ខាងលើ បន្ទាប់មកបើក selectors មួយ ឬទាំងពីរ ហើយ patch។ ពួកវាបិទជាមុន ដូច្នេះត្រូវជ្រើសដោយចេតនា។
3. បន្ទាប់ពីដំឡើង King ដែលបាន patch សូមបើកបញ្ជី **Create Modified APK File** ហើយជ្រើស tool ថ្មី។ ជ្រើស APK គោលដៅតាម file picker; សម្រាប់ UI ត្រូវជ្រើស layout និង elements មុនបង្កើត APK។
4. ពេលរក្សាទុក សូមជ្រើស **ឯកសារថ្មីផ្សេងពី APK ដើម** ហើយទុកច្បាប់ចម្លងដើម និងទិន្នន័យបម្រុង។ File providers ខ្លះអាចបង្ហាញ URI ខុសគ្នាសម្រាប់ឯកសារតែមួយ ដូច្នេះការការពារកុំឱ្យសរសេរជាន់មិនអាចធានាបានគ្រប់ករណីទេ។

## ការប្រុងប្រយ័ត្ន

- គាំទ្រតែ **APK តែមួយ**; មិនគាំទ្រ APK splits, `.apks` ឬ `.xapk`។ Base APK ដែលមិនមានសញ្ញា `split` ក៏អាចនៅតែត្រូវការ splits ផ្សេងទៀត។
- APK King ដែល Morphe ចុះហត្ថលេខាថ្មី ប្រហែលមិនអាច update ជំនាន់ដើមដោយផ្ទាល់។ ការលុប app អាចបាត់ទិន្នន័យ; សូម backup មុន។
- APK គោលដៅត្រូវចុះហត្ថលេខាថ្មីដោយ key ក្នុង Android Keystore របស់ King ដែលបាន patch; វាមិនអាច update app ដែលហត្ថលេខាខុសដោយផ្ទាល់។ Key នេះអាចបាត់បើលុប King ឬ clear data ដូច្នេះការអាប់ដេត APK ដែលបានបង្កើតអាចមិនអាចធ្វើបាន។
- សាកល្បងលើច្បាប់ចម្លង និង app ដែលអ្នកមានសិទ្ធិកែ។ កុំលុប app សំខាន់ ឬគ្មាន backup ដើម្បីសាកល្បង។

## ស្ថានភាពតេស្ត

- [Morphe Manager 2.3.0-dev.3 លើ Android 15 emulator](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/42476819817) បាន import bundle, ជ្រើស selectors ទាំងពីរ, patch និងរក្សាទុកច្បាប់ចម្លង King ដែលមានហត្ថលេខាត្រឹមត្រូវ។ APK ដែល Manager បង្កើតក្នុងតេស្តនោះមិនបានដំឡើង ឬចែកចាយទេ។
- [Android 15 emulator](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/42476819811) បានសាក King ច្បាប់ចម្លងដែល patch ដោយ Morphe Desktop ជាមួយ APK fixture៖ ជ្រើស input និងរក្សាទុកតាម system file picker, ចុះហត្ថលេខា, ដំឡើងលទ្ធផល, ប្ដូរ LVL denial ទៅ `allow(256)` និងលាក់ UI ពីរដែលបានជ្រើសដោយរក្សាធាតុផ្សេង។ ក៏បានសាក menu renderer និង click listeners ប៉ុន្តែ **មិនទាន់សាកចូលតាមម៉ឺនុយទាំងមូល**។
- Bundle នេះនៅសាកល្បង; APK កម្មវិធីពិត, ទូរស័ព្ទពិត និងកំណែ Android ផ្សេងៗមិនទាន់បានសាក។ APK ដើមនៅក្នុង pre-release មិនត្រូវបានកែ ឬជំនួស។
