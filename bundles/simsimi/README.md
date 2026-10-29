# SimSimi patches — កំណែសាកល្បង ដាច់ដោយឡែកពី YouTube

**Morphe bundle:** [`bundle.mpp`](bundle.mpp), **0.4.0-dev.1**។ សម្រាប់ **SimSimi 9.2.3** (`com.ismaker.android.simsimi`, version code `1119001`, Android API 24+)។ នេះជា `.mpp` សម្រាប់ Morphe Manager មិនមែន Python APK patcher ទេ។ កុំយកវាទៅជំនួស `patch.mpp` របស់ YouTube។

**ស្ថានភាពសំខាន់៖** បានកែផ្លូវកូដក្នុងកម្មវិធីសម្រាប់មុខងារទាំង ៦ ខាងក្រោម ប៉ុន្តែ **មិនទាន់សាកល្បងកំណែថ្មីលើទូរសព្ទ ឬបញ្ជាក់ការអនុញ្ញាតពីម៉ាស៊ីនមេទេ**។ ជាពិសេស patch Items មិនផ្ដល់ stock ឬសិទ្ធិប្រើ Items គ្មានកំណត់នៅលើម៉ាស៊ីនមេឡើយ។

## របៀបសាកល្បង

1. Import `bundles/simsimi/bundle.mpp` ជា local source ក្នុង Morphe Manager ហើយជ្រើស APK ដើម SimSimi 9.2.3។ បើមានជម្រើស **Experimental app versions** ក្នុង Sources សូមបើកសម្រាប់ bundle នេះ។ កុំប្រើ APK ដែលបាន patch រួចជាធាតុបញ្ចូល។
2. ដើម្បីសាក Quick Return សូម **បើក `Quick return: double-tap Chat (experimental)`** ក្នុងបញ្ជី patches៖ វាបិទជាមុន និងមិនតម្រូវឱ្យបើក Pull Refresh ឡើយ។
3. Patch និងដំឡើងជាមួយ ABI/config splits ដែលត្រូវគ្នា និងចុះហត្ថលេខាដោយ key ដូចគ្នាទាំង base និង splits។ ចូលបញ្ជី **Conversation ជាភាសាអង់គ្លេស**, អូសចុះក្រោម ហើយចុចរូប Chat ខាងក្រោម **ពីរដងជាប់គ្នា**។ គោលបំណងគឺឱ្យបញ្ជីត្រឡប់ទៅលើ ដោយមិន reload app។
4. បើចង់សាកមុខងារ Membership សូម **បើក selectors ទាំង ៦** ដែលមានពាក្យ `client only` ក្នុងតារាងខាងក្រោម៖ ពួកវាបិទជាមុន និងត្រូវការ `Unlock membership UI` ជា dependency។ សម្រាប់រូបថត និង read receipt សូមផ្ទៀងផ្ទាត់ជាមួយអ្នកទទួលពិត។
5. សម្រាប់ Items សូមប្រយ័ត្នប៊ូតុងទិញ៖ **ការទិញនៅតែអាចចំណាយ coins**។ ស្លាកថា unlimited នៅលើ UI មិនបញ្ជាក់ថាប្រើបានឥតគិតថ្លៃទេ។

<details>
<summary>SimSimi • 12 selectable experimental patches</summary>

| ឈ្មោះ patch ក្នុង Manager | លំនាំដើម | អ្វីដែលកែ និងដែនកំណត់ |
|---|---|---|
| Disable ad eligibility (experimental) | On | បិទ shared `canShowAds` gate; មិនទាន់បញ្ជាក់ថាលុប ads SDK ទាំងអស់។ |
| Unlock membership UI (client only, experimental) | On | ផ្ដល់ `hasMembership=true` ក្នុង client UI និង listener ដោយ clone ស្ថានភាព។ មិនបង្កើតការជាវ ឬសិទ្ធិនៅម៉ាស៊ីនមេ។ |
| Pull down to restart chat (experimental) | On | អូសចុះនៅបញ្ជី **Conversation ភាសាអង់គ្លេស** ប៉ុណ្ណោះ មិនមែនក្នុងបន្ទប់ឆាត។ វា reload React runtime ទាំងមូល មិនសម្លាប់ app និងមិនមែន refresh តែទិន្នន័យបញ្ជីទេ។ |
| Quick return: double-tap Chat (experimental) | Off | ចុច Chat ខាងក្រោមពីរដង នៅបញ្ជី Conversation ដើម្បីអូសបញ្ជីទៅដើមភ្លាមៗ ដោយមិន reload។ ចុចតែមួយនៅតែប្រើផ្លូវដើម; ការប្រើលើទូរសព្ទមិនទាន់សាកល្បង។ |
| MicroG RE service routing (experimental) | Off | ប្ដូរផ្លូវ native GMS ទៅ `app.revanced.android.gms`; ត្រូវដំឡើង MicroG RE ដាច់ដោយឡែក។ វា **មិនជួសជុល FCM push ទេ**៖ action និង permission មិនត្រូវនឹង RE 7.3.0-dev.2 ដែលបានពិនិត្យ។ [ព័ត៌មានលម្អិត](../../docs/simsimi/huawei-notifications.md)។ |
| Daily bonus without video (client path, experimental) | Off | ជ្រើសផ្លូវ membership ដែលមានស្រាប់ដោយមិនផ្ទុកវីដេអូ។ Server reward និង error នៅដដែល; មិនធានាការទទួលរង្វាន់។ |
| Conversation level controls (client only, experimental) | Off | ជ្រើស member branch ក្នុងសកម្មភាពប្ដូរ Freetalk level និងទុកសំណើរក្សាទុកកម្រិតទៅ server ដដែល។ មិនធានាប្រធានបទដែល server ផ្ដល់។ |
| Profile photo controls (client only, experimental) | Off | ជ្រើសផ្លូវបើក photo picker ជំនួសអេក្រង់ជាវ; ការផ្ទុក និងរក្សាទុករូបអាស្រ័យលើ server។ |
| Custom group cover controls (client only, experimental) | Off | បើក custom-cover picker និងប្រើ client membership flag ក្នុងទិន្នន័យ group។ មិនផ្ដល់ភាពជាម្ចាស់បន្ទប់ ឬសិទ្ធិ upload លើ server។ |
| Photo sending controls (client only, experimental) | Off | ជ្រើសផ្លូវផ្ញើរូបរបស់ member ទាំង direct និង group; ផ្លូវនេះអាចរំលង local quota/ad check។ មិនក្លែងការផ្ញើជោគជ័យ និងមិនប្ដូរច្បាប់ server ឬ moderation។ |
| Read receipt display (client only, experimental) | Off | បង្ហាញ indicator ដែលប្រើ `msgHasBeenRead` ដើម ជំនួសសញ្ញាសួររបស់ membership។ មិនបង្កើតទិន្នន័យថាបានអាន ប្រសិនបើ server មិនផ្ដល់។ |
| Membership item controls (client only, experimental) | Off | បង្ហាញ member item UI ដែលអាចមានស្លាក unlimited។ **មិនផ្ដល់ Items, coins, stock ឬធានាថា server អនុញ្ញាតឱ្យប្រើដោយឥតគិតថ្លៃ។** |

