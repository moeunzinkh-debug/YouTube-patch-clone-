# ការពិនិត្យ Telegram SMS Fee សម្រាប់ login / បង្កើតគណនី

## លទ្ធផល

**មិនបានបន្ថែម patch រំលងការបង់ប្រាក់ទេ។** មិនទាន់មានវិធីដែលបានផ្ទៀងផ្ទាត់ថា `.mpp` ខាង client អាចបញ្ជាឱ្យ Telegram បោះបង់ SMS Fee ឬផ្ញើកូដសម្រាប់គ្រប់គណនីបាន។ កុំសន្មតថាការលាក់ផ្ទាំងបង់ប្រាក់មានន័យថាលេខទូរសព្ទត្រូវបានផ្ទៀងផ្ទាត់ហើយ។ Bundle ដែលមានស្រាប់មិនត្រូវបានផ្លាស់ប្ដូរ។

## ករណីស្នើ email មុនទទួលកូដ

ការសង្កេតថាករណីដែលស្នើ Gmail/email ជាញឹកញាប់បន្តទៅកាន់ SMS Fee គឺមានប្រយោជន៍សម្រាប់ស៊ើបអង្កេត ប៉ុន្តែមិនទាន់បញ្ជាក់ថា **email ជាមូលហេតុបង្កើតថ្លៃ** ឬថាការលាក់វានឹងធ្វើឱ្យមាន SMS ឥតគិតថ្លៃទេ។ អេក្រង់ដែលមើលទៅស្រដៀងគ្នាអាចមានន័យខុសគ្នា៖

- **ស្នើបន្ថែម email សម្រាប់ login:** [Telegram API](https://core.telegram.org/api/auth) អាចត្រឡប់ `auth.sentCodeTypeSetUpEmailRequired`។ នៅ [Telegram Android 12.10.1](https://github.com/DrKLO/Telegram/blob/62b56a07ca7e30e39f7fd00a6728d6bbd716ca1c/TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java#L1930-L1933) app ទៅផ្ទាំង Add Email; protocol ណែនាំឱ្យផ្ទៀងផ្ទាត់ email ហើយបន្ទាប់មក server បញ្ជូនជំហាន `auth.sentCode` បន្ទាប់។ ការលាក់ផ្ទាំងនោះមិនមែនជាការផ្ទៀងផ្ទាត់ email និងមិនធានាថាមាន OTP ទូរសព្ទត្រូវបានផ្ញើរួចទេ។ ជម្រើស **Sign in with Google** គឺជាជម្រើសមួយក្នុង UI នេះ មិនមែនមានន័យថាត្រូវប្រើ Gmail ជានិច្ចទេ; អាចបញ្ចូល email ត្រឹមត្រូវដែលអ្នកគ្រប់គ្រង ប្រសិនបើអ្នកចង់បន្តតាមផ្លូវនេះ និង server ទទួលយក។
- **កូដសម្រាប់ login ត្រូវបានផ្ញើទៅ email ដែលមានរួច:** `auth.sentCodeTypeEmailCode` ជាផ្លូវផ្សេង។ ក្នុង [source ផ្ទាំងកូដ email](https://github.com/DrKLO/Telegram/blob/62b56a07ca7e30e39f7fd00a6728d6bbd716ca1c/TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java#L6443-L6470) មានប៊ូតុង Resend code; [កម្មវិធីអាចបង្ហាញវាក្រោយពេលរង់ចាំ](https://github.com/DrKLO/Telegram/blob/62b56a07ca7e30e39f7fd00a6728d6bbd716ca1c/TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java#L6679-L6688) ប្រសិនបើ server ផ្ដល់ `next_type`។ Telegram ជាអ្នកសម្រេចចម្លើយបន្ទាប់; វាមិនធានាថាជា SMS ឥតគិតថ្លៃទេ ហើយការស្នើញឹកញាប់អាចជាប់ rate limit។
- **សំណើបន្ថែម/ផ្លាស់ប្ដូរ login email ក្រោយចូលគណនី:** នេះជាផ្លូវដាច់ដោយឡែក។ ក្នុង [source](https://github.com/DrKLO/Telegram/blob/62b56a07ca7e30e39f7fd00a6728d6bbd716ca1c/TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java#L483-L490) និង [UI](https://github.com/DrKLO/Telegram/blob/62b56a07ca7e30e39f7fd00a6728d6bbd716ca1c/TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java#L751-L758) មានករណីដែលអាច Skip បាន បើសំណើនោះអនុញ្ញាត។ មិនត្រូវយកការមាន Skip នៅទីនេះទៅសន្មតថា email ដែល server ទាមទារពេល login/signup អាច Skip ដូចគ្នាទេ។

`next_type` គឺជាវាល **ស្រេចចិត្ត** ក្នុង `auth.sentCode` សម្រាប់វិធីបន្ទាប់នៅពេលវាត្រូវបានផ្ដល់។ មិនទាន់មានភស្តុតាងថា server ផ្ដល់ជម្រើសនេះលើអេក្រង់ Add Email របស់ករណីដែលមានបញ្ហា ឬទទួល `auth.resendCode` មុនបញ្ចប់ email setup ទេ។ ដូច្នេះមិនទាន់បង្កើត patch ដែលសន្យាថារំលង email/SMS Fee; bundle `.mpp` នៅដដែល។ កុំ reset login email ដោយស្វ័យប្រវត្តិ។

បើចង់ស៊ើបអង្កេតបន្ត សូមចែករំលែក **ពាក្យដែលបង្ហាញលើអេក្រង់** ឬរូបថតដែលបិទបាំងលេខទូរសព្ទ អាសយដ្ឋាន email OTP ពាក្យសម្ងាត់ និងទិន្នន័យ session ជាមុន ព្រមទាំង version របស់ Telegram; កុំផ្ញើលេខកូដ ឬព័ត៌មានសម្ងាត់។

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
