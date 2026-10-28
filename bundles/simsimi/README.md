# SimSimi patches — កំណែសាកល្បង ដាច់ដោយឡែកពី YouTube

**Morphe bundle:** [`bundle.mpp`](bundle.mpp), **0.3.0-dev.1**, 53,855 bytes។ សម្រាប់ **SimSimi 9.2.3** (`com.ismaker.android.simsimi`, version code `1119001`, Android API 24+)។ នេះជា `.mpp` សម្រាប់ Morphe Manager មិនមែន Python APK patcher ទេ។ កុំយកវាទៅជំនួស `patch.mpp` របស់ YouTube។

**ស្ថានភាពសំខាន់៖** បានកែផ្លូវកូដក្នុងកម្មវិធីសម្រាប់មុខងារទាំង ៦ ខាងក្រោម ប៉ុន្តែ **មិនទាន់សាកល្បងកំណែថ្មីលើទូរសព្ទ ឬបញ្ជាក់ការអនុញ្ញាតពីម៉ាស៊ីនមេទេ**។ ជាពិសេស patch Items មិនផ្ដល់ stock ឬសិទ្ធិប្រើ Items គ្មានកំណត់នៅលើម៉ាស៊ីនមេឡើយ។

## របៀបសាកល្បង

1. Import `bundles/simsimi/bundle.mpp` ទៅ Morphe Manager ហើយជ្រើស APK ដើម SimSimi 9.2.3។ កុំប្រើ APK ដែលបាន patch រួចជាធាតុបញ្ចូលសម្រាប់ bundle នេះ។
2. ក្នុងបញ្ជី patches សូម **បើក selectors ទាំង ៦** ដែលមានពាក្យ `client only` ក្នុងតារាងខាងក្រោម៖ ពួកវា **បិទជាមុន**។ ពេលបើក selector ណាមួយ វាត្រូវការ `Unlock membership UI` ជា dependency។
3. Patch និងដំឡើងជាមួយ split APK ដែលត្រូវគ្នា បន្ទាប់មកសាកមុខងារម្ដងមួយៗ។ សម្រាប់រូបថត និង read receipt សូមផ្ទៀងផ្ទាត់ជាមួយអ្នកទទួលពិត មិនមើលតែ UI ខាងអ្នកទេ។
4. សម្រាប់ Items សូមប្រយ័ត្នប៊ូតុងទិញ៖ **ការទិញនៅតែអាចចំណាយ coins**។ ស្លាកថា unlimited នៅលើ UI មិនបញ្ជាក់ថាប្រើបានឥតគិតថ្លៃទេ។

<details>
<summary>SimSimi • 11 selectable experimental patches</summary>