</details>

### ដែនកំណត់ Quick Return

- មុខងារនេះសម្រាប់ tab Chat ដែលបានជ្រើសរួច និងអេក្រង់ដែលបង្ហាញចំណងជើង `Conversation` ជាភាសាអង់គ្លេស ដូចក្នុងរូប។ វាព្យាយាមរំកិលបញ្ជីធំបំផុតទៅទីតាំង 0 មិនមែន reload ឬបិទ app។
- វាមិនទប់ការចុច tab ដើម ហើយព្យាយាមមិនដំណើរការនៅអេក្រង់ដែលមានប្រអប់សរសេរ។ ចំណងជើង និងប្រភេទ scroll view ត្រូវបានកំណត់ដោយផ្អែកលើរូប និងការវិភាគ APK; **មិនទាន់បញ្ជាក់លើទូរសព្ទ** ទេ។ បើ UI របស់អ្នកខុសពីនេះ វាអាចមិនដំណើរការ។

## ការផ្ទៀងផ្ទាត់

[Actions run 40799144878](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/40799144878) បាន៖

- Compile `.mpp` ដាច់ដោយឡែក និងពិនិត្យ selectors ទាំង ១២ ក្នុង Morphe Desktop; Quick Return បិទជាមុន។
- សាកល្បងចន្លោះពេលចុច និងការកំណត់គោលដៅអេក្រង់តាម Java host tests/stubs។ នេះមិនមែនជាការសាក Android ពិតទេ។
- អនុវត្ត `.mpp` លើ APK ដើមដោយ **Morphe Desktop v1.19.1** បីរបៀប៖ Quick Return តែមួយ, Pull Refresh តែមួយ និងទាំងពីររួមជាមួយមុខងារផ្សេងៗ។ ការពិនិត្យ DEX បានឃើញ hooks នៅ click handlers ខណៈផ្លូវ tab ដើម និង programmatic selection នៅដដែល; Hermes មិនផ្លាស់ប្ដូរក្នុង Quick Return តែមួយ។
- ពិនិត្យ combined Hermes, membership client gates, native reload hook និង MicroG visibility។ **មិនបាន** សាក Android Manager UI, ការដំឡើង/runtime លើទូរសព្ទ ឬ server entitlement។

Combined output Hermes SHA-256: `97bbf6a26444dd5755173800eae31579e972df1d1e54777d4dd68be7f7c89892`។ Bundle SHA-256 នៅ [`bundle.mpp.sha256`](bundle.mpp.sha256); លទ្ធផលលម្អិតនៅ [`quick-validation.json`](quick-validation.json), [`morphe-validation.json`](morphe-validation.json) និង [`build-status.json`](build-status.json)។

## APK splits និងការបង្កើត

APK ដើមដែលបានផ្ដល់ជា base APK មាន `splits.required=true` និងគ្មាន native libraries។ ការដំឡើងត្រូវមាន ABI/config splits ដែលត្រូវគ្នា និង signature ដូចគ្នា; ការលុប metadata មិនបង្កើត libraries ទេ។

ប្រភពនៅ `tools/simsimi/project` និង workflow នៅ `.github/workflows/build-simsimi-mpp.yml`។ ការកែ Hermes បដិសេធ bytecode ដែលមិនត្រូវ SHA-256 ដើម; Quick Return ក៏ពិនិត្យលេខ version/build និង native click handlers ដែរ។ ទិន្នន័យវិភាគនៅ `docs/simsimi/feature-gates.json`, `docs/simsimi/membership-targets.json` និង `docs/simsimi/quick-return-navigation.json`។ មិនបានបង្កើត SimSimi bundle release ថ្មី ហើយ bundle YouTube មិនបានផ្លាស់ប្ដូរ។
