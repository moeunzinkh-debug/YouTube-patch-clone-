# Gboard Khmerlish → ខ្មែរ (experimental)

មុខងារថ្មីសម្រាប់ [Morphe Manager](https://github.com/MorpheApp/morphe-manager) និង Gboard `18.5.4.993608717-release-arm64-v8a` / code `176049702`។ នេះជា fork សាកល្បង version `4.0.6-khmerlish-dev.1` ផ្អែកលើ upstream Gboard patches `v4.0.0`៖ រក្សា upstream patches 43 និង patch `Direct Google Translate (experimental)` មុន។ Pre-release `4.0.5` ចាស់មិនត្រូវបានជំនួសទេ និងមិនទាន់មានការកែសញ្ញាថ្មីនេះ។

[ទាញយក `.mpp` សាកល្បងថ្មី](gboard-khmerlish-experimental.mpp) · [SHA-256](gboard-khmerlish-experimental.mpp.sha256) · [លទ្ធផល build](validation.json) · [ការសាក Android](android-smoke.json) · [Pre-release 4.0.5 ចាស់](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/tag/Gboard-v4.0.5)

## របៀបប្រើ

1. ក្នុង Morphe Manager បន្ថែម `gboard-khmerlish-experimental.mpp` ជា **Sources → Add patch source → Local**។ កុំបើក Gboard source ចាស់ និង fork នេះជាមួយគ្នា ព្រោះ patches ដដែលអាចស្ទួន។
2. ជ្រើស **Khmerlish to Khmer (experimental)** ក្នុងបញ្ជី patches ហើយ patch APK Gboard ដើមកំណែដែលបានរាយខាងលើ។ Patch និង setting សម្រាប់បម្លែងស្វ័យប្រវត្តិមិនបើកជាមុនទេ។
3. ក្នុង toolbar របស់ Gboard ចុចរូបតំណាង **Khmerlish → ខ្មែរ**។ វាយ Khmerlish នៅប្រអប់ក្នុង panel ខាងក្រោម ហើយអត្ថបទខ្មែរនឹងបង្ហាញក្នុងប្រអប់របស់កម្មវិធីខាងលើភ្លាមៗ។ ចុច **✓** ឬ **×** ដើម្បីត្រឡប់ទៅ keyboard ធម្មតា។ Panel ប្រើបានដោយមិនចាំបាច់បើក switch ខាងក្រោម; ប្រសិនបើមិនឃើញ icon សាកមើលម៉ឺនុយ features។
4. ប្រសិនបើចង់បម្លែងពេលវាយលើ keyboard ធម្មតា សូមចូល **Settings → Patches → Khmerlish → ខ្មែរ (experimental)** ហើយបើក switch។ វាយជាអក្សរឡាតាំង រួចចុច **space ឬសញ្ញាខណ្ឌ** ដើម្បីបម្លែងពាក្យដែលស្គាល់៖

   | វាយ | លទ្ធផល |
   | --- | --- |
   | `nv na` | `នៅណា` |
   | `Kampuchea` ឬ `kampu` | `កម្ពុជា` |
   | `nak na` | `អ្នកណា` |
   | `srey sart` | `ស្រីស្អាត` |
   | `Nik o` | `នឹកអូន` |

5. ប្រសិនបើ Gboard English autocorrect កែពាក្យ Latin មុនពេលបម្លែងស្វ័យប្រវត្តិ សាកបិទ autocorrect ក្នុង Gboard។ ដើម្បីសាកដំបូង ប្រើអត្ថបទមិនសម្ងាត់ និងរក្សា keyboard បម្រុងដែលដំណើរការ។

## វចនានុក្រមផ្ទាល់ខ្លួន និងឯកសារពាក្យ

ចូល **Gboard Settings → Patches → Khmerlish → ខ្មែរ (experimental) → Personal Dictionary & Documents**។ ផ្ទាំង **ឯកសារពាក្យ / Word guide** អាចស្វែងរកទាំងអក្សរ Khmerlish និងខ្មែរ។ ចុចរូប **កែ ✎** ខាងចុងពាក្យណាមួយ ដើម្បីកែ Khmerlish ឬអត្ថបទខ្មែរ។ ការកែពាក្យដើមរក្សាទុកជាពាក្យផ្ទាល់ខ្លួន ហើយអាចលុបការកែ ដើម្បីត្រឡប់ទៅដើម។ បើប្តូរ Khmerlish របស់ពាក្យដើម វានឹងបន្ថែមពាក្យផ្ទាល់ខ្លួនថ្មី ដោយរក្សាពាក្យដើមដដែល។ ផ្ទាំង **ផ្ទាល់ខ្លួន / Personal** អាចបន្ថែម កែឈ្មោះ ឬលុប និងនាំចូល/នាំចេញបញ្ជីបាន។ ពាក្យផ្ទាល់ខ្លួនមានអាទិភាពលើវចនានុក្រមដើមសម្រាប់ទាំង automatic និង panel។ វាជាវចនានុក្រមដាច់ដោយឡែក មិនមែន Gboard personal dictionary ទេ។

- Khmerlish អាចជាពាក្យ ឬឃ្លាមានដកឃ្លា និងសញ្ញា ដូចជា `min dg del`, `p'o`, `p_o`, `p-o`, `p+o`។ អាចប្រើលេខ សញ្ញា Unicode និង emoji ផងដែរ (អតិបរមា 64 UTF-16 units; emoji ខ្លះរាប់ជា 2)។ មិនទទួល tab, បន្ទាត់ថ្មី, control characters ឬ whitespace ផ្សេងក្រៅពី space។ Space ស្ទួនត្រូវបានកាត់ឱ្យនៅតែមួយ; តម្លៃត្រូវមានអក្សរខ្មែរ និងមិនលើស 128 តួ។ សម្រាប់ automatic សូមចុច space បន្ទាប់ពី key; panel បង្ហាញភ្លាមៗ។ ឃ្លាត្រូវវាយដោយ space មួយរវាងពាក្យ។
- ក្នុង panel ចុច `?123` ដើម្បីប្រើសញ្ញាទូទៅ រួមទាំង `_ - + '`; ចុច `2/2` ដើម្បីបើកទំព័រសញ្ញាបន្ថែម។ សញ្ញា Unicode ផ្សេងទៀតអាច paste ចូល panel។ អាសយដ្ឋាន និង identifiers ដែលមាន `@`, `/`, `_`, `#` ឬលេខ មិនត្រូវបានបំបែកបម្លែងទេ លុះត្រាតែអ្នកបានរក្សាទុក key ពេញនោះដោយចេតនា។
- នាំចូលតែឯកសារ **UTF-8 `.txt`, `.csv` ឬ `.tsv`** មួយគូក្នុងមួយជួរ ដូចខាងក្រោម រួមទាំងឃ្លាដែលមានដកឃ្លា។ អាចទាញយក និងកែ [ឯកសារគំរូ CSV](khmerlish-personal-example.csv) នេះ។ មិនគាំទ្រ PDF/DOCX ទេ។ ឯកសារមិនត្រឹមត្រូវ ឬ key ស្ទួនត្រូវបានបដិសេធទាំងមូល។ អតិបរមា 5,000 គូ និង 2.5 MB ក្នុងឯកសារ; សរុបក្នុងវចនានុក្រមផ្ទាល់ខ្លួនមិនលើស 5,000 គូ។

  ```csv
  khmerlish,khmer
  soksabay,សុខសប្បាយ
  susdei,សួស្តី
  min dg del,មិនដឹងដែល
  p'o,ប្អូន
  "p,o",ប្អូន
  "#person",មនុស្ស
  ```

  ក្នុង CSV ប្រើ double quote ជុំវិញ key ដែលមាន comma, quote ឬចាប់ផ្ដើមដោយ `#`; សម្រាប់ quote ខាងក្នុង ត្រូវសរសេរពីរដង (`""`)។

- មុននាំចូល វាបង្ហាញចំនួនពាក្យថ្មី/ទំនាស់។ ជម្រើសធម្មតា **Keep existing** រក្សាពាក្យផ្ទាល់ខ្លួនចាស់; ជ្រើស **Replace** ប៉ុណ្ណោះទើបជំនួសទំនាស់។ **Export** បង្កើតអត្ថបទ TSV សម្រាប់ backup ដោយដៃ។ កម្មវិធីជ្រើសឯកសារខ្លះអាចបន្ថែម `.txt` ទៅឈ្មោះ; ឯកសារនោះនៅតែនាំចូលវិញបាន។
- ពាក្យដែលបានរក្សាទុកស្ថិតក្នុង private storage របស់ Gboard លើឧបករណ៍ មិន sync ឬ backup ដោយស្វ័យប្រវត្តិ។ សូម **Export មុន uninstall, clear data ឬប្ដូរ package**។ មិនរក្សាទុកអត្ថបទដែលអ្នកវាយក្នុង app ដោយស្វ័យប្រវត្តិទេ។

## លទ្ធផលសាកល្បង

ប្រវត្តិ៖ bundle `4.0.5` ចាស់ឆ្លងកាត់ [build និង unit tests 39/39](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/42321842707) និង [Android 15 emulator](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/42322277323); លទ្ធផលនោះមិនមែនជាការសាក bundle ថ្មីទេ។ សូមពិនិត្យ [របាយការណ៍ Android](android-smoke.json) និង SHA ឱ្យត្រូវគ្នានឹង bundle សម្រាប់លទ្ធផលថ្មី។ Fixture ជា Gboard ដែលបាន patch រួចពីភាគីទីបី និងចុះហត្ថលេខាថ្មីសម្រាប់តេស្តប៉ុណ្ណោះ — **មិនមែន stock Gboard**។ ការអនុវត្ត patch លើ stock APK, Morphe Manager UI និងទូរស័ព្ទពិតនៅមិនទាន់បានសាក។

## ឯកជនភាព និងកម្រិត

- ការបម្លែងនេះប្រើវចនានុក្រម **offline** ប្រហែល 24,506 spellings និងមិនផ្ញើអត្ថបទទៅ server។ `Direct Google Translate` ជា patch ផ្សេង៖ បើអ្នកជ្រើសប្រើវា អត្ថបទក្នុង Translate UI ត្រូវផ្ញើទៅ Google ដូចការព្រមានរបស់វា។
- នេះជា exact dictionary lookup មិនមែន AI ឬការយល់បរិបទទេ។ អក្ខរាវិរុទ្ធមិនស្គាល់ និងពាក្យមានច្រើនន័យដែលមិនទាន់កំណត់ទុកជាអក្សរដើម។ ពាក្យអង់គ្លេសខ្លះអាចដូច Khmerlish ដូច្នេះសូមបិទ switch ពេលសរសេរអង់គ្លេស។
- Password, email, URL, លេខ/ទូរស័ព្ទ, no-suggestions និង private/no-personalized-learning fields ត្រូវបានរំលង។ Editors ដែលមិនផ្តល់ cursor ឬមិនគាំទ្រ batch edit ក៏ត្រូវបានរំលង។
- Panel មាន keyboard QWERTY និងសញ្ញាជាមូលដ្ឋានផ្ទាល់ខ្លួន; suggestions, voice និងមុខងារផ្សេងៗរបស់ Gboard ប្រើតាម keyboard ធម្មតាបន្ទាប់ពីបិទ panel។ ការកែ cursor ឬជ្រើសអត្ថបទក្នុង app អាចបញ្ឈប់ panel ដើម្បីជៀសវាងលុបអត្ថបទដែលមិនពាក់ព័ន្ធ។
- សូមមើល [របាយការណ៍ Android ចុងក្រោយ](android-smoke.json) សម្រាប់លទ្ធផលពិត។ ការសាក algorithm ឬ patch លើ fixture មិនធានា runtime ក្នុង Gboard ពិត ឬគ្រប់ app។ Version ផ្សេងមិនត្រូវបានគាំទ្រដោយ patch ថ្មីនេះទេ។
- APK ដែល Morphe ចុះហត្ថលេខាថ្មីមិនអាច update Gboard ផ្លូវការដែលមាន package ដូចគ្នា និងហត្ថលេខាខុសគ្នាបានទេ។ កុំលុប keyboard តែមួយដោយគ្មាន backup។

ប្រភព dictionary, MIT license, ស្គ្រីបបង្កើត និងការសាកល្បង៖ [`tools/gboard-khmer`](../../tools/gboard-khmer/README.md)។
