# ការពិនិត្យ Telegram SMS Fee សម្រាប់ login / បង្កើតគណនី

## លទ្ធផល

**មិនបានបន្ថែម patch រំលងការបង់ប្រាក់ទេ។** មិនទាន់មានវិធីដែលបានផ្ទៀងផ្ទាត់ថា `.mpp` ខាង client អាចបញ្ជាឱ្យ Telegram បោះបង់ SMS Fee ឬផ្ញើកូដសម្រាប់គ្រប់គណនីបាន។ កុំសន្មតថាការលាក់ផ្ទាំងបង់ប្រាក់មានន័យថាលេខទូរសព្ទត្រូវបានផ្ទៀងផ្ទាត់ហើយ។ Bundle ដែលមានស្រាប់មិនត្រូវបានផ្លាស់ប្ដូរ។

## ភស្តុតាង

- [ឯកសារ Telegram API](https://core.telegram.org/api/auth) បញ្ជាក់ថា server ជ្រើសរបៀបផ្ញើកូដ ហើយអាចត្រឡប់ [`auth.sentCodePaymentRequired`](https://core.telegram.org/constructor/auth.sentCodePaymentRequired) សម្រាប់ login/sign-up ខ្លះ។ ចម្លើយនេះមានរូបិយប័ណ្ណ និងចំនួនទឹកប្រាក់; តម្លៃមិនចាំបាច់ស្មើ $1 សម្រាប់គ្រប់ករណីទេ។
- ក្នុង [source Telegram Android 12.10.1 ដែល pin តាម commit](https://github.com/DrKLO/Telegram/blob/62b56a07ca7e30e39f7fd00a6728d6bbd716ca1c/TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java#L1757-L1769), `fillNextCodeParams` ទទួល `TL_auth_sentCodePaymentRequired` ពីចម្លើយ ហើយទៅ `VIEW_PAY`។ [ផ្លូវទូទាត់](https://github.com/DrKLO/Telegram/blob/62b56a07ca7e30e39f7fd00a6728d6bbd716ca1c/TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java#L10273-L10291) ក៏ស្នើ `TL_checkPaidAuth` និងរង់ចាំចម្លើយ server។
- API ក៏មានកូដតាម Telegram app, SMS, call និងជម្រើសផ្សេងៗដែល server អាចជ្រើសបាន។ ហេតុនេះការដែលគណនីខ្លះមិនឃើញថ្លៃ **មិនបង្ហាញថាមាន client switch សម្រាប់បិទថ្លៃគ្រប់គណនី**។ កុំសាកល្បងស្នើកូដម្តងហើយម្តងទៀត ព្រោះអាចជួប rate limit។
- នេះជាការវិភាគ source និង protocol ប៉ុណ្ណោះ។ មិនមានការចូលគណនី ស្នើ OTP ប្រើលេខទូរសព្ទរបស់អ្នក ឬសាកគណនីដែលជាប់ថ្លៃទេ។ ការសាក emulator នៃ bundle មុននេះគ្រាន់តែបើក app ប៉ុណ្ណោះ។

## ជម្រើសដែលអាចសាកដោយសុវត្ថិភាព

1. **គណនីចាស់ដែលនៅ login លើឧបករណ៍ផ្សេង:** ពិនិត្យ chat ដែលមានសញ្ញាផ្ទៀងផ្ទាត់ឈ្មោះ **Telegram**។ ប្រសិនបើ Telegram ជ្រើសផ្ញើកូដតាម app នោះ អាចប្រើកូដនោះបាន; វាមិនត្រូវបានធានាសម្រាប់គ្រប់ការស្នើទេ។ សម្រាប់ Desktop អាចប្រើ QR ដោយឧបករណ៍ដែលបាន login រួច។
2. **Passkey:** បើគណនីកំពុង login រួច សូមប្រើ official Telegram → **Settings → Privacy and Security → Passkeys** ដើម្បីបង្កើត passkey សម្រាប់ login ពេលក្រោយ។ វាត្រូវការ passkey ដែលបានបង្កើតរួច និងគាំទ្រដោយឧបករណ៍; ប្រសិនបើបានបើក 2-Step Verification អាចនៅតែត្រូវការពាក្យសម្ងាត់នោះ។ Telegram [បញ្ជាក់ថា unofficial apps មានកម្រិតលើ passkey](https://core.telegram.org/api/passkeys); passkey ក្នុង APK ដែល patch និង sign ឡើងវិញ **មិនទាន់សាក** ដូច្នេះកុំសន្មតថាវាដំណើរការ។
3. **គណនីថ្មី ឬគ្មាន session/passkey:** ប្រសិនបើ official Telegram ផ្ដល់តែ SMS Fee គ្មានផ្លូវឥតគិតថ្លៃណាមួយត្រូវបានបញ្ជាក់សម្រាប់ការស្នើនោះទេ។ អាចទាក់ទង [Telegram Support](https://telegram.org/support) ឬប្រើជម្រើសដែល app ផ្ដល់។

កុំចែករំលែកលេខទូរសព្ទពេញ, OTP, 2FA password, session ឬ passkey នៅទីនេះ ឬផ្ញើឱ្យអ្នកផ្សេង។ កុំទុកចិត្ត bot ឬអ្នកលក់ដែលសន្យា bypass 100%។ កុំលុប app ដែលនៅ login មុនរៀបចំទិន្នន័យ និងវិធីចូលជំនួស។
