# Telegram Add Email — patch សាកល្បង

នេះជា **bundle សាកល្បងដាច់ដោយឡែក** ពី [Telegram bundle ដើម](../telegram/README.md)៖ រក្សា Telegram subset របស់ [rushiranpise/morphe-patches v1.23.1](https://github.com/rushiranpise/morphe-patches/releases/tag/v1.23.1) និងបន្ថែម selector មួយ។ វាមិនជំនួស bundle ដើម ឬ bundle របស់ app ផ្សេងទេ។ មិនមាន release ថ្មីត្រូវបានចេញផ្សាយទេ។

<details>
<summary>🧪 Selector បន្ថែម • បិទជាស្រេច</summary>

| ឈ្មោះក្នុង Morphe Manager | អ្វីដែលសាក |
|---|---|
| `Try another login method (experimental)` | នៅផ្ទាំង **Add Email** បង្ហាញប៊ូតុងសាក SMS/call តែពេលចម្លើយ server ផ្ដល់ `next_type` ដែលសមស្រប។ រង់ចាំតាម timeout ហើយស្នើម្ដងតែបន្ទាប់ពីអ្នកចុចបញ្ជាក់។ បើ server មិនផ្ដល់ជម្រើសនោះ ផ្ទាំង Add Email នៅដដែល។ |

</details>

**សំខាន់:** នេះមិនមែនជា patch ដែលបញ្ជាឱ្យ server ផ្ញើ OTP ដោយឥតគិតថ្លៃទេ។ មិនទាន់មានភស្តុតាងថា server ផ្ដល់ `next_type` នៅ Add Email សម្រាប់លេខរបស់អ្នក; ដូច្នេះប៊ូតុងអាចមិនលេចឡើងសោះ។ ទោះបង្ហាញក៏ដោយ Telegram អាចបដិសេធ ទាមទារ email ម្ដងទៀត បង្ហាញការបង់ប្រាក់ ឬដាក់ rate limit។ Patch មិនក្លែងបន្លំការផ្ទៀងផ្ទាត់ មិន reset login email និងមិនលាក់ផ្ទាំងថ្លៃ។ [ការពិនិត្យ protocol](../../docs/telegram/sms-fee-investigation.md) ពន្យល់បន្ថែម។

## ទាញយក និងរបៀបប្រើ

ទាញយក [`bundle.mpp`](bundle.mpp) សម្រាប់ Morphe Manager។ SHA-256៖ `f5dc6a460e3e0d4c092c3b232f086e03e76db688294e78196ed3744f15284788` ([ឯកសារត្រួតពិនិត្យ](bundle.mpp.sha256))។ វាជា patch bundle មិនមែន APK ទេ។

1. នៅក្នុង Morphe Manager ជ្រើស **Sources → + → Local** ហើយបញ្ចូល `bundle.mpp` សាកល្បង។ ដើម្បីជៀសវាងឈ្មោះ patch ស្ទួន សូមកុំបើក Telegram source ដើម និង bundle សាកល្បងនេះក្នុងពេលតែមួយ។ Local source មិន update ស្វ័យប្រវត្តិទេ។
2. ក្នុង Manager 2.2.0 បើក **Settings → Expert mode** ដើម្បីជ្រើស patch ដោយខ្លួនឯង។ ជ្រើស APK ដើម `org.telegram.messenger` **12.10.1 / 70382** ឬ `org.telegram.messenger.web` **12.10.1 / 70389**។ កំណែទាំងនេះជាគោលដៅដែល bundle ប្រកាស ប៉ុន្តែ APK Telegram ពី Google Play មិនទាន់បានសាកនៅទីនេះទេ។
3. នៅបញ្ជី patches បើក `Try another login method (experimental)` ដោយខ្លួនឯង ព្រោះវា **បិទជាស្រេច**។ Patches upstream ផ្សេងៗបើកជាមុន; ដកអ្វីដែលអ្នកមិនចង់ប្រើ រួច patch និង sign។ Telegram Plus មិនមាន selector សាកល្បងនេះទេ។
4. បើ Telegram បង្ហាញ **Add Email** និង server ផ្ដល់ជម្រើសទូរសព្ទដែលគាំទ្រ ប៊ូតុងនឹងអាចចុចបានក្រោយពេលរង់ចាំ។ អានសារព្រមាន រួចចុចបញ្ជាក់ដើម្បីសាក **ម្ដង**។ បើប៊ូតុងមិនមាន អាចដោយ server មិនផ្ដល់ជម្រើស ឬ patch មិនអាចដំណើរការលើ APK នោះ; កុំសន្មតថា OTP ត្រូវបានផ្ញើ ឬថាយើងដឹងច្បាស់ពីមូលហេតុ។
5. ប្រសិនបើសំណើបរាជ័យ ឬ hash ចាស់ផុតកំណត់ អាចត្រូវត្រឡប់ទៅផ្ទាំងលេខទូរសព្ទ ហើយធ្វើតាម Telegram។ កុំស្នើកូដម្ដងហើយម្ដងទៀត។ **កុំផ្ញើលេខទូរសព្ទពេញ OTP email password ឬ session មកទីនេះ**។

ការសាកប្រើលេខ និង challenge hash ដែល app បានទទួល ដើម្បីស្នើទៅ Telegram តាម API ដើម; patch មិនបន្ថែមសេវាភាគីទីបី ឬកត់ត្រាព័ត៌មានទាំងនេះទេ។ ការចុះហត្ថលេខាថ្មីធ្វើឱ្យ APK មិនអាច update app ដើមដែលប្រើ key ផ្សេង។ **កុំលុប Telegram ដែលនៅ login ដោយមិនត្រៀមទិន្នន័យជាមុន**; Secret Chats និងទិន្នន័យមូលដ្ឋានអាចបាត់។

## អ្វីដែលបាន និងមិនទាន់សាក

- [CI សាក Morphe Manager 2.2.0](manager-smoke.json) បាន import bundle នេះ ជ្រើស patch សាកល្បងតែមួយ ហើយ Manager បង្ហាញ **Patched · 1 patch** សម្រាប់ APK Telegram Web 12.10.1 ពិតលើ Android 15 emulator។ មិនបានពិនិត្យ DEX ឬបើក APK ដែល Manager បង្កើតក្នុងការសាកនោះទេ។
- [CI build ដំបូង](validation.json) បានប្រើ Morphe Desktop patch Telegram Web ទាំងជ្រើស patch សាកល្បងតែមួយ និងជ្រើសជាមួយ upstream defaults; វាបានពិនិត្យ hooks ក្នុង DEX ហើយសាក UI ជាមួយទិន្នន័យសំយោគនៅលើ [emulator](android-smoke.json)។ `validation.json` រាយថា Manager មិនទាន់សាក **ក្នុង run ដំបូងនោះ**; ការសាក Manager ខាងលើធ្វើឡើងបន្ទាប់មក។
- **មិនទាន់សាក** login/signup ជាមួយគណនីដែលជួបបញ្ហា, ការឆ្លើយតប `next_type`/resend ពិត, APK Google Play ឬទូរសព្ទពិត។ ដូច្នេះ មិនមានភស្តុតាងថាអាចទទួល OTP ដោយមិនគិតថ្លៃ ឬជៀស SMS Fee បានទេ។
