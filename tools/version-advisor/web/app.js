/* YouTube Version Advisor — bilingual UI (no dependencies, same-origin API). */
(() => {
  "use strict";

  const T = {
    en: {
      appTitle: "YouTube Version Advisor",
      appSubtitle: "Automatic version updates · matched to your phone model",
      checking: "Checking…",
      updateTitle: "Newer YouTube versions are available upstream",
      refreshNow: "Update now",
      phoneTitle: "Phone profile",
      phoneSubtitle: "Detected automatically, or choose a model manually",
      detectBtn: "Auto-detect",
      modelLabel: "Phone model / model code",
      modelPlaceholder: "Galaxy A54 5G, SM-A546B, Redmi Note 12…",
      androidLabel: "Android version",
      densityLabel: "Screen density",
      channelLabel: "Version source",
      channelLocal: "This repository (safe)",
      channelUpstream: "Latest upstream",
      analyzeBtn: "Analyze now",
      refreshBtn: "Check for new versions",
      privacy: "Device data is analyzed locally and is never sent to Google. Results are estimates — confirm the real Android version on your phone.",
      resultTitle: "Recommendation",
      resultSubtitle: "The YouTube version that best fits this phone",
      recommended: "Recommended YouTube version",
      minAndroid: "Min Android",
      patchBundle: "Patch bundle",
      stable: "Stable",
      experimental: "Experimental",
      whyTitle: "Why this version",
      newestLabel: "Newest compatible",
      compatibilityLabel: "Compatible versions",
      apkTitle: "Which APK to download",
      notesTitle: "Notes",
      noCompatible: "No supported YouTube version can run on this phone.",
      allVersionsTitle: "All supported versions",
      allVersionsSubtitle: "Compared against the SDK level of your device",
      colVersion: "YouTube",
      colStatus: "Status",
      colMin: "Min Android",
      colSdk: "SDK",
      colMatch: "Compatible",
      colScore: "Score",
      catalogTitle: "Automatically updated version catalog",
      catalogSubtitle: "Built from this repo's patches-list.json and the upstream Morphe patch bundle via the GitHub API",
      checkUpstream: "Check upstream",
      localChannel: "This repository",
      upstreamChannel: "Latest upstream",
      changesTitle: "What changed",
      catalogNote: "Note: the tool updates the version catalog only. Adding a new target to the real patches requires syncing the Kotlin patch sources from upstream first.",
      footerLine: "Unofficial project — not affiliated with Google, YouTube or MorpheApp.",
      yes: "yes", no: "no", android: "Android", sdk: "SDK", patches: "patches", versions: "versions",
      detectedAs: "Detected", demoProfile: "Example profile", demoHint: "Auto-detection needs an Android phone browser. Showing a sample device — pick your model above.",
      detectedHint: "Model detected from this browser. You can override any field.",
      selectHint: "Selected from the device database. All fields can be overridden.",
      typedHint: "Free-text model — enter the Android version and SDK below for an accurate result.",
      modelSelected: "Selected",
      compatibleSummary: "{n} of {total} versions compatible",
      refreshed: "Catalog refreshed",
      noChanges: "Catalog is already up to date",
      refreshFailed: "Could not reach upstream — showing the last known catalog",
      refreshing: "Refreshing…",
      autoChecked: "auto · checked {time}",
      lastChecked: "Last checked",
      added: "new", removed: "dropped", modified: "changed", inRepo: "in repo", needsSync: "needs sync",
      noChangesShort: "No differences", backendError: "Server error — please try again",
      score: "score", demoTag: "sample", sourceDatabase: "database", sourceUA: "browser", sourceManual: "manual", sourceAdb: "adb",
    },
    km: {
      appTitle: "អ្នកណែនាំកំណែ YouTube",
      appSubtitle: "ធ្វើបច្ចុប្បន្នភាពដោយស្វ័យប្រវត្តិ · វិភាគតាមម៉ូដែលទូរសព្ទ",
      checking: "កំពុងពិនិត្យ…",
      updateTitle: "មានកំណែ YouTube ថ្មីៗនៅ upstream",
      refreshNow: "ធ្វើបច្ចុប្បន្នភាពឥឡូវ",
      phoneTitle: "ព័ត៌មានទូរសព្ទ",
      phoneSubtitle: "រកឃើញដោយស្វ័យប្រវត្តិ ឬជ្រើសម៉ូដែលដោយដៃ",
      detectBtn: "រកឃើញស្វ័យប្រវត្តិ",
      modelLabel: "ម៉ូដែលទូរសព្ទ / លេខកូដម៉ូដែល",
      modelPlaceholder: "Galaxy A54 5G, SM-A546B, Redmi Note 12…",
      androidLabel: "កំណែ Android",
      densityLabel: "ដង់ស៊ីតេអេក្រង់",
      channelLabel: "ប្រភពកំណែ",
      channelLocal: "Repository នេះ (មានសុវត្ថិភាព)",
      channelUpstream: "Upstream ចុងក្រោយ",
      analyzeBtn: "វិភាគឥឡូវ",
      refreshBtn: "ពិនិត្យកំណែថ្មី",
      privacy: "ព័ត៌មានឧបករណ៍ត្រូវបានវិភាគក្នុងម៉ាស៊ីនមេខ្លួនឯង មិនបានផ្ញើទៅ Google ទេ។ លទ្ធផលជាការប៉ាន់ស្មាន — សូមពិនិត្យកំណែ Android ពិតប្រាកដ។",
      resultTitle: "លទ្ធផលវិភាគ",
      resultSubtitle: "កំណែដែលសាកសមបំផុតសម្រាប់ទូរសព្ទរបស់អ្នក",
      recommended: "កំណែ YouTube ដែលណែនាំ",
      minAndroid: "Android អប្បបរមា",
      patchBundle: "កញ្ចប់ patch",
      stable: "ស្ថិរភាព",
      experimental: "ពិសោធន៍",
      whyTitle: "ហេតុអ្វីបានជាកំណែនេះ",
      newestLabel: "ថ្មីបំផុតដែលឆបគ្នា",
      compatibilityLabel: "កំណែដែលឆបគ្នា",
      apkTitle: "គួរទាញយក APK មួយណា",
      notesTitle: "កំណត់ចំណាំ",
      noCompatible: "គ្មានកំណែ YouTube ណាដែលគាំទ្រអាចដំណើរការលើទូរសព្ទនេះទេ។",
      allVersionsTitle: "កំណែដែលគាំទ្រទាំងអស់",
      allVersionsSubtitle: "ប្រៀបធៀបជាមួយកម្រិត SDK របស់ឧបករណ៍អ្នក",
      colVersion: "YouTube",
      colStatus: "ស្ថានភាព",
      colMin: "Android អប្បបរមា",
      colSdk: "SDK",
      colMatch: "ឆបគ្នា",
      colScore: "ពិន្ទុ",
      catalogTitle: "បញ្ជីកំណែដែលបានធ្វើបច្ចុប្បន្នភាពដោយស្វ័យប្រវត្តិ",
      catalogSubtitle: "ទាញចេញពី patches-list.json ក្នុង repository និងកញ្ចប់ patch របស់ Morphe តាម GitHub API",
      checkUpstream: "ពិនិត្យ upstream",
      localChannel: "Repository នេះ",
      upstreamChannel: "Upstream ចុងក្រោយ",
      changesTitle: "អ្វីដែលផ្លាស់ប្តូរ",
      catalogNote: "ចំណាំ៖ ឧបករណ៍នេះធ្វើបច្ចុប្បន្នភាពតែ «បញ្ជីកំណែ» ប៉ុណ្ណោះ។ ការបន្ថែមកំណែថ្មីទៅក្នុង patch ពិតប្រាកដ ត្រូវការ synchronize កូដ Kotlin ពី upstream ជាមុនសិន។",
      footerLine: "គម្រោងឯករាជ្យ — មិនពាក់ព័ន្ធនឹង Google, YouTube ឬ MorpheApp ទេ។",
      yes: "បាទ", no: "ទេ", android: "Android", sdk: "SDK", patches: "patch", versions: "កំណែ",
      detectedAs: "បានរកឃើញ", demoProfile: "ទម្រង់គំរូ", demoHint: "ការរកឃើញស្វ័យប្រវត្តិត្រូវការ browser នៅលើទូរសព្ទ Android។ កំពុងបង្ហាញឧបករណ៍គំរូ — សូមជ្រើសម៉ូដែលរបស់អ្នកខាងលើ។",
      detectedHint: "រកឃើញម៉ូដែលពី browser នេះ។ អ្នកអាចកែប្រែគ្រប់វាលបាន។",
      selectHint: "បានជ្រើសពីមូលដ្ឋានទិន្នន័យឧបករណ៍។ គ្រប់វាលអាចកែប្រែបាន។",
      typedHint: "ម៉ូដែលបញ្ចូលដោយដៃ — សូមបញ្ចូលកំណែ Android និង SDK ខាងក្រោម ដើម្បីទទួលលទ្ធផលត្រឹមត្រូវ។",
      modelSelected: "បានជ្រើស",
      compatibleSummary: "{n} ក្នុងចំណោម {total} កំណែឆបគ្នា",
      refreshed: "បញ្ជីកំណែបានធ្វើបច្ចុប្បន្នភាព",
      noChanges: "បញ្ជីកំណែទាន់សម័យហើយ",
      refreshFailed: "មិនអាចភ្ជាប់ upstream បានទេ — កំពុងបង្ហាញបញ្ជីចុងក្រោយដែលមាន",
      refreshing: "កំពុងធ្វើបច្ចុប្បន្នភាព…",
      autoChecked: "ស្វ័យប្រវត្តិ · ពិនិត្យ {time}",
      lastChecked: "ពិនិត្យលើកចុងក្រោយ",
      added: "ថ្មី", removed: "លុបចោល", modified: "ផ្លាស់ប្តូរ", inRepo: "មានហើយ", needsSync: "ត្រូវ sync",
      noChangesShort: "គ្មានភាពខុសគ្នា", backendError: "មានបញ្ហាម៉ាស៊ីនមេ — សូមព្យាយាមម្តងទៀត",
      score: "ពិន្ទុ", demoTag: "គំរូ", sourceDatabase: "មូលដ្ឋានទិន្នន័យ", sourceUA: "browser", sourceManual: "ដោយដៃ", sourceAdb: "adb",
    },
  };

  const ANDROID_SDK = { "8.0": 26, "8.1": 27, "9": 28, "10": 29, "11": 30, "12": 31, "12L": 32, "13": 33, "14": 34, "15": 35, "16": 36 };

  const state = {
    lang: "km", catalog: null, devices: [], server: null, result: null,
    selectedDeviceId: null, demo: false, detected: null, matches: [], activeSuggestion: -1,
  };

  const $ = (id) => document.getElementById(id);
  const t = (key, params = {}) => {
    let text = (T[state.lang] && T[state.lang][key]) || T.en[key] || key;
    Object.entries(params).forEach(([k, v]) => { text = text.replaceAll(`{${k}}`, v); });
    return text;
  };
  const tr = (item) => (item ? (item[state.lang] || item.en) : "");
  const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  function applyI18n() {
    document.documentElement.lang = state.lang === "km" ? "km" : "en";
    document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => { el.placeholder = t(el.dataset.i18nPlaceholder); });
    document.querySelectorAll(".lang-btn").forEach((btn) => btn.classList.toggle("active", btn.dataset.lang === state.lang));
  }

  let toastTimer;
  function toast(message) {
    const el = $("toast");
    el.textContent = message;
    el.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { el.hidden = true; }, 3500);
  }

  async function api(url, options = {}) {
    const response = await fetch(url, options);
    let data = {};
    try { data = await response.json(); } catch (_) { /* ignore */ }
    return { ok: response.ok, status: response.status, data };
  }
  const post = (url, body) => api(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });

  function timeLabel(iso) {
    if (!iso) return "—";
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return iso;
    return date.toLocaleTimeString(state.lang === "km" ? "km-KH" : "en-GB", { hour: "2-digit", minute: "2-digit" });
  }

  /* ---------- rendering ---------- */

  function renderSync() {
    const pill = $("syncPill"), text = $("syncText"), server = state.server || {};
    pill.className = "sync-pill" + (server.refreshing ? " busy" : server.refreshError ? " error" : "");
    pill.title = `${t("lastChecked")}: ${server.lastRefresh || "—"}${server.refreshError ? "\n" + server.refreshError : ""}`;
    text.textContent = server.refreshing ? t("refreshing") : server.refreshError ? t("refreshFailed") : t("autoChecked", { time: timeLabel(server.lastRefresh) });
  }

  function renderCatalog() {
    const c = state.catalog;
    if (!c) return;
    const local = c.local, upstream = c.upstream, changes = c.changes;
    $("localMeta").textContent = `v${local.patchVersion} · ${local.patchCount} ${t("patches")} · ${local.versions.length} ${t("versions")}`;
    const releaseTag = upstream.release && upstream.release.tag;
    const releaseSuffix = releaseTag && releaseTag !== `v${upstream.patchVersion}` ? ` · ${releaseTag}` : "";
    $("upstreamMeta").textContent = `v${upstream.patchVersion} · ${t("lastChecked")} ${timeLabel(upstream.checkedAt)}${releaseSuffix}`;
    const hours = (state.server && state.server.refreshHours) || 6;
    $("changesMeta").textContent = `${t("lastChecked")} ${timeLabel(upstream.checkedAt)} · ${state.lang === "km" ? "រៀងរាល់" : "every"} ${hours}h`;
    $("channelBadge").textContent = `v${(state.result && state.result.patchVersion) || local.patchVersion}`;

    const item = (entry, cls = "") => {
      const status = entry.experimental ? t("experimental") : t("stable");
      return `<li class="${cls}"><span class="v">${esc(entry.version)}</span><span class="side">${t("minAndroid")} ${esc(entry.androidMin)} · ${status}</span></li>`;
    };
    $("localList").innerHTML = local.versions.map((v) => item(v)).join("");
    const localSet = new Set(local.versions.map((v) => v.version));
    $("upstreamList").innerHTML = (upstream.versions || []).map((v) => {
      const note = localSet.has(v.version) ? t("inRepo") : t("needsSync");
      return `<li class="${localSet.has(v.version) ? "" : "added"}"><span class="v">${esc(v.version)}</span><span class="side">${esc(note)} · SDK ${v.minSdk}</span></li>`;
    }).join("");
    const diffs = [
      ...changes.added.map((v) => `<li class="added"><span class="v">${esc(v.version)}</span><span class="side">${t("added")}</span></li>`),
      ...changes.removed.map((v) => `<li class="removed"><span class="v">${esc(v.version)}</span><span class="side">${t("removed")}</span></li>`),
      ...changes.modified.map((m) => `<li><span class="v">${esc(m.version)}</span><span class="side">${t("modified")}</span></li>`),
    ];
    $("changesList").innerHTML = diffs.length ? diffs.join("") : `<li><span>${t("noChangesShort")}</span></li>`;

    const notice = $("updateNotice");
    if (changes.added.length) {
      notice.hidden = false;
      $("updateNoticeBody").textContent = `${changes.added.map((v) => v.version).join(", ")} — ${state.lang === "km" ? "ត្រូវការ sync ប្រភព patch មុនប្រើប្រាស់។" : "sync the patch sources before patching with them."}`;
    } else {
      notice.hidden = true;
    }
    $("footerVersion").textContent = `${c.generator || "advisor"} · ${state.lang === "km" ? "បង្កើត" : "generated"} ${timeLabel(c.generatedAt)}`;
  }

  function renderResult() {
    const r = state.result;
    const box = $("resultBody");
    if (!r) { box.innerHTML = '<div class="skeleton"></div>'; return; }
    if (!r.recommendation) {
      box.innerHTML = `<div class="error-box"><strong>${esc(tr(r.noCompatibleReason) || t("noCompatible"))}</strong></div>`;
      $("optionsBody").innerHTML = "";
      return;
    }
    const best = r.recommendation, newest = r.newestCompatible;
    const statusKey = best.experimental ? "experimental" : "stable";
    const device = r.device;
    const hero = `
      <div class="hero-result">
        <div class="hero-label">${t("recommended")}</div>
        <div class="hero-version">${esc(best.version)}</div>
        <div class="hero-meta">
          <span class="badge ${best.experimental ? "experimental" : "stable"}">${t(statusKey)}</span>
          <span class="badge outline">${t("minAndroid")} ${esc(best.androidMin)} · SDK ${best.minSdk}</span>
          <span class="badge outline">${t("patchBundle")} v${esc(r.patchVersion)}</span>
        </div>
      </div>`;
    const reasons = `<div class="section-title">${t("whyTitle")}</div><ul class="reason-list">${best.reasons.map((x) => `<li>${esc(tr(x))}</li>`).join("")}</ul>`;
    const mini = `
      <div class="mini-grid" style="margin-top:16px">
        <div class="mini-card"><span>${t("newestLabel")}</span><strong>${newest ? esc(newest.version) : "—"}</strong></div>
        <div class="mini-card"><span>${t("compatibilityLabel")}</span><strong>${r.compatibleCount} / ${r.options.length}</strong></div>
      </div>`;
    const apk = `<div class="section-title">${t("apkTitle")}</div><ul class="apk-list">${r.apk.advice.map((x) => `<li>${esc(tr(x))}</li>`).join("")}</ul>`;
    const notes = r.notes.length ? `<div class="section-title">${t("notesTitle")}</div><div class="notes">${r.notes.map((x) => `<div class="note ${x.code === "update_available" || x.code === "no_compatible" ? "warn" : ""}">${esc(tr(x))}</div>`).join("")}</div>` : "";
    const profile = `<div class="section-title">${esc(device.name)} · ${t("android")} ${esc(device.android)} (SDK ${device.sdk}) · ${esc(device.primaryAbi)} · ${esc(device.density)}${state.demo ? ` · ${t("demoTag")}` : ""}</div>`;
    box.innerHTML = hero + profile + reasons + mini + apk + notes;

    $("compatibleCount").textContent = t("compatibleSummary", { n: r.compatibleCount, total: r.options.length });
    $("channelBadge").textContent = `v${esc(r.patchVersion)}`;
    $("resultSubtitle").textContent = t("resultSubtitle");
  }

  function renderTable() {
    const r = state.result;
    if (!r) return;
    $("optionsBody").innerHTML = r.options.map((option) => {
      const statusKey = option.experimental ? "experimental" : "stable";
      const recommended = r.recommendation && r.recommendation.version === option.version && option.compatible;
      const score = option.compatible ? Math.max(0, Math.min(100, option.score)) : 0;
      const reasonText = option.reasons.map(tr).join(" · ");
      return `<tr class="${recommended ? "recommended" : ""} ${option.compatible ? "" : "incompatible"}" title="${esc(reasonText)}">
        <td class="version-cell">${esc(option.version)}${recommended ? " ★" : ""}</td>
        <td><span class="tag ${statusKey}">${t(statusKey)}</span></td>
        <td>${esc(option.androidMin)}</td>
        <td>${option.minSdk}</td>
        <td class="${option.compatible ? "yes" : "no"}">${option.compatible ? t("yes") : t("no")}</td>
        <td><div class="score-bar"><div class="score-track"><div class="score-fill ${recommended ? "best" : ""}" style="width:${score}%"></div></div><span>${option.compatible ? option.score : "—"}</span></div></td>
      </tr>`;
    }).join("");
  }

  function renderAll() {
    applyI18n();
    renderSync();
    renderCatalog();
    renderResult();
    renderTable();
  }

  /* ---------- device input ---------- */

  function setFields(device) {
    $("androidInput").value = device.android || "";
    $("sdkInput").value = device.sdk ?? "";
    $("abiInput").value = (device.primaryAbi || (device.abi || [])[0] || "");
    $("densityInput").value = device.density || "";
    $("ramInput").value = device.ramGb ?? "";
  }

  function showDeviceHint(text, isDemo) {
    const banner = $("detectBanner");
    banner.hidden = false;
    banner.textContent = text;
    $("selectedDevice").textContent = isDemo ? t("demoProfile") : (state.selectedDeviceId ? t("selectHint") : t("typedHint"));
  }

  function selectDevice(device, { fromDetection = false, demo = false } = {}) {
    state.selectedDeviceId = device.id || null;
    state.demo = demo;
    $("modelInput").value = device.name || device.model || device.id;
    setFields(device);
    $("suggestions").hidden = true;
    showDeviceHint(fromDetection ? `${t("detectedAs")}: ${device.name} — ${t("detectedHint")}` : demo ? t("demoHint") : t("selectHint"), demo);
    scheduleAnalysis();
  }

  function renderSuggestions() {
    const box = $("suggestions");
    if (!state.matches.length) { box.hidden = true; return; }
    box.innerHTML = state.matches.map((d, i) => `<div class="suggestion ${i === state.activeSuggestion ? "active" : ""}" data-index="${i}">${esc(d.brand)} ${esc(d.name)} <small>${esc((d.models || [])[0] || "")} · ${t("android")} ${esc(d.android)}</small></div>`).join("");
    box.hidden = false;
  }

  function buildPayload() {
    const payload = { channel: $("channelInput").value };
    if (state.selectedDeviceId) payload.deviceId = state.selectedDeviceId;
    else if ($("modelInput").value.trim()) payload.model = $("modelInput").value.trim();
    const sdk = $("sdkInput").value, android = $("androidInput").value, abi = $("abiInput").value,
      density = $("densityInput").value, ram = $("ramInput").value;
    if (sdk) payload.sdk = Number(sdk);
    if (android) payload.android = android;
    if (abi) payload.abi = abi;
    if (density) payload.density = density;
    if (ram) payload.ramGb = Number(ram);
    return payload;
  }

  async function runAnalysis() {
    try {
      const { ok, data } = await post("/api/recommend", buildPayload());
      if (!ok) { toast(data.error || t("backendError")); return; }
      state.result = data;
      renderResult();
      renderTable();
      $("channelBadge").textContent = `v${esc(data.patchVersion)}`;
    } catch (error) {
      toast(t("backendError") + ` (${error.message})`);
    }
  }

  let analysisTimer;
  function scheduleAnalysis() {
    clearTimeout(analysisTimer);
    analysisTimer = setTimeout(runAnalysis, 260);
  }

  async function autoDetect() {
    const payload = { userAgent: navigator.userAgent || "" };
    try {
      if (navigator.userAgentData && navigator.userAgentData.getHighEntropyValues) {
        const hints = await navigator.userAgentData.getHighEntropyValues(["model", "platformVersion", "architecture", "bitness", "platform"]);
        payload.modelHint = hints.model || "";
        payload.platformVersion = hints.platformVersion || "";
        payload.architecture = hints.architecture || "";
        payload.bitness = hints.bitness || "";
      }
    } catch (_) { /* high-entropy hints are optional */ }

    try {
      const { ok, data } = await post("/api/detect", payload);
      if (ok && data.device && data.device.sdk) {
        const device = { ...data.device, primaryAbi: data.device.primaryAbi || (data.device.abi || [])[0] };
        state.detected = device;
        state.matches = data.matches || [];
        if (device.deviceId) {
          const match = state.devices.find((d) => d.id === device.deviceId);
          selectDevice({ ...device, id: device.deviceId, name: (match && match.name) || device.name }, { fromDetection: true });
        } else {
          state.selectedDeviceId = null;
          $("modelInput").value = device.model || "";
          setFields(device);
          showDeviceHint(t("detectedHint"), false);
          await runAnalysis();
        }
        return;
      }
    } catch (_) { /* fall through to demo profile */ }

    const sample = state.devices.find((d) => d.id === "samsung-a54") || state.devices[0];
    if (sample) selectDevice(sample, { demo: true });
  }

  /* ---------- catalog refresh ---------- */

  async function loadState() {
    const { ok, data } = await api("/api/state");
    if (!ok) { toast(t("backendError")); return; }
    const previous = state.catalog && state.catalog.generatedAt;
    state.catalog = data.catalog;
    state.devices = data.devices || [];
    state.server = data.server;
    renderAll();
    if (previous && previous !== data.catalog.generatedAt && state.result) {
      await runAnalysis();  // background auto-refresh changed the catalog
    }
  }

  async function refreshCatalog() {
    const buttons = [$("refreshBtn"), $("catalogRefresh"), $("noticeRefresh")];
    buttons.forEach((b) => { if (b) b.disabled = true; });
    $("syncPill").className = "sync-pill busy";
    $("syncText").textContent = t("refreshing");
    try {
      const { ok, data } = await post("/api/refresh", {});
      if (ok) {
        state.catalog = data.catalog || state.catalog;
        state.server = data.state || state.server;
        renderAll();
        await runAnalysis();
        toast(data.error ? t("refreshFailed") : data.changed ? t("refreshed") : t("noChanges"));
      } else {
        toast(t("backendError"));
      }
    } catch (error) {
      toast(t("refreshFailed") + ` (${error.message})`);
    } finally {
      buttons.forEach((b) => { if (b) b.disabled = false; });
      renderSync();
    }
  }

  /* ---------- events ---------- */

  function bindEvents() {
    document.querySelectorAll(".lang-btn").forEach((btn) => btn.addEventListener("click", () => {
      state.lang = btn.dataset.lang;
      renderAll();
      if (state.demo) showDeviceHint(t("demoHint"), true);
    }));
    $("detectBtn").addEventListener("click", autoDetect);
    $("analyzeBtn").addEventListener("click", runAnalysis);
    [$("refreshBtn"), $("catalogRefresh"), $("noticeRefresh")].forEach((b) => b.addEventListener("click", refreshCatalog));

    const model = $("modelInput");
    model.addEventListener("input", () => {
      state.selectedDeviceId = null;
      state.demo = false;
      const query = model.value.trim();
      const { normalize } = { normalize: (s) => s.toLowerCase().replace(/[^a-z0-9]/g, "") };
      const needle = normalize(query);
      state.matches = query
        ? state.devices.filter((d) => normalize([d.id, d.name, d.brand, ...(d.models || []), ...(d.aliases || [])].join(" ")).includes(needle)).slice(0, 8)
        : [];
      state.activeSuggestion = -1;
      renderSuggestions();
      $("selectedDevice").textContent = t("typedHint");
      $("detectBanner").hidden = true;
      scheduleAnalysis();
    });
    model.addEventListener("keydown", (event) => {
      if (state.matches.length && !$("suggestions").hidden) {
        if (event.key === "ArrowDown" || event.key === "ArrowUp") {
          event.preventDefault();
          state.activeSuggestion = Math.max(0, Math.min(state.matches.length - 1, state.activeSuggestion + (event.key === "ArrowDown" ? 1 : -1)));
          renderSuggestions();
        } else if (event.key === "Enter" && state.activeSuggestion >= 0) {
          event.preventDefault();
          selectDevice(state.matches[state.activeSuggestion]);
        }
      }
    });
    $("suggestions").addEventListener("click", (event) => {
      const row = event.target.closest(".suggestion");
      if (row) selectDevice(state.matches[Number(row.dataset.index)]);
    });
    document.addEventListener("click", (event) => {
      if (!event.target.closest(".field")) $("suggestions").hidden = true;
    });

    $("androidInput").addEventListener("change", () => {
      const value = $("androidInput").value;
      if (value && ANDROID_SDK[value]) $("sdkInput").value = ANDROID_SDK[value];
      scheduleAnalysis();
    });
    ["sdkInput", "abiInput", "densityInput", "ramInput", "channelInput"].forEach((id) => $(id).addEventListener("change", scheduleAnalysis));
  }

  async function init() {
    bindEvents();
    applyI18n();
    await loadState();
    await autoDetect();
    setInterval(loadState, 5 * 60 * 1000);  // pick up server-side background refreshes
  }

  document.addEventListener("DOMContentLoaded", init);
})();
