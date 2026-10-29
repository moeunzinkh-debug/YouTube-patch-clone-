# Telegram Patch Clone v1.23.1-tg.1

**Pre-release** សម្រាប់ Morphe Manager៖ នេះគឺជា bundle Telegram ដើមរបស់ clone ដែល build ពី [rushiranpise/morphe-patches v1.23.1](https://github.com/rushiranpise/morphe-patches/releases/tag/v1.23.1) ប៉ុណ្ណោះ។ វាមិនមែនជាផលិតផលផ្លូវការរបស់ Telegram ឬ Morphe ទេ ហើយមិនជំនួស bundle YouTube, Gboard ឬ SimSimi។ ស្លាក pre-release បង្ហាញពីកម្រិតតេស្តរបស់ bundle ក្នុងគម្រោងនេះ មិនមែនជាការបន្ថែម patch skip email សាកល្បងទេ។

## ទាញយក និងប្រើ

1. ទាញយក **`bundle.mpp`** ពី Assets ខាងក្រោម។ វាជា patch bundle មិនមែន APK សម្រាប់ដំឡើងផ្ទាល់ទេ។
2. ក្នុង Morphe Manager ចូល **Sources → + → Local** ហើយជ្រើស `bundle.mpp`។ ជៀសវាងជ្រើស patches ដូចគ្នាពី sources ស្ទួន។
3. ជ្រើស APK ដើម និងកំណែដែល upstream រាយ៖ `org.telegram.messenger` 12.10.1 (70382), `org.telegram.messenger.web` 12.10.1 (70389) ឬ `org.telegram.plus` 12.10.1.1 (22510)។ កំណែផ្សេងមិនទាន់បានបញ្ជាក់។
4. Bundle មាន **15 upstream selectors**; Telegram ដើម និង Web មាន 14 ព្រោះ `Disable analytics` សម្រាប់ Plus ប៉ុណ្ណោះ។ Upstream បើក selectors ទាំងអស់ជាមុន ដូច្នេះត្រូវពិនិត្យ និងដកមុខងារដែលមិនចង់ប្រើមុន patch។ [បញ្ជី និងការព្រមានលម្អិត](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/blob/Telegram-v1.23.1-tg.1/bundles/telegram/README.md)។

**បញ្ហាដែលបានរាយការណ៍៖** `Disable auto-update` មាន fingerprint error នៅក្នុង log មួយសម្រាប់ `org.telegram.messenger` 12.10.1។ បើជួបបញ្ហានេះ អាចដក selector នោះជាបណ្ដោះអាសន្ន ហើយសាកម្ដងទៀត។ នេះមិនមែនជាការជួសជុល និងមិនធានាថា selectors ផ្សេងនឹងជោគជ័យទេ។

SHA-256 របស់ `bundle.mpp`: `c3fd498bff06cd6acaabadcec696cf571480e0212f3d530e4f9e425ca7573cbb` (776,015 bytes)។ `bundle.mpp.sha256` មាន checksum សម្រាប់ផ្ទៀងផ្ទាត់ឯកសារ។

## ស្ថានភាពសាកល្បង និងសុវត្ថិភាព

- [Build/Desktop CI](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/40834594669) បាន build bundle និង patch APK Telegram **Web** 12.10.1 ដែលផ្ទៀងផ្ទាត់ហត្ថលេខាដើម ដោយសាក `Remove ads` តែមួយ និង selectors 14 ទាំងអស់។
- [Android 15 emulator CI](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/40835921134) បានដំឡើង និងបើក APK Web ដើម និង APK ដែល patch ដោយគ្មានគណនី។ វាជា **launch smoke test** ប៉ុណ្ណោះ។
- Standard Telegram APK, Telegram Plus, ទូរស័ព្ទពិត, login/signup, notifications និងមុខងារនីមួយៗ **មិនទាន់សាកនៅទីនេះទេ**។ Bundle នេះមិនមាន patch skip email និងមិនធានាការជៀស SMS fee ឬ OTP ឥតគិតថ្លៃ។ `Unlock Premium` ជាការកែ client ប៉ុណ្ណោះ មិនផ្ដល់ subscription លើ server។
- App ដែល sign ឡើងវិញជាទូទៅមិនអាច update app ដើមដែលប្រើ key ផ្សេងបាន។ **កុំលុប Telegram ដើមដោយមិនត្រៀមទិន្នន័យ**៖ Secret Chats និងទិន្នន័យក្នុងឧបករណ៍អាចបាត់។ មុខងាររក្សាសារ/view-once ឬមិនជូនដំណឹង screenshot អាចប៉ះពាល់ឯកជនភាពអ្នកដទៃ។

## ប្រភព និងអាជ្ញាបណ្ណ

ការបង្កើតនេះជាផ្នែករង Telegram ដាច់ដោយឡែកពី upstream commit [`92c0fca0ae103a419c7fc61f9c5b8b38b7d6b82a`](https://github.com/rushiranpise/morphe-patches/tree/92c0fca0ae103a419c7fc61f9c5b8b38b7d6b82a) ក្រោម GPL-3.0។ [Source និង provenance](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/blob/Telegram-v1.23.1-tg.1/docs/telegram/upstream.md) · [LICENSE](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/blob/Telegram-v1.23.1-tg.1/extras/telegram-upstream/LICENSE) · [NOTICE](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/blob/Telegram-v1.23.1-tg.1/extras/telegram-upstream/NOTICE)។ ឯកសារ license របស់ dependency HiddenApiBypass ក៏មានក្នុង Assets។
