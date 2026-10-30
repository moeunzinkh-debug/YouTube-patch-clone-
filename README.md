# YouTube Patch Clone (unofficial source subset)

This repository contains a **YouTube-focused source subset** of [MorpheApp/morphe-patches](https://github.com/MorpheApp/morphe-patches), with an additional Khmer voice-over TTS integration. It is a patch-source project, **not** a YouTube app or a ready-to-install APK.

> **Scope:** the compiled `patch.mpp` contains **only the YouTube patch set**. Shared support code is retained where the YouTube patches need it; the separate YouTube Music and Reddit patch sets are not included.
>
> កំណត់សម្គាល់៖ យកតែផ្នែក YouTube ប៉ុណ្ណោះ។ ឯកសារ shared ដែលចាំបាច់សម្រាប់ YouTube នៅតែមាន ប៉ុន្តែមិនបានដាក់ patch set របស់ YouTube Music ឬ Reddit ទេ។

[![Release](https://img.shields.io/badge/release-v1.49.0-e4313c?logo=github)](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/tag/v1.49.0)
[![patch.mpp](https://img.shields.io/badge/patch.mpp-9.8%20MiB-3157d5)](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/download/v1.49.0/patch.mpp)
[![YouTube stable](https://img.shields.io/badge/YouTube%20stable-21.23.492-14835b)](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/tree/youtube-21.23.492)
[![YouTube latest](https://img.shields.io/badge/YouTube%20latest-21.42.241-a8650b)](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/tree/youtube-21.42.241)
[![Upstream](https://img.shields.io/badge/upstream-v1.48.0-6a7290)](https://github.com/MorpheApp/morphe-patches/releases/tag/v1.48.0)
[![License](https://img.shields.io/badge/license-GPLv3-blue)](LICENSE)

[![Build patch.mpp](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/workflows/build-mpp.yml/badge.svg)](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/workflows/build-mpp.yml)
[![Verify patch.mpp](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/workflows/verify-mpp.yml/badge.svg)](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/workflows/verify-mpp.yml)
[![Release patch.mpp](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/workflows/release-mpp.yml/badge.svg)](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/workflows/release-mpp.yml)

<details>
<summary>🌙 Kimi AI • 1 experimental patch (bundle ដាច់ដោយឡែក)</summary>

កំណែដែលបានពិនិត្យ៖ `com.moonshot.kimichat` **3.1.5 (381)**, Android 8.0+ និង arm64។

- `Remove license check` — រារាំងចំណុចចាប់ផ្ដើម PairIP license check ពីរ **ខាង client**; បើកជាមុន។ វាមិនផ្ដល់ subscription ឬផ្លាស់ប្ដូរការផ្ទៀងផ្ទាត់ខាង server ទេ ហើយការដំណើរការជាក់ស្ដែងមិនទាន់បញ្ជាក់ទេ។

Morphe Manager 2.3.0-dev.3 បានរួម និង patch `.apks` នេះក្នុង Android emulator; DEX លទ្ធផលត្រូវបានពិនិត្យ។ App ផ្ទាល់មិនបានដំឡើង ឬបើកទេ។ [លទ្ធផល Manager](bundles/kimi/manager-smoke.json)។

[ទាញយក Kimi `bundle.mpp` ពី Release](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/download/Kimi/bundle.mpp) · [ច្បាប់ចម្លងក្នុង repository](bundles/kimi/bundle.mpp) · [របៀបប្រើ និងលទ្ធផលតេស្ត](bundles/kimi/README.md) · [SHA-256](bundles/kimi/bundle.mpp.sha256)

**ប្រយ័ត្ន៖** `.apks` នៅ Release `Kimi` មានហត្ថលេខា Android test key សាធារណៈ មិនអាចបញ្ជាក់ថាជា APK ផ្លូវការ ឬមានសុវត្ថិភាពបានទេ។ កុំបញ្ចូលពាក្យសម្ងាត់ ឬទិន្នន័យឯកជនក្នុង APK ដែលមិនទាន់ទុកចិត្ត។

</details>

<!-- GBOARD-PATCH-LIST:START -->
<a id="gboard-patches"></a>
<details>
<summary>⌨️ Gboard • 43 patches (bundle ដាច់ដោយឡែក)</summary>

ប្រភព៖ [jasonwu1994/Gboard-patches v4.0.0](https://github.com/jasonwu1994/Gboard-patches/releases/tag/v4.0.0)។
Bundle នេះគឺជាច្បាប់ចម្លងឯកសារ `.mpp` របស់ upstream ដោយមិនកែប្រែ; វា **មិនមែន** `patch.mpp` របស់ YouTube ទេ។

គោលដៅដែល upstream រាយ៖ `com.google.android.inputmethod.latin` កំណែ
`18.5.4.993608717-release-arm64-v8a` ប៉ុណ្ណោះ។ Patches ទាំង 43 ត្រូវបានជ្រើសជាមុនក្នុង upstream;
នេះមិនមានន័យថាមុខងារបណ្ដាញទាំងអស់ចាប់ផ្ដើមដោយស្វ័យប្រវត្តិទេ។ ពិនិត្យជម្រើសមុន patch។

[ទាញយក Gboard bundle](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/tag/Gboard-v4.0.0) ·
[ការដំឡើង សុវត្ថិភាព និងកម្រិតកំណត់](bundles/gboard/README.md) ·
[Source និងអាជ្ញាបណ្ណ](extras/gboard-patches/)

<details>
<summary>⌨️ ការវាយអក្សរ ភាសា និងឧបករណ៍ • 18</summary>

- `AI Writing Tools` — បង្ហាញឧបករណ៍សរសេរ AI។ Upstream កំណត់ឲ្យគាំទ្រគ្រប់ភាសា ប៉ុន្តែភាសាខ្មែរមិនទាន់បានសាកល្បងនៅទីនេះទេ។
- `Advanced Voice Typing` — បើកការវាយដោយសំឡេងកម្រិតខ្ពស់ និងសញ្ញាវណ្ណយុត្តិស្វ័យប្រវត្តិតាមការគាំទ្ររបស់ Gboard។
- `Custom Symbols` — បន្ថែមផ្ទាំងនិមិត្តសញ្ញាផ្ទាល់ខ្លួន និងផ្លូវកាត់ពីការចុចក្បៀសឲ្យយូរ។
- `Enable Inline Autofill Suggestions` — បើកការណែនាំបំពេញទិន្នន័យដោយស្វ័យប្រវត្តិក្នុងបរិបទដែលគាំទ្រ។
- `Enable cursor trackpad mode` — ចុច spacebar ឲ្យយូរ ដើម្បីប្រើរបៀបបញ្ជាទីតាំងទស្សន៍ទ្រនិច។
- `English QWERTY Up-Flick Uppercase` — លើក្តារចុច QWERTY អង់គ្លេស អូសឡើងដើម្បីប្ដូរអក្សរធំ និងតូច។
- `Grammar Checker` — បើកជម្រើសពិនិត្យវេយ្យាករណ៍ក្នុងការកែអត្ថបទ។
- `Inline Suggestions` — បើកជម្រើស Smart Compose ក្នុងការកែអត្ថបទ។
- `Latin Globe Key Ignore Interval` — កំណត់រយៈពេលរង់ចាំប៊ូតុងផ្លាស់ប្ដូរភាសាលើក្តារចុចអង់គ្លេស។
- `Long-Press Editing Shortcuts` — បន្ថែមផ្លូវកាត់ចុចឲ្យយូរសម្រាប់ជ្រើសទាំងអស់ ធ្វើវិញ ថតចម្លង កាត់ និងបិទភ្ជាប់លើ QWERTY អង់គ្លេស និង Zhuyin។
- `Quick Insert` — បើកផ្ទាំងបញ្ចូលរហ័ស និងប៊ូតុងក្នុង toolbar។
- `Simple Calculator` — បង្ហាញលទ្ធផលគណនាពីកន្សោមដែលវាយក្នុងជួរណែនាំ។
- `Swipeable Custom Top Row` — អូសជួរខាងលើដើម្បីប្ដូរទៅជួរអត្ថបទ ឬ JavaScript ផ្ទាល់ខ្លួន។ ប្រើតែកូដដែលទុកចិត្ត។
- `Toolbar Editing Buttons` — បន្ថែមប៊ូតុងជ្រើសទាំងអស់ ថតចម្លង កាត់ និងបិទភ្ជាប់ទៅម៉ឺនុយ។
- `Use Bluetooth Microphone` — បើកជម្រើសប្រើមីក្រូហ្វូន Bluetooth សម្រាប់វាយដោយសំឡេង។
- `Zhuyin Bottom Row Key Sizes` — កែទំហំប៊ូតុងជួរខាងក្រោមនៃក្តារចុច Zhuyin។
- `Zhuyin Quick Traditional/Simplified Toggle` — អូសឡើងលើប៊ូតុង Zhuyin ㄥ ដើម្បីប្ដូរអក្សរចិនបុរាណ និងសាមញ្ញ។
- `Zhuyin Slide Input` — បើកការអូសឡើង និងចុះសម្រាប់ក្តារចុច Zhuyin។

</details>

<details>
<summary>🔐 Clipboard បណ្ដាញ និង package • 8</summary>

- `Add Gboard Signature Bypass` — រំលងការត្រួតពិនិត្យបញ្ជីហត្ថលេខាខាងក្នុង Gboard; មិនរំលងការត្រួតពិនិត្យហត្ថលេខាដំឡើងរបស់ Android ទេ។
- `Clipboard Custom Character Limit` — កំណត់ចំនួនតួអក្សរអតិបរមាក្នុងធាតុ clipboard នីមួយៗ។
- `Clipboard Enhancements` — កែរយៈពេលរក្សាទុក ចំនួនធាតុ ការបង្ហាញពេលវេលា និងទម្រង់ clipboard។
- `FTP Server` — បន្ថែមម៉ាស៊ីន FTP លើបណ្ដាញក្នុងស្រុក សម្រាប់មើល និងផ្ទេរឯកសារ។ កំណត់ការចូល និងពាក្យសម្ងាត់ឲ្យប្រុងប្រយ័ត្ន។
- `Floating Web Search` — បើកទំព័របណ្ដែតពី Gboard សម្រាប់ស្វែងរកតាមវេបសាយ។
- `Incognito Mode Toggle` — បន្ថែមប៊ូតុងប្ដូររបៀបអនាមិក និងការកំណត់ clipboard/សំឡេងក្នុងរបៀបនោះ។
- `Package Rename` — ប្ដូរ package ទៅ dev.jason.com.google.android.inputmethod.latin និងអាចកំណត់ឈ្មោះ app ដើម្បីដំឡើងក្បែរច្បាប់ដើម។
- `Web Clipboard` — បន្ថែម clipboard តាម browser ក្នុង LAN ដោយមានកូដភ្ជាប់ និង Quick Settings Tile ជាជម្រើស។

</details>

<details>
<summary>🎨 រូបរាង ប្លង់ និង toolbar • 14</summary>

- `Access Points menu style` — ប្ដូររចនាប័ទ្មម៉ឺនុយ Access Points ថ្មី ឬចាស់។
- `Change emoji size` — កែទំហំ emoji។
- `Close Proactive Suggestions` — បង្ហាញប៊ូតុងបិទនៅលើជួរការណែនាំ។
- `Custom Theme` — នាំចូលស្បែក ZIP ផ្ទាល់ខ្លួន ឬស្បែកពីឃ្លាំង Rboard។
- `Emojis, stickers & GIFs Tab Order` — អូសរៀបលំដាប់ផ្ទាំង emoji, sticker និង GIF។
- `Enable accessibility layout` — បើកប្លង់ក្តារចុចសម្រាប់ភាពងាយស្រួលប្រើប្រាស់។
- `Enable split keyboard` — បើកប្លង់ក្តារចុចបំបែកពីរផ្នែក។
- `Frosted Glass` — បន្ថែមផ្ទៃព្រិល និងតម្លាភាពស្បែក; ត្រូវការ Android 12+ និងឧបករណ៍គាំទ្រ cross-window blur។
- `G Logo on Spacebar` — បង្ហាញរូប G លើ spacebar ជំនួសស្លាកឈ្មោះភាសា។
- `Key Shape Selection` — បើកជម្រើសរូបរាងប៊ូតុងក្នុងព័ត៌មានស្បែក។
- `Rounded Keyboard Panel` — កំណត់ជ្រុងមូល និងកម្រិតមូលខាងលើ/ក្រោមនៃផ្ទាំងក្តារចុច។
- `Settings Homepage Override` — ប្ដូរទំព័រកំណត់ Gboard រវាងរចនាប័ទ្មថ្មី និងចាស់។
- `Swipe Down to Dismiss Keyboard` — អូសចុះពីជួរការណែនាំ ឬ toolbar ដើម្បីបិទក្តារចុច។
- `Top Toolbar Item Count` — កំណត់ចំនួនធាតុក្នុង toolbar ខាងលើ។

</details>

<details>
<summary>🧰 បម្រុងទុក កំណត់កម្រិតខ្ពស់ និង OCR • 3</summary>

- `Backup & Restore` — នាំចេញ និងស្ដារការកំណត់ patches ព្រមទាំងបម្រុងទុក ប្រៀបធៀប ឬស្ដារ Gboard PB/XML flags។
- `Developer options` — បើក Developer options និង Flag Editor សម្រាប់កែ flags។
- `Enable OCR / Scan Text` — បើកស្កែនអក្សរសម្រាប់ Latin, ចិន, ជប៉ុន, កូរ៉េ និង Devanagari; upstream មិនបានរាយភាសាខ្មែរទេ។

</details>

**សុវត្ថិភាព៖** FTP, Web Clipboard, JavaScript និង signature bypass មានផលប៉ះពាល់លើសុវត្ថិភាព/ទិន្នន័យ;
ដកជម្រើសដែលមិនត្រូវការ និងប្រើតែនៅក្នុងបណ្ដាញដែលទុកចិត្ត។ រក្សាក្តារចុចមួយផ្សេងទៀតទុកជាបម្រុង។
OCR មិនរាយភាសាខ្មែរ ហើយមុខងារភាសាខ្មែរមិនត្រូវបានផ្ទៀងផ្ទាត់នៅទីនេះទេ។

</details>
<!-- GBOARD-PATCH-LIST:END -->

<details>
<summary>✈️ Telegram • 15 patches (bundle ដាច់ដោយឡែក)</summary>

ប្រភព៖ [rushiranpise/morphe-patches v1.23.1](https://github.com/rushiranpise/morphe-patches/releases/tag/v1.23.1)។
នេះជា bundle ដែល build ឡើងវិញពី **Telegram subset ប៉ុណ្ណោះ** មិនមែន upstream bundle ដែលមាន app ផ្សេងៗទេ។
[GitHub Release (pre-release)](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/tag/Telegram-v1.23.1-tg.1) · [ទាញយក `bundle.mpp` ពី repository](bundles/telegram/bundle.mpp) · [របៀបប្រើ និងការព្រមាន](bundles/telegram/README.md) · [ប្រភព/អាជ្ញាបណ្ណ](docs/telegram/upstream.md)

កំណែដែល upstream រាយ៖ Telegram `org.telegram.messenger` **12.10.1 (70382)**, Telegram Web Android package `org.telegram.messenger.web` **12.10.1 (70389)** និង Telegram Plus `org.telegram.plus` **12.10.1.1 (22510)**។ Telegram និង Telegram Web មាន 14 selectors; `Disable analytics` បន្ថែមសម្រាប់ Telegram Plus ប៉ុណ្ណោះ។ **Selectors ទាំងអស់បើកជាមុន** ដូច upstream; ពិនិត្យ និងដកអ្វីដែលមិនចង់ប្រើមុន patch។

Morphe Desktop បាន patch និង rebuild APK Telegram Web 12.10.1 ដែលផ្ទៀងផ្ទាត់ហត្ថលេខាដើមរួច ដោយជ្រើស `Remove ads` តែមួយ និងជ្រើសទាំង 14 ដាច់ដោយឡែក។ APK ទាំងពីរ (test-signed) ក៏បានបើកនៅ Android 15 emulator ដោយគ្មានគណនី ប៉ុន្តែមិនទាន់សាកមុខងារជាក់ស្ដែងទេ។ Telegram ដើម និង Plus មិនទាន់សាក patch ជាមួយ APK នៅទីនេះទេ; សូមមើល [លទ្ធផល Desktop](bundles/telegram/validation.json) និង [emulator](bundles/telegram/android-smoke.json)។

- `Anti-delete messages` — ព្យាយាមរក្សាសារដែលអ្នកផ្សេងលុបនៅក្នុងឧបករណ៍។
- `Anti-disappearing media` — ព្យាយាមរក្សា view-once media; ប៉ះពាល់ឯកជនភាព និងផ្លូវផ្ទុក secret media។
- `Anti-screenshot notification` — ព្យាយាមមិនផ្ញើការជូនដំណឹង screenshot។
- `Bypass channel restrictions` — ព្យាយាមរំលងការកំណត់មាតិកា channel ខាង app។
- `Bypass content restrictions` — ព្យាយាមអនុញ្ញាត save/forward ដែល client ទប់។
- `Bypass integrity check` — spoof លទ្ធផលត្រួតពិនិត្យខាង app; មិនធានា login ឬ hardware/server attestation។
- `Disable analytics` — ទប់ analytics ខ្លះក្នុង Telegram Plus ប៉ុណ្ណោះ; push មិនទាន់បញ្ជាក់។
- `Disable auto-update` — ទប់ការឆែក update របស់ app; ត្រូវតាមដាន security updates ដោយខ្លួនឯង។
- `Disable channel switching` — បិទ gesture ប្ដូរទៅ channel បន្ទាប់។
- `Download speed boost` — ប្ដូរប៉ារ៉ាម៉ែត្រទាញយក; ល្បឿនពិតមិនត្រូវបានធានា។
- `Hide typing indicator` — ព្យាយាមលាក់សញ្ញាកំពុងវាយ។
- `Remove ads` — ព្យាយាមទប់ sponsored messages និង video ads។
- `Unlock Premium` — ប្ដូរតែការត្រួតពិនិត្យក្នុង client; **មិនបង្កើត Telegram Premium subscription ឬសិទ្ធិលើ server**។
- `Use normal paste` — ប្រើ paste ធម្មតាជំនួស Rich HTML paste។
- `Voice to music` — ព្យាយាមចាក់ voice note ក្នុង music player; ក៏អាចប៉ះពាល់ voice-once ផងដែរ។

**ប្រយ័ត្ន៖** ការរក្សាសារ/view-once និងការលាក់ screenshot notification អាចប៉ះពាល់ឯកជនភាពរបស់អ្នកដទៃ។ Patching/signing ជាទូទៅប្រើ key ខុសពី app ដើម; កុំលុប app ដើមដោយមិនត្រៀមទិន្នន័យ ព្រោះ Secret Chats និងទិន្នន័យក្នុងឧបករណ៍អាចបាត់។ [ស្ថានភាពសាកល្បង](bundles/telegram/validation.json) រាយអ្វីដែលបាន និងមិនបានសាក។

</details>

<details>
<summary>🗨️ SimSimi • 12 experimental patches (separate bundle)</summary>

For **SimSimi 9.2.3**, import [`bundles/simsimi/bundle.mpp`](bundles/simsimi/bundle.mpp)
into Morphe Manager. This bundle is separate from YouTube `patch.mpp`.

- **Disable ad eligibility (experimental)** — shared ad gate, not proven complete SDK removal.
- **Unlock membership UI (client only, experimental)** — client UI status only, not a server subscription.
- **Pull down to restart chat (experimental)** — English Conversation list only, not inside chat rooms; requests React runtime reload.
- **Quick return: double-tap Chat (experimental)** — opt-in; double-tap the selected bottom Chat tab to scroll the English Conversation list to the top, without reloading. Normal tab clicks continue unchanged.
- **Daily bonus without video (client path, experimental)** — opt-in existing non-video flow; server reward is not guaranteed.
- **MicroG RE service routing (experimental)** — opt-in native routing, not full GMS compatibility. It does not fix FCM push; the inspected RE 7.3.0-dev.2 APK has action/permission mismatches ([diagnosis](docs/simsimi/huawei-notifications.md)).
- **Conversation level controls (client only, experimental)** — opt-in member slider path; server level/topic handling remains authoritative.
- **Profile photo controls (client only, experimental)** — opt-in profile picker path; server upload still required.
- **Custom group cover controls (client only, experimental)** — opt-in cover picker; no group ownership or server upload rights are granted.
- **Photo sending controls (client only, experimental)** — opt-in existing direct/group member send paths; server limits and moderation still apply.
- **Read receipt display (client only, experimental)** — opt-in display of the real supplied read flag; no receipt is fabricated.
- **Membership item controls (client only, experimental)** — opt-in member UI only; does **not** grant free or unlimited server items, even if the UI says unlimited.

Quick Return is **off by default** and independent of Pull Refresh. The six individual
membership feature patches are also off by default and require the membership UI patch.
The actual `.mpp` was applied to the original APK using Morphe Desktop; Quick Return was
checked both alone and together with Pull Refresh
([CI proof](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/40799144878)).
**Quick Return and the six membership features have not been device-tested; server acceptance is unverified.**
Matching, identically signed splits are required for installation. See the
[full catalog and limitations](bundles/simsimi/README.md). No new SimSimi bundle release was published.

</details>

<!-- PATCH-LIST:START -->
<details>
<summary>📦 YouTube • 106 patches</summary>

### YouTube Patches

និយាយពីអ្វីដែលមាននៅក្នុង patches ទាំងអស់ / What is inside the whole patch bundle. បញ្ជីពេញខាងក្រោមគឺ 111 patches ពី [`patches-list.json`](patches-list.json) v1.49.0 (106 កំណត់គោលដៅ `com.google.android.youtube` + 5 shared/generic)។

**ឧទាហរណ៍ / Highlights**

- Remove Ads
- Background Playback
- Hide Shorts
- Custom Theme

ទាំងនេះត្រូវគ្នាជាមួយ `Hide ads`, `Remove background playback restrictions`, `Hide Shorts components` និង `Theme`។ ក្រៅពីនោះនៅមាន SponsorBlock, Return YouTube Dislike, DeArrow, Picture-in-Picture, Playback speed, Video quality, Loop video, Swipe controls, Seekbar, Downloads, Save to Watch later, Copy/share links, Spoof app version/signature, GmsCore support និង **Voice over translation** (Khmer TTS) ជាដើម។

បើកក្រុមខាងក្រោមដើម្បីមើលគ្រប់ patch / Expand a group to see every patch name:

<details>
<summary>✨ ថ្មីពី v1.48.0 / New in v1.48.0 • 9</summary>

- `Ask flyout menu`
- `Custom font`
- `Feed card layout`
- `Feed video actions`
- `Feed view count`
- `Force animations`
- `Series tracking`
- `Skip live Shorts`
- `Video delay`

</details>

<details>
<summary>🚫 ពាណិជ្ជកម្ម & ការរំខាន / Ads & distractions • 20</summary>

- `AI channel filter`
- `Channel whitelist`
- `DeArrow`
- `Hide ads`
- `Hide autoplay preview`
- `Hide end screen cards`
- `Hide end screen suggested video`
- `Hide info cards`
- `Hide layout components`
- `Hide player flyout menu components`
- `Hide player overlay buttons`
- `Hide related video overlay`
- `Hide related videos`
- `Hide status bar`
- `Hide timestamp`
- `Hide video action buttons`
- `Remove viewer discretion dialog`
- `Restore original titles`
- `Return YouTube Dislike`
- `SponsorBlock`

</details>

<details>
<summary>▶️ ការចាក់វីដេអូ / Playback & video • 23</summary>

- `Audio equalizer`
- `Captions`
- `Double tap to seek`
- `Exit fullscreen mode`
- `Force fullscreen landscape`
- `Force original audio`
- `Fullscreen video scale`
- `Loop video`
- `Media notification controls`
- `Miniplayer`
- `Mute button`
- `Open videos fullscreen`
- `Picture-in-picture button`
- `Play all`
- `Playback buffer`
- `Playback in feeds`
- `Playback speed`
- `Reload video`
- `Remember live stream playback position`
- `Remove background playback restrictions`
- `Seekbar`
- `Skip silence`
- `Video quality`

</details>

<details>
<summary>📱 Shorts • 5</summary>

- `Disable Shorts resuming on startup`
- `Hide Shorts components`
- `Open Shorts in regular player`
- `Shorts autoplay`
- `Shorts icon style`

</details>

<details>
<summary>🎨 រូបរាង & អេក្រង់ / Theme, layout & player UI • 14</summary>

- `Ambient mode`
- `App refresh rate`
- `Change form factor`
- `Change header`
- `Change start page`
- `Custom branding`
- `Custom player overlay opacity`
- `Navigation bar`
- `Override YouTube Music buttons`
- `Player icon style`
- `Settings menu filter`
- `Swipe controls`
- `Theme`
- `Wide search bar`

</details>

<details>
<summary>⚙️ បិទ/បើកមុខងារ / Behaviour toggles • 15</summary>

- `Disable auto feed refresh`
- `Disable continue watching prompt`
- `Disable double tap actions`
- `Disable DRC audio`
- `Disable fullscreen gestures`
- `Disable haptic feedback`
- `Disable layout updates`
- `Disable Play Store updates`
- `Disable player popup panels`
- `Disable playlist autoplay`
- `Disable QUIC protocol`
- `Disable rolling number animations`
- `Disable scrolling speed limit`
- `Disable sign in to TV popup`
- `Disable video codecs`

</details>

<details>
<summary>🌐 បណ្តាញ & គណនី / Network, spoofing & account • 13</summary>

- `Bypass image region restrictions`
- `Bypass link redirects`
- `Change installer source`
- `Check watch history domain name resolution`
- `Enable debugging`
- `GmsCore support`
- `Network proxy`
- `Override certificate pinning`
- `PoToken provider`
- `Spoof app version`
- `Spoof device dimensions`
- `Spoof signature`
- `Spoof video streams`

</details>

<details>
<summary>🧰 ចែករំលែក & ឧបករណ៍ / Sharing & tools • 12</summary>

- `Add to queue`
- `Channel search`
- `Clone app`
- `Copy text`
- `Copy video link`
- `Downloads`
- `Open channel of live avatar`
- `Open links externally`
- `Open system share sheet`
- `Sanitize sharing links`
- `Save to Watch later`
- `Voice over translation`

</details>

> ចំណាំ៖ ក្រុម «ថ្មីពី v1.48.0» គឺជា patches ដែលបានបន្ថែមពី upstream v1.48.0។ ស្លាក `youtube-*` មិនបន្ថែម patch ថ្មីទេ — ការបន្ថែមកំណែ YouTube ថ្មីត្រូវការ sync កូដ patch ពី upstream មុន។

</details>
<!-- PATCH-LIST:END -->

## Upstream sync / ការធ្វើបច្ចុប្បន្នភាពពី upstream

This fork is synced to the **YouTube-only source of upstream v1.48.0** (bundle release `v1.49.0`) and includes the **9 new YouTube patches** (Ask flyout menu, Custom font, Feed card layout, Feed video actions, Feed view count, Force animations, Series tracking, Skip live Shorts, Video delay) — see the «New in v1.48.0» group above. Those 9 are the net new features; to compile them the shared YouTube patch/extension sources had to be aligned with v1.48.0 (morphe-patcher 2.0.0), while our Khmer TTS package, Khmer strings, YouTube-only resource checker and fork metadata were preserved. **No YouTube Music or Reddit patches are included.** See [`docs/upstream-sync.md`](docs/upstream-sync.md) for the full comparison, the v1.49.0-dev.7 additions and the supported YouTube versions. **Recommended YouTube target: `21.23.492`** — the same as upstream (Manager recommends the newest non-experimental target; `21.23.492` was promoted to stable upstream in v1.49.0-dev.7).

## New: in-app Audio equalizer (v1.48.2)

The branch's [`patch.mpp`](patch.mpp) includes **Audio equalizer** with device-supported
band sliders, hardware presets, enable/disable and reset to flat. Select the patch,
then open **Morphe settings → Video → Audio equalizer** while a video is playing.
Settings persist across sessions; unsupported audio engines show a status instead
of intentionally stopping playback. It does not process remote/cast audio.

[EQ usage and limitations](docs/youtube-equalizer.md). CI compilation and controller
tests passed; APK/device listening tests remain pending. Release badges and the source descriptor point to **1.49.0**. Refresh your patch
source in Manager or import the release bundle to use EQ.

## v1.49.0: player EQ shortcut and SEA-LION

- Top-player EQ shortcut near CC/settings, using native relative control layout; opens the existing in-app EQ dialog.
- New SEA-LION translation provider: `https://api.sea-lion.ai/v1/`, model `aisingapore/Gemma-SEA-LION-v4-27B-IT`, with a separate masked API-key field.
- Existing translation providers remain available. Exported settings can contain API keys; do not share them.
- Android compilation and offline tests verified; live SEA-LION calls and device layout/spacing remain to be verified.
- Recommended YouTube remains **21.23.492**. This is a fork release, not a claim of a new upstream sync.

See [SEA-LION setup](docs/youtube-sealion-translation.md) and [release notes](docs/releases/v1.49.0.md).
