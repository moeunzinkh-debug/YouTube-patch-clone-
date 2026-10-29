# SimSimi notifications លើ Huawei — ការស៊ើបអង្កេត

**ស្ថានភាព៖** នេះជាការពិនិត្យ APK និងកូដឋិតិវន្ត មិនមែនការធ្វើតេស្ត push លើទូរសព្ទទេ។ គេមិនទាន់ដឹងថាលើទូរសព្ទរបស់អ្នកប្រើ MicroG មួយណា បើក patch routing ឬអត់ ហើយ notification មិនមកទាំងស្រុង ឬមានក្នុងផ្ទាំង notification តែអត់ banner។ កុំសន្និដ្ឋានថា RE mismatch ខាងក្រោមជាមូលហេតុពិតរបស់ទូរសព្ទនោះដោយមិនធ្វើតេស្ត។

## អ្វីដែលបានពិនិត្យ

- SimSimi 9.2.3 `com.ismaker.android.simsimi` version code `1119001`៖ `base.2.apk` SHA-256 `f18da384232c8e918e1073fd2e95cde6dda9bda2a34f4f90bb527ca95ea8af70`។
- APK ខាងលើដែលអនុវត្ត **តែ** `MicroG RE service routing (experimental)` ពី `bundles/simsimi/bundle.mpp` ដោយ Morphe Desktop 1.19.1។ Patch នេះបិទជាមុន។
- MicroG RE release `microg-re-v7.3.0-dev.2`, package `app.revanced.android.gms`, arm64 APK SHA-256 `b650b0325de4d80606597003d64ac7b358489c4e5eba6b76dfdc0008e0ca47e4`។
- MicroG Original-HW release `microg-original-hw-v0.3.17.255070`, manifest version `0.3.17.255070-hw`, package `com.google.android.gms`, arm64 APK SHA-256 `a8c5f8cd1845394f77d657ffdbff843bfb3ad86dcd1cc4afdac75cf098b46709`។
- ការពិនិត្យទាំងពីរ edition បានជោគជ័យនៅ [Actions run 40802411438](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/40802411438)។ Inspector ប្រើ APK release ដែលបានផ្ទៀងផ្ទាត់ hash; មិនទាញ token, គណនី ឬ log ពីឧបករណ៍អ្នកប្រើទេ។

## លទ្ធផល

APK SimSimi ប្រកាស `POST_NOTIFICATIONS` និងមាន Firebase/React Native Firebase messaging receivers និង services។ Manifest មានតែការប្រកាសប៉ុណ្ណោះ៖ វាមិនបង្ហាញថាអ្នកប្រើបានអនុញ្ញាត notification, ទទួល FCM token ឬ server បានផ្ញើសារពិតឡើយ។

**ការមិនត្រូវគ្នា RE ដែលបានបញ្ជាក់ក្នុង APK៖**

| ផ្លូវ | SimSimi ដែលបានជ្រើស RE routing | MicroG RE 7.3.0-dev.2 |
|---|---|---|
| Token-request action | `com.google.iid.TOKEN_REQUEST` | receiver ចុះបញ្ជី `app.revanced.iid.TOKEN_REQUEST` |
| Register action | `com.google.android.c2dm.intent.REGISTER` | service ចុះបញ្ជី `app.revanced.android.c2dm.intent.REGISTER` |
| SEND permission | Firebase metadata នៅតែប្រើ `com.google.android.c2dm.permission.SEND`; SimSimi messaging receivers ក៏ទាមទារវាពីអ្នកផ្ញើ | APK ប្រកាស និងស្នើ `app.revanced.android.c2dm.permission.SEND` មិនមែន Google-named permission នោះ |

DEX បង្ហាញថា routing patch ប្ដូរ native literal ពិតប្រាកដ `com.google.android.gms` ទៅ `app.revanced.android.gms` ប៉ុន្តែ **មិនប្ដូរ** ឈ្មោះ action និង permission ក្នុងតារាង។ ក្នុង `cloudmessaging.zzw.zzb` និង `firebase.iid.Metadata.getIidImplementation` កូដពិនិត្យ Google SEND permission សម្រាប់ package RE ហើយរក Google-named registration actions ក្នុង package RE។ នេះជាការមិនត្រូវគ្នាដែលអាចរារាំងការចុះបញ្ជី ឬការដឹកជញ្ជូន FCM នៅពេលប្រើបន្សំដែលបានពិនិត្យ ហើយមិនគួរចាត់ទុក routing patch ថាជា push fix ទេ។