| ឈ្មោះ patch ក្នុង Manager | លំនាំដើម | អ្វីដែលកែ និងដែនកំណត់ |
|---|---|---|
| Disable ad eligibility (experimental) | On | បិទ shared `canShowAds` gate; មិនទាន់បញ្ជាក់ថាលុប ads SDK ទាំងអស់។ |
| Unlock membership UI (client only, experimental) | On | ផ្ដល់ `hasMembership=true` ក្នុង client UI និង listener ដោយ clone ស្ថានភាព។ មិនបង្កើតការជាវ ឬសិទ្ធិនៅម៉ាស៊ីនមេ។ |
| Pull down to restart chat (experimental) | On | អូសចុះនៅបញ្ជី **Conversation ភាសាអង់គ្លេស** ប៉ុណ្ណោះ មិនមែនក្នុងបន្ទប់ឆាត។ វា reload React runtime ទាំងមូល មិនសម្លាប់ app និងមិនមែន refresh តែទិន្នន័យបញ្ជីទេ។ |
| MicroG RE service routing (experimental) | Off | ប្ដូរផ្លូវ native GMS ទៅ `app.revanced.android.gms`; ត្រូវដំឡើង MicroG RE ដាច់ដោយឡែក ហើយមិនមែន GMS support ពេញលេញ។ |
| Daily bonus without video (client path, experimental) | Off | ជ្រើសផ្លូវ membership ដែលមានស្រាប់ដោយមិនផ្ទុកវីដេអូ។ Server reward និង error នៅដដែល; មិនធានាការទទួលរង្វាន់។ |
| Conversation level controls (client only, experimental) | Off | ជ្រើស member branch ក្នុងសកម្មភាពប្ដូរ Freetalk level និងទុកសំណើរក្សាទុកកម្រិតទៅ server ដដែល។ មិនធានាប្រធានបទដែល server ផ្ដល់។ |
| Profile photo controls (client only, experimental) | Off | ជ្រើសផ្លូវបើក photo picker ជំនួសអេក្រង់ជាវ; ការផ្ទុក និងរក្សាទុករូបអាស្រ័យលើ server។ |
| Custom group cover controls (client only, experimental) | Off | បើក custom-cover picker និងប្រើ client membership flag ក្នុងទិន្នន័យ group។ មិនផ្ដល់ភាពជាម្ចាស់បន្ទប់ ឬសិទ្ធិ upload លើ server។ |
| Photo sending controls (client only, experimental) | Off | ជ្រើសផ្លូវផ្ញើរូបរបស់ member ទាំង direct និង group; ផ្លូវនេះអាចរំលង local quota/ad check។ មិនក្លែងការផ្ញើជោគជ័យ និងមិនប្ដូរច្បាប់ server ឬ moderation។ |
| Read receipt display (client only, experimental) | Off | បង្ហាញ indicator ដែលប្រើ `msgHasBeenRead` ដើម ជំនួសសញ្ញាសួររបស់ membership។ មិនបង្កើតទិន្នន័យថាបានអាន ប្រសិនបើ server មិនផ្ដល់។ |
| Membership item controls (client only, experimental) | Off | បង្ហាញ member item UI ដែលអាចមានស្លាក unlimited។ **មិនផ្ដល់ Items, coins, stock ឬធានាថា server អនុញ្ញាតឱ្យប្រើដោយឥតគិតថ្លៃ។** |

</details>

## ការផ្ទៀងផ្ទាត់

[Actions run 40658603472](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/40658603472) បាន៖

- Compile bundle និងដំណើរការ JVM tests លើ Hermes payload ដើម រួមទាំងការសាកល្បងបញ្ចូល patches រួមគ្នា និងបដិសេធ bytecode មិនស្គាល់។
- Decode instructions និងពិនិត្យថា feature branches ទៅផ្លូវដែលចង់បាន ដោយទុក read flag និងកូដប្រើ item នៅដដែល។
- អនុវត្ត `.mpp` ពិតលើ APK ដើមដោយ **Morphe Desktop v1.19.1** ជាមួយ selectors ថ្មីទាំង ៦ និង MicroG/daily bonus បើក។ Output Hermes ត្រូវគ្នានឹង payload ដែលបានតេស្ត; native reload hook និង MicroG visibility ត្រូវបានពិនិត្យ។
- **មិនបាន** សាកល្បង Android Manager UI, ការដំឡើង/runtime លើទូរសព្ទ, ឬ server entitlement។

Combined output Hermes SHA-256: `97bbf6a26444dd5755173800eae31579e972df1d1e54777d4dd68be7f7c89892`។ Bundle SHA-256: `5f1aca7743f2e8c68b0b7b13ed4470aaa855d1245dd4ef7c22ac27a475a88d87`។ ព័ត៌មានម៉ាស៊ីនតេស្តនៅ [`morphe-validation.json`](morphe-validation.json) និង [`build-status.json`](build-status.json)។

## APK splits និងការបង្កើត

APK ដើមដែលបានផ្ដល់ជា base APK មាន `splits.required=true` និងគ្មាន native libraries។ ការដំឡើងត្រូវមាន ABI/config splits ដែលត្រូវគ្នា; ការលុប metadata មិនបង្កើត libraries ទេ។

ប្រភពនៅ `tools/simsimi/project` និង workflow នៅ `.github/workflows/build-simsimi-mpp.yml`។ Bytecode កំណែដែលមិនត្រូវ SHA-256 ដើមនឹងត្រូវបដិសេធ។ ទិន្នន័យវិភាគនៅ `docs/simsimi/feature-gates.json` និង `docs/simsimi/membership-targets.json`។ គ្មាន SimSimi release ត្រូវបានចេញ ហើយ bundle YouTube មិនបានផ្លាស់ប្ដូរ។
