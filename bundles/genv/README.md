# GenV — Morphe patch សាកល្បង

នេះជា **bundle `.mpp` ដាច់ដោយឡែក** សម្រាប់ Morphe Manager មិនមែន APK សម្រាប់ដំឡើងផ្ទាល់ និងមិនប្ដូរ bundles របស់ app ផ្សេង។

<details>
<summary>🎬 GenV • 1 experimental patch</summary>

| ឈ្មោះក្នុង Manager | ជម្រើសដើម | អ្វីដែលបានកែ |
|---|---|---|
| `Remove license check` | បើក | បញ្ឈប់ចំណុចចាប់ផ្ដើម PairIP license check ពីរដែលបានពិនិត្យក្នុង client: `LicenseClient.checkLicense(Context)` និង `initializeLicenseCheck()`។ វាមិនបង្កើតលទ្ធផល license ជោគជ័យក្លែងក្លាយ និងមិនកែ billing ឬ subscription ទេ។ |

</details>

**គោលដៅ:** package `com.ainate.ai.video.generate`, version **3.7.2**, version code **163**, Android 7.0+ (API 24)។ Patch ពិនិត្យ package, version, version code និងទម្រង់ methods/call sites មុនកែ; បើមិនត្រូវ ឬបាន patch រួច វាបដិសេធ។ ការផ្ទៀងផ្ទាត់ fingerprint មិនស្មើនឹងការធានាប្រភព ឬភាពសុវត្ថិភាពរបស់ APK ទេ។ សម្រាប់ការធ្វើតេស្ត យើង pin SHA-256 នៃ APK ក្នុង release ជាក់លាក់ខាងក្រោម។

## សំខាន់៖ APK ក្នុង Release មិនទាន់ពេញលេញ

[Release `GenV`](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/tag/GenV) មាន `GenV_3.7.2.apk` SHA-256 `f50a9d162a5802ce30ba842c09d08c8c2b2c816dc439eb1b8c0346aa71501d2e`។ ការពិនិត្យឃើញ `com.android.vending.splits.required=true` ហើយ base APK នេះគ្មាន native libraries ទេ។ ដូច្នេះ **កុំរំពឹងថា APK មួយនេះអាចដំឡើង និងដំណើរការជា app ពេញបានដោយឯករាជ្យ**។ ត្រូវការ base និង splits ដែលត្រូវគ្នាទាំងអស់ (រួម ABI/device configuration) ពីប្រភពដែលទុកចិត្ត និងមាន package, version និងហត្ថលេខាត្រូវគ្នា។ ការរួម splits ពេញរបស់ GenV មិនទាន់បានសាកនៅទីនេះទេ។ [ព័ត៌មានពិនិត្យ](release-inspection.json)។

`apksigner` ផ្ទៀងផ្ទាត់ថាហត្ថលេខាក្នុងឯកសារមានសុពលភាព ប៉ុន្តែ **មិនមែនជាការផ្ទៀងផ្ទាត់ឯករាជ្យថាជា APK ផ្លូវការរបស់អ្នកបង្កើត**។ កុំបញ្ចូលទិន្នន័យផ្ទាល់ខ្លួន ឬពាក្យសម្ងាត់ក្នុង app ដែលមិនទាន់ទុកចិត្ត។ ការ patch និង sign ឡើងវិញមិនធ្វើឱ្យ APK ដែលមានប្រភពមិនច្បាស់ក្លាយជាសុវត្ថិភាពទេ។

## របៀបប្រើ

