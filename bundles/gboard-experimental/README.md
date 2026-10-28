# Gboard Direct Translate — fork សាកល្បង

នេះជា **fork សាកល្បង** ពី [Gboard-patches v4.0.0 របស់ jasonwu1994](https://github.com/jasonwu1994/Gboard-patches) មិនមែន bundle ដើម ឬ release ថ្មីទេ។ មុខងារ upstream 43 ត្រូវរក្សាទុក ហើយមាន patch បន្ថែមមួយឈ្មោះ **Direct Google Translate (experimental)** ដែលត្រូវជ្រើសដោយខ្លួនឯង។ Source, អាជ្ញាបណ្ណ និងកម្រិតបច្ចេកទេស៖ [`tools/gboard-translate`](../../tools/gboard-translate/README.md)។

**កុំប្រើ fork `4.0.0-direct-translate-dev.1`**៖ ការត្រួតពិនិត្យបន្ថែមបានរកឃើញការចូលប្រើ private field ខុសពី class មួយទៀត។ វាត្រូវបានដកចេញ ហើយ `dev.2` ត្រូវឆ្លងកាត់ការសាកល្បងឡើងវិញមុនប្រើ។

## ការប្រើប្រាស់ បើ CI បានបង្កើតឯកសារ `.mpp` រួច

1. ទាញយក `gboard-direct-translate-experimental.mpp` ពីថតនេះ ហើយក្នុង Morphe Manager ជ្រើស **Sources → Add patch source → Local**។ ដើម្បីជៀសវាង patches ស្ទួន កុំបើក Gboard source ដើម និង fork នេះជាមួយគ្នា។
2. ជ្រើស APK Gboard ដើម `com.google.android.inputmethod.latin` កំណែ `18.5.4.993608717-release-arm64-v8a` / code `176049702`។ ជ្រើស **Direct Google Translate (experimental)** ក្នុងបញ្ជី។ វា **មិនបើកស្វ័យប្រវត្តិ** ទេ។ ជ្រើស ឬដក upstream patches ផ្សេងៗតាមតម្រូវការ។
3. សាក Translate UI ដើមដោយប្រើឃ្លាដែលមិនរសើប ជ្រើស English → Khmer, Khmer → English និង Auto → Khmer។ ពិនិត្យផងដែរពេលប្ដូរអត្ថបទលឿន បិទ keyboard ឬគ្មានអ៊ីនធឺណិត។
4. កុំប្រើទិន្នន័យរសើបសម្រាប់ការសាកល្បងដំបូង ហើយរក្សា keyboard ដែលដំណើរការមួយផ្សេងទៀតជាបម្រុង។

**ឯកជនភាព និងដែនកំណត់៖** អត្ថបទដែលបញ្ចូលក្នុង Translate ត្រូវផ្ញើតាម HTTPS POST ទៅ Google ដោយប្រើ endpoint `gtx` ក្រៅផ្លូវការ ដែលអាច rate-limit ឬឈប់ដំណើរការ។ Fork នេះអាចជំនួសការបកប្រែ offline/system សម្រាប់ Translate UI ដោយការបកប្រែ online។ Request ដែលបានផ្ញើហើយមិនអាចដកត្រឡប់បានទេ។ អានព័ត៌មានលម្អិតក្នុង source README ខាងលើ។

**ការដំឡើង៖** បើបិទ Package Rename ដូចការកំណត់ដែលអ្នកបានរាយការណ៍ APK ដែល Morphe ចុះហត្ថលេខាថ្មីមិនអាច update ឬដំឡើងក្បែរ Gboard ផ្លូវការដែលមាន package ដូចគ្នា និងហត្ថលេខាខុសគ្នាបានទេ។ សូមកុំលុប keyboard ដែលកំពុងប្រើដោយគ្មាន backup។ Package Rename ជាជម្រើសបន្ថែមសម្រាប់ការដំឡើងក្បែរ app ដើម ប៉ុន្តែអាចមានផលប៉ះពាល់ផ្សេង ហើយមិនមែនជាការបញ្ជាក់ថា Translate ដំណើរការទេ។

កំណត់ត្រា `validation.json` (បើ CI បានបង្កើត) បែងចែកការសាកល្បងលើ fixture របស់ភាគីទីបីពី APK ដើម និងការសាកល្បងលើទូរស័ព្ទ។ ការបង្កើត ឬ patch fixture ជោគជ័យ **មិនធានា** ថាការបកប្រែដំណើរការលើឧបករណ៍របស់អ្នកទេ។ Bundle upstream និង [Release Gboard-v4.0.0](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/tag/Gboard-v4.0.0) មិនត្រូវបានជំនួស។
