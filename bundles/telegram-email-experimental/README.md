# Telegram Add Email — patch សាកល្បង

នេះជា **bundle សាកល្បងដាច់ដោយឡែក** ពី [Telegram bundle ដើម](../telegram/README.md)៖ រក្សា Telegram subset របស់ [rushiranpise/morphe-patches v1.23.1](https://github.com/rushiranpise/morphe-patches/releases/tag/v1.23.1) និងបន្ថែម selector មួយ។ វាមិនជំនួស bundle ដើម ឬ bundle របស់ app ផ្សេងទេ។ មិនមាន release ថ្មីត្រូវបានចេញផ្សាយទេ។

<details>
<summary>🧪 Selector បន្ថែម • បិទជាស្រេច</summary>

| ឈ្មោះក្នុង Morphe Manager | អ្វីដែលសាក |
|---|---|
| `Try another login method (experimental)` | នៅផ្ទាំង **Add Email** បង្ហាញប៊ូតុងសាក SMS/call តែពេលចម្លើយ server ផ្ដល់ `next_type` ដែលសមស្រប។ រង់ចាំតាម timeout ហើយស្នើម្ដងតែបន្ទាប់ពីអ្នកចុចបញ្ជាក់។ បើ server មិនផ្ដល់ជម្រើសនោះ ផ្ទាំង Add Email នៅដដែល។ |

</details>

**សំខាន់:** នេះមិនមែនជា patch ដែលបញ្ជាឱ្យ server ផ្ញើ OTP ដោយឥតគិតថ្លៃទេ។ មិនទាន់មានភស្តុតាងថា server ផ្ដល់ `next_type` នៅ Add Email សម្រាប់លេខរបស់អ្នក; ដូច្នេះប៊ូតុងអាចមិនលេចឡើងសោះ។ ទោះបង្ហាញក៏ដោយ Telegram អាចបដិសេធ ទាមទារ email ម្ដងទៀត បង្ហាញការបង់ប្រាក់ ឬដាក់ rate limit។ Patch មិនក្លែងបន្លំការផ្ទៀងផ្ទាត់ មិន reset login email និងមិនលាក់ផ្ទាំងថ្លៃ។ [ការពិនិត្យ protocol](../../docs/telegram/sms-fee-investigation.md) ពន្យល់បន្ថែម។

## របៀបប្រើ បើ CI បានបង្កើត `bundle.mpp` ក្នុងថតនេះរួច

1. នៅក្នុង Morphe Manager ជ្រើស **Sources → + → Local** ហើយបញ្ចូល `bundles/telegram-email-experimental/bundle.mpp`។ ដើម្បីជៀសវាងឈ្មោះ patch ស្ទួន សូមកុំបើក Telegram source ដើម និង bundle សាកល្បងនេះក្នុងពេលតែមួយ។
2. ជ្រើស APK ដើម `org.telegram.messenger` **12.10.1 / 70382** ឬ `org.telegram.messenger.web` **12.10.1 / 70389**។ Patch ថ្មី **បិទជាស្រេច**; បើចង់សាក ត្រូវជ្រើសវាដោយខ្លួនឯង។ Patches upstream ផ្សេងៗបើកជាមុន; ដកអ្វីដែលអ្នកមិនចង់ប្រើ។ Telegram Plus មិនមាន selector សាកល្បងនេះទេ។
3. បើ Telegram បង្ហាញ **Add Email** និង server ផ្ដល់ជម្រើសទូរសព្ទ ប៊ូតុងនឹងអាចចុចបានក្រោយពេលរង់ចាំ។ អានសារព្រមាន រួចចុចបញ្ជាក់ដើម្បីសាក **ម្ដង**។ បើប៊ូតុងមិនមាន វាមិនមានជម្រើសដែល patch អាចស្នើបាននៅការឆ្លើយតបនោះទេ; កុំសន្មតថា OTP ត្រូវបានផ្ញើ។
4. ប្រសិនបើសំណើបរាជ័យ ឬ hash ចាស់ផុតកំណត់ អាចត្រូវត្រឡប់ទៅផ្ទាំងលេខទូរសព្ទ ហើយធ្វើតាម Telegram។ កុំស្នើកូដម្ដងហើយម្ដងទៀត។ **កុំផ្ញើលេខទូរសព្ទពេញ OTP email password ឬ session មកទីនេះ**។

ការសាកប្រើលេខ និង challenge hash ដែល app បានទទួល ដើម្បីស្នើទៅ Telegram តាម API ដើម; patch មិនបន្ថែមសេវាភាគីទីបី ឬកត់ត្រាព័ត៌មានទាំងនេះទេ។ ការចុះហត្ថលេខាថ្មីធ្វើឱ្យ APK មិនអាច update app ដើមដែលប្រើ key ផ្សេង។ **កុំលុប Telegram ដែលនៅ login ដោយមិនត្រៀមទិន្នន័យជាមុន**; Secret Chats និងទិន្នន័យមូលដ្ឋានអាចបាត់។

`validation.json` និង `android-smoke.json` នៅថតនេះត្រូវបានបង្កើតដោយ CI បន្ទាប់ពីការត្រួតពិនិត្យឆ្លង។ ការសាកជាមួយទិន្នន័យសំយោគ ឬ APK Telegram Web **មិនមែន** ជាភស្តុតាងថា OTP ឬការជៀសថ្លៃដំណើរការលើ server, Google Play APK ឬទូរសព្ទពិតរបស់អ្នកទេ។