សម្រាប់ **Original-HW** ដែលបានពិនិត្យវិញ manifest ប្រកាស Google-named `TOKEN_REQUEST`, `REGISTER` និង `SEND` ត្រូវនឹងឈ្មោះក្នុង SimSimi ដើម។ នេះបំបាត់ mismatch ឈ្មោះខាងលើក្នុងការប្រៀបធៀបឋិតិវន្តប៉ុណ្ណោះ មិនធានា token, Firebase compatibility ឬ notification ពិតលើ Huawei ទេ។

កូដ MicroG RE ដែលត្រូវនឹង release ក៏មាន [fallback ទៅ Google legacy receive action](https://github.com/moeunzinkh-debug/MicroG-Re-Rebuild-/blob/c6f05e6b0cdce7059a13898c1f99161eece021b3/play-services-core/src/main/java/org/microg/gms/gcm/McsService.java) ដែរ; ដូច្នេះមិនអាចនិយាយថា RE ខ្វះ legacy action support ទាំងអស់បានទេ។ ប៉ុន្តែ fallback action មួយនេះមិនបញ្ជាក់ថា permission សម្រាប់ផ្ញើទៅ receivers ឬ token registration ដំណើរការទេ។

## ពិនិត្យលើ Huawei ដោយមិនលុបទិន្នន័យ

1. **Settings → Notifications → SimSimi**៖ បើក Allow notifications និងប្រភេទ notification ទាក់ទង; បើក Banner/Pop-up/Lock screen តាមអ្វីដែលម៉ូដែលផ្ដល់។ ពិនិត្យ Do Not Disturb ផង។ បើ notification មានក្នុងផ្ទាំងតែគ្មាន banner សូមចាប់ផ្ដើមពី category និង banner ជាមុន។
2. **Settings → Apps → App launch** (ឈ្មោះម៉ឺនុយអាចខុសគ្នា)៖ សាក Manage manually និងអនុញ្ញាត Auto-launch, Secondary launch និង Run in background សម្រាប់ SimSimi និង GMS/MicroG ដែលបានដំឡើង។ ពិនិត្យ background data/Battery Saver ផង; ការបើក background អាចប្រើថ្មបន្ថែម។
3. ប្រសិនបើប្រើ MicroG៖ នៅ MicroG Settings ពិនិត្យ **Device Registration** និង **Cloud Messaging → Receive push notifications** និងស្ថានភាព connection/app list។ `Connected` តែមួយមិនធានាថា SimSimi បានចុះបញ្ជី ឬ server ផ្ញើជោគជ័យទេ។
4. បើសាកជាមួយ Google Play services ឬ Original-HW `com.google.android.gms` សូមកុំជ្រើស RE routing លើ APK ដែលនឹង patch; RE routing គឺសម្រាប់ `app.revanced.android.gms` មិនមែន Original-HW។ ការប្ដូរ selector ត្រូវ patch ឡើងវិញពី APK ដើម មិនមែនជាប៊ូតុងក្នុង app ដែលបានដំឡើង។ មិនចាំបាច់លុប app ឬសម្អាត data ដើម្បីធ្វើការពិនិត្យ settings ជាមុនទេ។
5. បើក SimSimi និងចូលគណនី រួចទុក app នៅ background ដោយមិន Force stop; ឱ្យគណនីផ្សេងផ្ញើសារ រង់ចាំពេលអេក្រង់បិទ ហើយប្រៀបធៀបថាមាន notification ក្នុងផ្ទាំង, មាន banner ឬមកក្រោយបើក app វិញ។ នេះជាការធ្វើតេស្តរោគសញ្ញា មិនធានាថារាល់សារនឹងបង្កើត notification ពី server ឡើយ។

ប្រភព Huawei៖ [ការកំណត់ notification/banner](https://consumer.huawei.com/uk/support/content/en-gb00918405/) និង [ការគ្រប់គ្រង app launch](https://consumer.huawei.com/en/support/content/en-us15850065/)។ មិនត្រូវចែករំលែក FCM token, account ID ឬ log ដែលមិនបានបិទទិន្នន័យឯកជន។
