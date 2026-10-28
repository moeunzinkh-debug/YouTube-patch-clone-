# Gboard Direct Translate — កំណែសាកល្បង dev.2

**Pre-release សាកល្បង** សម្រាប់ Morphe Manager។ នេះជាប្រភព fork ដាច់ដោយឡែក មិនមែន bundle ដើមរបស់ Gboard-patches v4.0.0 ទេ។ Release នេះមិនជំនួស [Gboard-v4.0.0](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/tag/Gboard-v4.0.0)។

## ទាញយក និងប្រើប្រាស់

1. ទាញយក **`bundle.mpp`** ពី Assets ខាងក្រោម។ ក្នុង Morphe Manager ជ្រើស **Sources → Add patch source → Local** ហើយជ្រើសឯកសារនេះ។ កុំបើក Gboard source ដើម និង fork នេះជាមួយគ្នា ព្រោះ patches នឹងស្ទួន។
2. ជ្រើស APK Gboard package `com.google.android.inputmethod.latin`, version **`18.5.4.993608717-release-arm64-v8a`** / version code **`176049702`** ប៉ុណ្ណោះ។
3. ជ្រើស **Direct Google Translate (experimental)** ដោយខ្លួនឯង៖ patch នេះបិទជាមុន។ Fork រក្សា patches upstream ចំនួន 43 និង default របស់ពួកវា។
4. សាកល្បង Translate UI ដើមជាមួយអត្ថបទមិនរសើប។ រក្សា keyboard មួយផ្សេងទៀតជាបម្រុង។

`bundle.mpp` SHA-256: `e0c1a903435261959bdbac23c70bc18cea9cd55e53b2a735e03abab0f55dcc33` (8,201,400 bytes)។ ឯកសារ `bundle.mpp.sha256` អាចប្រើផ្ទៀងផ្ទាត់ភាពត្រឹមត្រូវបន្ទាប់ពីទាញយក។

## សុវត្ថិភាព និងស្ថានភាពតេស្ត

- Patch ផ្ញើអត្ថបទដែលបញ្ចូលក្នុង Translate UI ទៅ Google តាម HTTPS ដោយប្រើ endpoint `gtx` ក្រៅផ្លូវការ។ វាអាច rate-limit ឬឈប់ដំណើរការ និងអាចជំនួស system/offline Translate សម្រាប់ UI នោះ។ កុំប្រើអត្ថបទរសើបក្នុងការសាកល្បងដំបូង។
- ការបង្កើត, unit tests, សំណើសាកល្បង English↔Khmer និងការអនុវត្ត patch លើ fixture ភាគីទីបីបានឆ្លងកាត់ [CI](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/40696115128)។ Fixture នោះ **មិនមែន APK ដើមរបស់ Google** ទេ។
- [Android emulator smoke](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/40700801310) បានបើក keyboard និងឃើញសារ first-use របស់ Translate ប៉ុន្តែ **មិនទាន់បានបញ្ជាក់លទ្ធផលបកប្រែតាម UI** ទេ។ APK ដើម និងទូរស័ព្ទ/បណ្ដាញរបស់អ្នកមិនទាន់ត្រូវបានសាកល្បង។ ការសាក emulator បន្ទាប់បានបរាជ័យមុន script រត់។
- `dev.1` ត្រូវបានដកចេញដោយសារបញ្ហាចូលប្រើ private field។ `dev.2` ប្រើ accessor នៅក្នុង class ដើម និងបានឆ្លងកាត់ការត្រួតពិនិត្យ DEX បន្ថែម ប៉ុន្តែវានៅតែជាកំណែសាកល្បង។
- ប្រសិនបើ Package Rename បិទ APK ដែល Morphe ចុះហត្ថលេខាថ្មីមិនអាច update ឬដំឡើងក្បែរ Gboard ផ្លូវការដែលមាន package ដូចគ្នា និងហត្ថលេខាខុសគ្នាបានទេ។ កុំលុប keyboard ដែលកំពុងប្រើដោយគ្មានជម្រើសបម្រុង។

## ប្រភព និងអាជ្ញាបណ្ណ

Fork នេះផ្អែកលើ [jasonwu1994/Gboard-patches v4.0.0](https://github.com/jasonwu1994/Gboard-patches/releases/tag/v4.0.0) (GPL-3.0)។ ប្រភព upstream ដែលបាន pin មាននៅ `extras/gboard-patches/` និងការកែប្រែ fork មាននៅ `tools/gboard-translate/` ក្នុង tag របស់ release នេះ។ ឯកសារ `LICENSE` និង `NOTICE` របស់ upstream ត្រូវបានភ្ជាប់ក្នុង Assets ផងដែរ។
