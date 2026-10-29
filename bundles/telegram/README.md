# Telegram Patch Clone — bundle ដាច់ដោយឡែក

Bundle នេះជាការជ្រើសយក **តែ Telegram** ពី [rushiranpise/morphe-patches v1.23.1](https://github.com/rushiranpise/morphe-patches/releases/tag/v1.23.1) និង build ឡើងវិញសម្រាប់ Morphe Manager។ វា **មិនមែន APK របស់ Telegram**, មិនមែន bundle upstream ដែលមាន app ផ្សេងៗ និងមិនជំនួស `patch.mpp` របស់ YouTube ឬ bundle Gboard/SimSimi ទេ។

## កំណែដែល upstream កំណត់

| App Android | Package | Version / version code | Selectors |
|---|---|---|---|
| Telegram | `org.telegram.messenger` | `12.10.1` / `70382` | 14 |
| Telegram Web (Android package) | `org.telegram.messenger.web` | `12.10.1` / `70389` | 14 |
| Telegram Plus | `org.telegram.plus` | `12.10.1.1` / `22510` | 15 |

កំណែផ្សេងមិនត្រូវបានបញ្ជាក់ថាគាំទ្រទេ។ Telegram Web ខាងលើសំដៅលើ **Android package** នេះ មិនមែន website ក្នុង browser ទេ។ Telegram Plus ជា app ដាច់ដោយឡែក; upstream រាយវាជា XAPK ដូច្នេះការដំឡើងអាចត្រូវការ splits ដែលត្រូវគ្នា។

## របៀបប្រើ

1. ទាញយក [`bundle.mpp`](bundle.mpp) ទៅទូរស័ព្ទ។ ក្នុង **Morphe Manager** ចូល **Sources → + → Local** ហើយជ្រើសឯកសារ `.mpp` នោះ។ វាជា patch bundle ដាច់ដោយឡែក មិនមែន APK ដែលអាចដំឡើងដោយផ្ទាល់ទេ។ Local source មិន update ស្វ័យប្រវត្តិទេ។
2. ជ្រើស **APK ដើម** និង package/version ដូចតារាង។ មុន patch សូមពិនិត្យ selectors៖ **upstream បើកទាំងអស់ជាមុន** រួមទាំងមុខងារប៉ះពាល់ឯកជនភាព និង `Disable auto-update`។ ដកជម្រើសដែលអ្នកមិនចង់ប្រើ។
3. Patch និង sign តាម Manager។ Android ទាមទារ signature ដូចគ្នាដើម្បី update app ដែលមានស្រាប់; APK ដែល patch ហើយជាទូទៅមាន key ខុសពី Telegram ដើម។ **កុំលុប app ដើមដោយមិនត្រៀមទុកទិន្នន័យ**៖ Secret Chats និងទិន្នន័យក្នុងឧបករណ៍អាចបាត់។ សម្រាប់ split packages ត្រូវឱ្យ base និង splits ត្រូវកំណែ/ABI និងចុះហត្ថលេខាដូចគ្នា។

<details>
<summary>📨 Telegram • 15 patches (14 សម្រាប់ Telegram ដើម)</summary>

| ឈ្មោះក្នុង Manager | គោលបំណង upstream និងដែនកំណត់ |
|---|---|
| `Anti-delete messages` | ព្យាយាមរក្សាសារដែលអ្នកផ្សេងលុបនៅលើឧបករណ៍នេះ; មិនធានាការស្ដារសារដែលមិនធ្លាប់ទទួល។ |
| `Anti-disappearing media` | ព្យាយាមរក្សារូប វីដេអូ និងសារសំឡេង view-once។ វាប៉ះពាល់ឯកជនភាព និងកូដផ្លូវផ្ទុក/អ៊ិនគ្រីប secret media; កុំសន្មតថាមានសុវត្ថិភាពដូច app ដើម។ |
| `Anti-screenshot notification` | ព្យាយាមទប់ការផ្ញើសេចក្ដីជូនដំណឹង screenshot ទៅភាគីម្ខាងទៀត។ |
| `Bypass channel restrictions` | ព្យាយាមបើក ឬរក្សាទុក/forward មាតិកាខ្លះដែល channel ដាក់ការកំណត់; server នៅតែអាចទប់។ |
| `Bypass content restrictions` | ព្យាយាមរំលងការទប់ save/forward ខាង client ក្នុង chat/channel។ |
| `Bypass integrity check` | ប្ដូរលទ្ធផលពិនិត្យ certificate និង SafetyNet ខាង app; **មិនធានា login ឬឆ្លងការផ្ទៀងផ្ទាត់ hardware/server**។ |
| `Disable analytics` | Telegram Plus ប៉ុណ្ណោះ៖ ទប់ analytics/event tracking ខ្លះ; upstream រក្សា Firebase initialization ប៉ុន្តែ push មិនទាន់សាកល្បងនៅទីនេះ។ |
| `Disable auto-update` | ទប់ការឆែក update និង update screen របស់ app; អ្នកត្រូវតាមដាន security updates ដោយខ្លួនឯង។ |
| `Disable channel switching` | បិទ gesture អូសដើម្បីប្ដូរទៅ channel បន្ទាប់។ |
| `Download speed boost` | កែទំហំ chunk និងចំនួនសំណើទាញយកតាម upstream; **មិនធានាល្បឿន** ព្រោះអាស្រ័យលើ network/server។ |
| `Hide typing indicator` | ព្យាយាមមិនផ្ញើសញ្ញាថាកំពុងវាយ; មិនធានាថា server ឬ client ផ្សេងមិនបង្ហាញស្ថានភាពទេ។ |
| `Remove ads` | ព្យាយាមទប់ sponsored messages និង video ads; ការដក ads ទាំងអស់មិនទាន់បញ្ជាក់លើឧបករណ៍។ |
| `Unlock Premium` | ប្ដូរការត្រួតពិនិត្យ Premium **ក្នុង client**។ វាមិនបង្កើត subscription ឬសិទ្ធិលើ server; មុខងារខ្លះអាចមិនដំណើរការ ហើយ status/crown អាចបង្ហាញខុស។ |
| `Use normal paste` | រំលង Rich HTML paste ដើម្បីប្រើផ្លូវ paste ធម្មតា។ |
| `Voice to music` | ព្យាយាមចាក់ voice note ក្នុង music player។ កូដ upstream ក៏អាចប៉ះពាល់ការសម្គាល់ voice-once ទោះមិនជ្រើស Anti-disappearing ក៏ដោយ។ |

</details>

**ឯកជនភាព និងសុវត្ថិភាព៖** មុខងាររក្សាសារ/view-once ឬមិនជូនដំណឹង screenshot ផ្លាស់ប្ដូរការរំពឹងទុកឯកជនភាពរបស់អ្នកផ្ញើ។ ជ្រើសប្រើដោយការទទួលខុសត្រូវ។ Patches ជាច្រើនពឹងលើ code spoof signature និង install source របស់ upstream; វាមិនមែនជាការធានាថាសេវាសុវត្ថិភាព ឬការដំឡើង Android ត្រូវបានរំលងដោយជោគជ័យទេ។

## អ្វីដែលបានសាកល្បង

- CI បានផ្ទៀងផ្ទាត់ source ពី upstream, build bundle ដាច់ដោយឡែក និងប្រើ **Morphe Desktop 1.19.1** អានបាន 15 selectors និងកំណែគោលដៅ។
- Desktop បាន patch និង rebuild APK **Telegram Web 12.10.1 (70389)** ដែលបានផ្ទៀងផ្ទាត់ SHA-256 និងហត្ថលេខាដើម Telegram: ម្ដងជ្រើស `Remove ads` តែមួយ និងម្ដងជ្រើសទាំង 14 selectors សម្រាប់ package នោះ។ APK តេស្តមកពី [mirror ភាគីទីបី](https://github.com/LOVECHEN/telegram-release/releases/tag/android-12.10.1); repository នេះមិនចែកចាយ APK ទេ។
- លើ Android 15 emulator គ្មានគណនី ការដំឡើង និងបើក APK ដើម ព្រមទាំង APK ដែល patch ទាំងពីរ (ចុះហត្ថលេខាដោយ test key) បានដំណើរការ; process និង foreground activity នៅបន្តក្រោយ 12 វិនាទី។ នេះគ្រាន់តែជា launch smoke test ប៉ុណ្ណោះ។
- **មិនទាន់សាក** APK សម្រាប់ `org.telegram.messenger` ឬ Telegram Plus, UI របស់ Morphe Manager នៅ Android, login, notification, មុខងារនីមួយៗលើឧបករណ៍ពិត ឬសិទ្ធិ Premium លើ server ទេ។ ការសាក Desktop/emulator មិនធានាលទ្ធផលទាំងនោះឡើយ។

[ប្រភព អាជ្ញាបណ្ណ និងវិធី build](../../docs/telegram/upstream.md) · [លទ្ធផល Desktop](validation.json) · [លទ្ធផល emulator](android-smoke.json) · [SHA-256](bundle.mpp.sha256) · [ការពិនិត្យ email និង SMS Fee ពេល login](../../docs/telegram/sms-fee-investigation.md)
