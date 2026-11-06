# Gboard Khmerlish → ខ្មែរ (experimental)

មុខងារថ្មីសម្រាប់ [Morphe Manager](https://github.com/MorpheApp/morphe-manager) និង Gboard `18.5.4.993608717-release-arm64-v8a` / code `176049702`។ នេះជា fork សាកល្បងដាច់ដោយឡែក៖ រក្សា upstream Gboard patches 43 និង patch `Direct Google Translate (experimental)` មុន។ Release Gboard ដែលមានស្រាប់មិនត្រូវបានជំនួសទេ។

## របៀបប្រើ (បន្ទាប់ពី build `.mpp` ជោគជ័យ)

1. ក្នុង Morphe Manager បន្ថែម `gboard-khmerlish-experimental.mpp` ជា **Sources → Add patch source → Local**។ កុំបើក Gboard source ចាស់ និង fork នេះជាមួយគ្នា ព្រោះ patches ដដែលអាចស្ទួន។
2. ជ្រើស **Khmerlish to Khmer (experimental)** ក្នុងបញ្ជី patches ហើយ patch APK Gboard ដើមកំណែដែលបានរាយខាងលើ។ Patch និង setting នេះមិនបើកជាមុនទេ។
3. ក្នុង Gboard ចូល **Settings → Patches → Khmerlish → ខ្មែរ (experimental)** ហើយបើក switch។ វាយជាអក្សរឡាតាំង រួចចុច **space ឬសញ្ញាខណ្ឌ** ដើម្បីបម្លែងពាក្យដែលស្គាល់៖

   | វាយ | លទ្ធផល |
   | --- | --- |
   | `nv na` | `នៅណា` |
   | `Kampuchea` ឬ `kampu` | `កម្ពុជា` |
   | `nak na` | `អ្នកណា` |
   | `srey sart` | `ស្រីស្អាត` |
   | `Nik o` | `នឹកអូន` |

4. ប្រសិនបើ Gboard English autocorrect កែពាក្យ Latin មុនពេលបម្លែង សាកបិទ autocorrect ក្នុង Gboard។ ដើម្បីសាកដំបូង ប្រើអត្ថបទមិនសម្ងាត់ និងរក្សា keyboard បម្រុងដែលដំណើរការ។

## ឯកជនភាព និងកម្រិត

- ការបម្លែងនេះប្រើវចនានុក្រម **offline** ប្រហែល 24,506 spellings និងមិនផ្ញើអត្ថបទទៅ server។ `Direct Google Translate` ជា patch ផ្សេង៖ បើអ្នកជ្រើសប្រើវា អត្ថបទក្នុង Translate UI ត្រូវផ្ញើទៅ Google ដូចការព្រមានរបស់វា។
- នេះជា exact dictionary lookup មិនមែន AI ឬការយល់បរិបទទេ។ អក្ខរាវិរុទ្ធមិនស្គាល់ និងពាក្យមានច្រើនន័យដែលមិនទាន់កំណត់ទុកជាអក្សរដើម។ ពាក្យអង់គ្លេសខ្លះអាចដូច Khmerlish ដូច្នេះសូមបិទ switch ពេលសរសេរអង់គ្លេស។
- Password, email, URL, លេខ/ទូរស័ព្ទ, no-suggestions និង private/no-personalized-learning fields ត្រូវបានរំលង។ Editors ដែលមិនផ្តល់ cursor ឬមិនគាំទ្រ batch edit ក៏ត្រូវបានរំលង។
- ការសាក algorithm ឬ patch លើ fixture មិនធានា runtime ក្នុង Gboard ពិត ឬគ្រប់ app។ Version ផ្សេងមិនត្រូវបានគាំទ្រដោយ patch ថ្មីនេះទេ។
- APK ដែល Morphe ចុះហត្ថលេខាថ្មីមិនអាច update Gboard ផ្លូវការដែលមាន package ដូចគ្នា និងហត្ថលេខាខុសគ្នាបានទេ។ កុំលុប keyboard តែមួយដោយគ្មាន backup។

ប្រភព dictionary, MIT license, ស្គ្រីបបង្កើត និងការសាកល្បង៖ [`tools/gboard-khmer`](../../tools/gboard-khmer/README.md)។
