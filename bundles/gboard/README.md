# Gboard Patches 4.0.0 — bundle ដាច់ដោយឡែក

នេះជាការចម្លង [Gboard-patches v4.0.0](https://github.com/jasonwu1994/Gboard-patches/releases/tag/v4.0.0) របស់ **jasonwu1994** មកដាក់ក្នុងគម្រោងនេះ។ ឯកសារ `.mpp` គឺជាច្បាប់ចម្លងដើម **មិនបានកែប្រែ** មិនមែនជាកូដថ្មី ឬជាផ្នែកនៃ `patch.mpp` របស់ YouTube ទេ។ ការពន្យល់ខាងក្រោម និងបញ្ជីជាភាសាខ្មែរប៉ុណ្ណោះដែលបន្ថែមក្នុង repo នេះ; វាមិនមានន័យថាបានបកប្រែ UI របស់ Gboard ទេ។

## ទាញយក និងប្រើជាមួយ Morphe Manager

1. ទាញយក [`gboard-patches-4.0.0.mpp`](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/download/Gboard-v4.0.0/gboard-patches-4.0.0.mpp) ពី [Release Gboard-v4.0.0](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/tag/Gboard-v4.0.0)។ វាជា patch bundle **មិនមែន APK សម្រាប់ដំឡើងផ្ទាល់**។
2. ក្នុង Morphe Manager ចូល **Sources → Add patch source → Local** ហើយជ្រើសឯកសារ `.mpp` នោះ។ វាជា source ដាច់ដោយឡែកពី YouTube/SimSimi។
3. ជ្រើស APK ដើមដែលមិនទាន់ patch របស់ Gboard សម្រាប់ package `com.google.android.inputmethod.latin` និងកំណែ `18.5.4.993608717-release-arm64-v8a`។ នេះជាកំណែតែមួយដែល metadata របស់ upstream v4.0.0 រាយ; កុំសន្មតថាកំណែ ឬ ABI ផ្សេងត្រូវគ្នា។ ត្រូវមាន APK និង split ដែលត្រូវគ្នា ប្រសិនបើការចែកចាយនោះប្រើ split APK។
4. ពិនិត្យបញ្ជី patches និងជម្រើសមុនចាប់ផ្ដើម។ Upstream កំណត់ patches ទាំង 43 ជា default-selected ប៉ុន្តែនេះមិនមានន័យថាសេវាបណ្ដាញទាំងអស់ដំណើរការដោយស្វ័យប្រវត្តិទេ។ ដកមុខងារដែលមិនចង់ប្រើតាមតម្រូវការ។
5. បន្ទាប់ពី patch រួច ដំឡើងលទ្ធផល និងបើក keyboard នោះក្នុង Android Settings ប្រសិនបើចង់ប្រើ។ រក្សាក្តារចុចផ្សេងមួយដែលដំណើរការទុកជាបម្រុង មុនប្ដូរ keyboard លំនាំដើម។

**ជម្រើស remote source:** ក្នុង **Sources → Add patch source → Remote** អាចបញ្ចូល JSON ដែលបាន pin ទៅ tag នេះ៖

```text
https://raw.githubusercontent.com/moeunzinkh-debug/YouTube-patch-clone-/refs/tags/Gboard-v4.0.0/bundles/gboard/patches-bundle.json
```

URL នេះត្រូវបាន pin ទៅ Release នេះ ដូច្នេះវា **មិនប្ដូរទៅកំណែ Gboard ថ្មីដោយស្វ័យប្រវត្តិ** ទេ។ កុំប្រើ URL repo ដើមដោយគ្មាន path សម្រាប់ Gboard: វាចង្អុលទៅ manifest របស់ YouTube។ បើ Manager មិនអាចបន្ថែម JSON នេះបាន សូមប្រើ **Local** `.mpp` ខាងលើ។

Release របស់ការចម្លងនេះត្រូវបានសម្គាល់ជា **pre-release** ដោយសារគម្រោងនេះមិនទាន់សាកល្បង APK/ឧបករណ៍ និងដើម្បីកុំឲ្យវាក្លាយជាអាប់ដេត stable លំនាំដើមរបស់ YouTube។ **Upstream v4.0.0 ផ្ទាល់ជា stable release**។

## Patches និងសុវត្ថិភាព

- [បញ្ជី patches ទាំង 43 ជាភាសាខ្មែរ](../../README.md#gboard-patches) ស្ថិតនៅក្នុងផ្នែក Gboard ដែលអាចបើក/បិទបានក្នុង README ដើម។ ឈ្មោះ patch រក្សាដូច upstream ដើម្បីងាយស្វែងរកក្នុង Manager។
- **Package Rename** ប្ដូរ package ទៅ `dev.jason.com.google.android.inputmethod.latin` ដើម្បីអាចដំឡើងក្បែរ Gboard ផ្លូវការ; ឈ្មោះ app លំនាំដើមដែល upstream កំណត់គឺ `GboardWu`។ បើដកវាចេញ APK ដែលបានចុះហត្ថលេខាថ្មីអាចមិនអាចដំឡើងជំនួស Gboard ផ្លូវការបាន ដោយសារហត្ថលេខា Android ខុសគ្នា។ កុំលុប keyboard ដើមដោយគ្មានជម្រើសបម្រុង។
- **Add Gboard Signature Bypass** រំលងការពិនិត្យ whitelist ហត្ថលេខាខាងក្នុង Gboard; វាមិនរំលងការពិនិត្យហត្ថលេខាដំឡើងរបស់ Android និងមិនធានា Google services ទេ។
- **FTP Server** អាចចែករំលែកឯកសារតាម LAN និងអាចអនុញ្ញាត anonymous access។ ប្រើតែលើបណ្ដាញដែលទុកចិត្ត កំណត់ពាក្យសម្ងាត់/សិទ្ធិឲ្យសមស្រប និងបិទពេលមិនប្រើ។ **Web Clipboard** ចែករំលែក clipboard តាមបណ្ដាញជាមួយ pairing code; clipboard អាចមានព័ត៌មានរសើប។ កុំសន្មតថា LAN ឬ pairing ធ្វើឲ្យទិន្នន័យមានសុវត្ថិភាពទាំងស្រុង។
- **Swipeable Custom Top Row** អាចដំណើរការ JavaScript; ប្រើតែកូដដែលទុកចិត្ត។ Keyboard អាចទទួលអត្ថបទដែលអ្នកវាយ ដូច្នេះគួរពិនិត្យប្រភព និងមុខងារដែលបើក។ ការផ្ទៀងផ្ទាត់ checksum មិនមែនជាការធ្វើសវនកម្មសុវត្ថិភាពទេ។
- **Frosted Glass** ត្រូវការ Android 12+ និងការគាំទ្រ cross-window blur។ OCR ដែល upstream រាយគាំទ្រ Latin, ចិន, ជប៉ុន, កូរ៉េ និង Devanagari; **មិនបានរាយខ្មែរ**។ មុខងារភាសាខ្មែរ រួមទាំងសំឡេង និង AI មិនទាន់ផ្ទៀងផ្ទាត់នៅទីនេះទេ។

## ប្រភព ការផ្ទៀងផ្ទាត់ និងកម្រិតកំណត់

- Source snapshot៖ [`extras/gboard-patches/`](../../extras/gboard-patches/) ពី tag `v4.0.0`, commit `2eb71854accc7e906d3e4f5495b2a54ed1e2af47`។ ឯកសារ [GPL v3 LICENSE](../../extras/gboard-patches/LICENSE) និង [NOTICE](../../extras/gboard-patches/NOTICE) របស់ upstream ត្រូវបានរក្សាទុក។ ច្បាប់ដើម និងអាជ្ញាបណ្ណពាក់ព័ន្ធស្ថិតក្នុង source snapshot។
- SHA-256 របស់ upstream និងច្បាប់ចម្លង៖ `fadf54bea20f337a03baddf2bd294c86d254a744456c6e53ee13f4ad25a58716`។ ផ្ទៀងផ្ទាត់ជាមួយ [`gboard-patches-4.0.0.mpp.sha256`](gboard-patches-4.0.0.mpp.sha256)។ Hash ដូចគ្នាមានន័យថាបៃដូច asset ដែល GitHub API របស់ upstream រាយ ប៉ុន្តែមិនជំនួសហត្ថលេខាឌីជីថល ឬការសវនកម្មទេ។
- Metadata ដើម៖ [`patches-list.json`](patches-list.json); ទីមក និង pin៖ [`upstream.json`](upstream.json)។
- ការផ្ទៀងផ្ទាត់ស្វ័យប្រវត្តិ និងស្ថានភាពពិត៖ [`morphe-validation.json`](morphe-validation.json)។ ការរាយ patches ដោយ engine មិនស្មើនឹងការសាកល្បង patch APK ឬដំណើរការលើទូរស័ព្ទទេ។ គម្រោងនេះមិនទាន់សាកល្បង APK Gboard ពិត ឬមុខងារលើឧបករណ៍។
- សម្រាប់អ្នកអភិវឌ្ឍន៍៖ `python3 tools/gboard/verify_bundle.py --verify-vendor` និង `python3 tools/gboard/test_verification.py`។ ដើម្បី build ពី source ប្រើ Java 21, Android SDK និងការចូល Morphe GitHub Packages តាមការណែនាំក្នុង [README upstream](../../extras/gboard-patches/README.md#build)។ កុំដាក់ credentials ក្នុង repository ឬក្នុង chat។