1. ទាញយក [GenV-patches-v0.1.0-dev.1.mpp ពី pre-release](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/download/GenV/GenV-patches-v0.1.0-dev.1.mpp) និង [checksum](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/download/GenV/GenV-patches-v0.1.0-dev.1.mpp.sha256) ឬ [`bundle.mpp` ក្នុង repository](bundle.mpp)។ ក្នុង Morphe Manager ចូល **Sources → Add patch source → Local** ហើយជ្រើស `.mpp`។ Local source មិន update ស្វ័យប្រវត្តិ។
2. នៅ **Sources**, ជ្រើស **GenV patches (experimental)** ហើយបើក **Experimental app versions**។ បើចង់មើល selector ផ្ទាល់ បើក **Settings → Expert mode** ផង។
3. នៅ **Apps → GenV**, ជ្រើស **No, I already have it** រួចជ្រើសឯកសារ APK/split archive ពេញលេញ ដែលត្រូវនឹង build ខាងលើ។ ពិនិត្យការព្រមានរបស់ Manager និងប្រភពឯកសារ។ ទោះ Manager អាច patch base ក្នុងការសាករបស់យើង ក៏វា **មិនបំពេញ split ដែលបាត់ទេ**។
4. ពិនិត្យថា **Remove license check** ត្រូវបានជ្រើស រួចចុច **Patch**។ APK ដែល Manager ចុះហត្ថលេខាថ្មីអាចមិនអាច update ពី app ដើមដែលមាន key ផ្សេង។ បម្រុងទុកទិន្នន័យមុនពិចារណាលុប app ចាស់; ការលុបអាចធ្វើឱ្យបាត់ទិន្នន័យ។

## តេស្ត និងដែនកំណត់

- [Morphe Desktop build និង DEX test](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/42483563872) បាន patch ច្បាប់ចម្លងបណ្ដោះអាសន្ននៃ base ដែលមាន SHA ខាងលើ។ របាយការណ៍បញ្ជាក់ early `return-void` ក្នុង methods ពីរនោះ; app/provider call sites, billing method ដែលបានពិនិត្យ និង manifest នៅដដែល។ ការព្យាយាម patch ម្ដងទៀតត្រូវបានបដិសេធ។ [patch-validation.json](patch-validation.json)។
- [Morphe Manager test](manager-smoke.json) នាំចូល bundle, បើក experimental target និង patch **base ដែលមិនពេញ** ក្នុង Android emulator; លទ្ធផលត្រូវបានពិនិត្យ DEX និង signature ប៉ុន្តែ app ពិតមិនបានដំឡើង ឬបើកទេ។
- [Synthetic Android test](android-smoke.json) ប្រើ app សិប្បនិម្មិតដែលមាន opcode shape ដូច fingerprint និង counters គ្មានបណ្ដាញ/គណនី។ វាសាកសកម្មភាពមុន/ក្រោយ patch និងបដិសេធ version code ឬ opcode ដែលខុស។ **នេះមិនមែនការសាក runtime របស់ GenV ពិតទេ**។
- Patch នេះបិទតែ PairIP client entry points ដែលបានពិនិត្យ មិនធានាដក license checks ផ្សេងទៀតទាំងអស់។ វាមិនផ្ដល់ purchase/subscription, server entitlement ឬរំលង server/Play Integrity attestation ទេ។ ការបើក GenV ពិត, login, ការរួម splits និងឥរិយាបថ server/paid features **មិនទាន់បានផ្ទៀងផ្ទាត់**។
- APK ដើម និង tag `GenV` មិនត្រូវបានកែ ជំនួស ឬផ្លាស់ទី។ Tag មានស្រាប់ចង្អុលទៅ commit មុន patch ដូច្នេះ source archive នៅ tag នោះ **មិនមាន source ថ្មីនេះទេ**; source បច្ចុប្បន្ននៅ working branch រហូតដល់ merge។ ប្រើលើច្បាប់ចម្លង និង app ដែលអ្នកមានសិទ្ធិកែ។

Bundle SHA-256: `818c9b0972515d506d06a6f27e08419e68e1e513ecc07a2194b8fbc91227fe26`។ ប្រភព៖ [`tools/genv/project`](../../tools/genv/project/) · [checksum](bundle.mpp.sha256) · [របាយការណ៍](validation.json)
