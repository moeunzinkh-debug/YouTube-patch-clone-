package app.morphe.patches.bigtree

import app.morphe.patcher.extensions.InstructionExtensions.addInstructions
import app.morphe.patcher.patch.AppTarget
import app.morphe.patcher.patch.Compatibility
import app.morphe.patcher.patch.bytecodePatch
import com.android.tools.smali.dexlib2.AccessFlags
import com.android.tools.smali.dexlib2.Opcode
import com.android.tools.smali.dexlib2.iface.instruction.ReferenceInstruction
import com.android.tools.smali.dexlib2.iface.reference.MethodReference
import com.android.tools.smali.dexlib2.iface.reference.StringReference

private const val WEB_CLIENT = "LG1/m0;"
private const val URL_WATCHER_MARKER = "window.__urlWatcher"
private const val SNAP_MARKER = "window.__morpheSnapMedia"
private const val TRANSLATE_MARKER = "window.__morpheEnglishTranslation"

private val snapMediaScript = """
(function(){
  if(window.__morpheSnapMedia)return;
  window.__morpheSnapMedia=true;
  var nativeKeys=['morphe-snap-manifest-url','morphe-snap-media-url'],found={},sequence=0;
  function toast(message){try{if(window.Android&&Android.showToast)Android.showToast(message);}catch(e){}}
  function absolute(url,base){
    try{return new URL(String(url||''),base||document.baseURI).href;}catch(e){return '';}
  }
  function blocked(url){return /\.(?:ts|m4s|cmfv|cmfa|aac)(?:[?#]|$)/i.test(url)||/^blob:|^data:/i.test(url);}
  function mediaScore(url,hint){
    var value=String(url||''),info=String(hint||'').toLowerCase(),score=0;
    if(!/^https?:/i.test(value)||blocked(value))return 0;
    if(/\.m3u8(?:[?#]|$)/i.test(value))score=30000;
    else if(/\.mpd(?:[?#]|$)/i.test(value))score=29000;
    else if(/\.(?:mp4|m4v|webm|mov)(?:[?#]|$)/i.test(value))score=22000;
    else if(/(?:manifest|playlist|master|videoplayback|playurl|video_url|stream_url)/i.test(value))score=16000;
    else if(/video|media|stream|source|download|attachment|original|播放|下载|下載/.test(info))score=9000;
    if(/download|attachment|original|source|下载|下載/.test(info))score+=4000;
    return score;
  }
  function remember(url,hint,base){
    var value=absolute(url,base),score=mediaScore(value,hint);
    if(!score)return;
    var old=found[value];
    found[value]={url:value,score:Math.max(score,old?old.score:0),order:++sequence};
  }
  function metadata(element){
    var values=[];
    ['id','class','title','aria-label','name','type','data-action','data-command','data-role','data-title'].forEach(function(name){
      try{values.push(element.getAttribute(name)||'');}catch(e){}
    });
    try{var text=(element.textContent||'').trim();if(text.length<120)values.push(text);}catch(e){}
    return values.join(' ').toLowerCase();
  }
  function install(win){
    try{
      if(!win||win.__morpheMediaCapture)return;
      win.__morpheMediaCapture=true;
      var originalFetch=win.fetch;
      if(originalFetch)win.fetch=function(input){
        try{remember(typeof input==='string'?input:input&&input.url,'fetch',win.document.baseURI);}catch(e){}
        return originalFetch.apply(this,arguments);
      };
      var originalOpen=win.XMLHttpRequest&&win.XMLHttpRequest.prototype.open;
      if(originalOpen)win.XMLHttpRequest.prototype.open=function(method,url){
        try{remember(url,'xhr '+method,win.document.baseURI);}catch(e){}
        return originalOpen.apply(this,arguments);
      };
      if(win.PerformanceObserver){
        var observer=new win.PerformanceObserver(function(list){
          list.getEntries().forEach(function(entry){remember(entry.name,'performance '+(entry.initiatorType||''),win.document.baseURI);});
        });
        observer.observe({entryTypes:['resource']});
      }
    }catch(e){}
  }
  function documents(){
    var result=[document],seen=[document];
    for(var index=0;index<result.length;index++){
      var frames=[];install(result[index].defaultView);
      try{frames=result[index].querySelectorAll('iframe,frame');}catch(e){}
      Array.prototype.forEach.call(frames,function(frame){
        try{remember(frame.src,metadata(frame),result[index].baseURI);}catch(e){}
        try{var child=frame.contentDocument;if(child&&seen.indexOf(child)<0){seen.push(child);result.push(child);}}catch(e){}
      });
    }
    return result;
  }
  function scan(){
    documents().forEach(function(doc){
      var nodes=[];
      try{nodes=doc.querySelectorAll('video,audio,source,track,iframe,frame,embed,object,[href],[src],[srcset],[data-url],[data-src],[data-file],[data-download],[data-download-url],[data-video-url],[data-stream-url]');}catch(e){}
      Array.prototype.forEach.call(nodes,function(element){
        try{
          var info=metadata(element),values=[element.currentSrc,element.src,element.href,element.data];
          ['data-url','data-src','data-file','data-download','data-download-url','data-video-url','data-stream-url'].forEach(function(name){values.push(element.getAttribute(name));});
          var srcset=element.getAttribute&&element.getAttribute('srcset');
          if(srcset)srcset.split(',').forEach(function(item){values.push(item.trim().split(/\s+/)[0]);});
          values.forEach(function(value){remember(value,info,doc.baseURI);});
        }catch(e){}
      });
      try{doc.defaultView.performance.getEntriesByType('resource').forEach(function(entry){remember(entry.name,'performance '+(entry.initiatorType||''),doc.baseURI);});}catch(e){}
      try{
        doc.querySelectorAll('script:not([src])').forEach(function(script){
          var text=script.textContent||'',matches=text.match(/https?:\\?\/\\?\/[^\s"'<>]+/g)||[];
          matches.forEach(function(value){remember(value.replace(/\\\//g,'/'),'script media url',doc.baseURI);});
        });
      }catch(e){}
    });
    try{if(window.Android&&Android.getData)nativeKeys.forEach(function(key){remember(Android.getData(key),'native iframe/resource request',document.baseURI);});}catch(e){}
  }
  function bestMediaUrl(){
    scan();
    var candidates=Object.keys(found).map(function(key){return found[key];});
    candidates.sort(function(a,b){return b.score-a.score||b.order-a.order;});
    return candidates.length?candidates[0].url:'';
  }
  install(window);
  try{new MutationObserver(function(){scan();}).observe(document.documentElement,{subtree:true,childList:true,attributes:true,attributeFilter:['src','href','srcset','data-url','data-src','data-file','data-download','data-download-url','data-video-url','data-stream-url']});}catch(e){}
  setInterval(scan,1500);scan();
  function openDownload(){
    var url=bestMediaUrl();
    if(!url){toast('Video not found yet. Start playback, wait a few seconds, then tap again.');return;}
    try{
      if(window.Android&&Android.openAppDownload){Android.openAppDownload(url);toast('Choose a downloader to save the detected video.');return;}
    }catch(e){}
    toast('No external downloader is available.');
  }
  var button=document.createElement('button');
  button.id='morphe-snap-media';
  button.innerHTML='<svg viewBox="0 0 24 24" width="28" height="28" aria-hidden="true"><path fill="currentColor" d="M5 20h14v-2H5v2zm7-18v10.17l3.59-3.58L17 10l-5 5-5-5 1.41-1.41L11 12.17V2h1z"/></svg>';
  button.setAttribute('aria-label','Download media');button.setAttribute('title','Download media');button.setAttribute('translate','no');button.className='notranslate';
  button.style.cssText='position:fixed;right:14px;bottom:74px;z-index:2147483647;width:54px;height:54px;padding:0;display:flex;align-items:center;justify-content:center;border:0;border-radius:50%;background:#1769e0;color:white;box-shadow:0 3px 10px #0009;touch-action:none;user-select:none;-webkit-user-select:none';
  try{var saved=JSON.parse(localStorage.getItem('morphe-snap-position')||'null');if(saved&&isFinite(saved.x)&&isFinite(saved.y)){button.style.left=Math.max(0,Math.min(innerWidth-54,saved.x))+'px';button.style.top=Math.max(0,Math.min(innerHeight-54,saved.y))+'px';button.style.right='auto';button.style.bottom='auto';}}catch(e){}
  var drag=null,suppressClick=false;
  button.addEventListener('pointerdown',function(event){
    if(event.button!==undefined&&event.button!==0)return;
    var box=button.getBoundingClientRect();button.style.left=box.left+'px';button.style.top=box.top+'px';button.style.right='auto';button.style.bottom='auto';
    drag={id:event.pointerId,startX:event.clientX,startY:event.clientY,left:box.left,top:box.top,moved:false};
    try{button.setPointerCapture(event.pointerId);}catch(e){}event.preventDefault();
  });
  button.addEventListener('pointermove',function(event){
    if(!drag||drag.id!==event.pointerId)return;
    var dx=event.clientX-drag.startX,dy=event.clientY-drag.startY;if(Math.abs(dx)>5||Math.abs(dy)>5)drag.moved=true;
    button.style.left=Math.max(0,Math.min(innerWidth-button.offsetWidth,drag.left+dx))+'px';button.style.top=Math.max(0,Math.min(innerHeight-button.offsetHeight,drag.top+dy))+'px';event.preventDefault();
  });
  function finishDrag(event){
    if(!drag||drag.id!==event.pointerId)return;suppressClick=drag.moved;
    if(drag.moved){try{localStorage.setItem('morphe-snap-position',JSON.stringify({x:button.offsetLeft,y:button.offsetTop}));}catch(e){}}
    drag=null;try{button.releasePointerCapture(event.pointerId);}catch(e){}setTimeout(function(){suppressClick=false;},0);event.preventDefault();
  }
  button.addEventListener('pointerup',finishDrag);button.addEventListener('pointercancel',finishDrag);
  button.addEventListener('click',function(event){if(suppressClick){event.preventDefault();event.stopPropagation();return;}openDownload();});
  (document.body||document.documentElement).appendChild(button);
})();
""".trimIndent()
private val translateEnglishScript = """
(function(){
  if(window.__morpheEnglishTranslation)return;
  window.__morpheEnglishTranslation=true;
  var host=document.createElement('div');
  host.id='morphe-google-translate';
  host.style.cssText='position:fixed;left:10px;bottom:72px;z-index:2147483646;max-width:190px;background:white;color:black;padding:6px;border-radius:8px;box-shadow:0 2px 8px #0008';
  (document.body||document.documentElement).appendChild(host);
  function chooseEnglish(){
    var select=document.querySelector('.goog-te-combo');
    if(select){select.value='en';select.dispatchEvent(new Event('change',{bubbles:true}));return true;}
    return false;
  }
  window.__morpheGoogleTranslateInit=function(){
    try{
      new google.translate.TranslateElement({pageLanguage:'auto',includedLanguages:'en',autoDisplay:false},'morphe-google-translate');
      setTimeout(chooseEnglish,500);
    }catch(e){}
  };
  var button=document.createElement('button');
  button.textContent='Translate to English';
  button.setAttribute('aria-label','Translate this page to English');
  button.style.cssText='border:0;border-radius:16px;padding:8px 10px;background:#0b8043;color:white;font:600 13px sans-serif';
  button.onclick=function(){if(!chooseEnglish()&&window.__morpheGoogleTranslateInit)window.__morpheGoogleTranslateInit();};
  host.appendChild(button);
  var script=document.createElement('script');
  script.src='https://translate.google.com/translate_a/element.js?cb=__morpheGoogleTranslateInit';
  script.async=true;
  script.onerror=function(){button.textContent='Translation unavailable';};
  (document.head||document.documentElement).appendChild(script);
})();
""".trimIndent()

private fun String.smaliLiteral(): String = buildString(length + 2) {
    append('"')
    for (character in this@smaliLiteral) when (character) {
        '\\' -> append("\\\\")
        '"' -> append("\\\"")
        '\n' -> append("\\n")
        '\r' -> append("\\r")
        '\t' -> append("\\t")
        else -> append(character)
    }
    append('"')
}

private fun app.morphe.patcher.patch.BytecodePatchContext.injectPageScript(marker: String, script: String) {
    require(packageMetadata.versionName == "1.14" && packageMetadata.versionCode == "10") {
        "BigTree patches support only the reviewed BigTree 1.14 build 10"
    }
    val client = mutableClassDefBy(WEB_CLIENT)
    require(client.superclass == "Landroid/webkit/WebViewClient;") { "Reviewed BigTree WebView client changed" }
    val method = client.methods.singleOrNull { candidate ->
        candidate.name == "onPageFinished" && candidate.returnType == "V" &&
            candidate.parameterTypes.map { it.toString() } == listOf("Landroid/webkit/WebView;", "Ljava/lang/String;") &&
            AccessFlags.PUBLIC.isSet(candidate.accessFlags) && !AccessFlags.STATIC.isSet(candidate.accessFlags)
    } ?: error("Reviewed BigTree page-finished hook is unavailable")
    val implementation = requireNotNull(method.implementation) { "BigTree page-finished hook has no implementation" }
    require(implementation.registerCount == 5) { "BigTree page-finished register layout changed" }
    val instructions = implementation.instructions.toList()
    require(instructions.firstOrNull()?.opcode == Opcode.INVOKE_SUPER && instructions.lastOrNull()?.opcode == Opcode.RETURN_VOID) {
        "BigTree page-finished control flow changed"
    }
    val strings = instructions.mapNotNull { (it as? ReferenceInstruction)?.reference as? StringReference }.map { it.string }
    require(strings.count { URL_WATCHER_MARKER in it } == 1) { "BigTree URL watcher fingerprint changed" }
    require(strings.none { marker in it }) { "Requested BigTree feature is already installed" }
    val installedFeatureCount = strings.count { SNAP_MARKER in it || TRANSLATE_MARKER in it }
    require(installedFeatureCount in 0..1) { "Unexpected BigTree feature injection state" }
    val calls = instructions.mapNotNull { (it as? ReferenceInstruction)?.reference as? MethodReference }
    require(calls.count {
        it.definingClass == "Landroid/webkit/WebView;" && it.name == "evaluateJavascript" &&
            it.parameterTypes.map { type -> type.toString() } == listOf("Ljava/lang/String;", "Landroid/webkit/ValueCallback;")
    } == 1 + installedFeatureCount) { "BigTree page JavaScript hook fingerprint changed" }

    // p1 is the WebView. v0 and v1 are the two existing local registers and
    // are overwritten by the original body immediately after this injection.
    method.addInstructions(1, """
        const-string v0, ${script.smaliLiteral()}
        const/4 v1, 0x0
        invoke-virtual {p1, v0, v1}, Landroid/webkit/WebView;->evaluateJavascript(Ljava/lang/String;Landroid/webkit/ValueCallback;)V
    """.trimIndent())
}

private fun app.morphe.patcher.patch.BytecodePatchContext.injectNativeMediaCapture() {
    val client = mutableClassDefBy(WEB_CLIENT)
    val method = client.methods.singleOrNull { candidate ->
        candidate.name == "shouldInterceptRequest" &&
            candidate.returnType == "Landroid/webkit/WebResourceResponse;" &&
            candidate.parameterTypes.map { it.toString() } == listOf(
                "Landroid/webkit/WebView;", "Landroid/webkit/WebResourceRequest;",
            ) && AccessFlags.PUBLIC.isSet(candidate.accessFlags) && !AccessFlags.STATIC.isSet(candidate.accessFlags)
    } ?: error("Reviewed BigTree resource-request hook is unavailable")
    val implementation = requireNotNull(method.implementation) { "BigTree resource-request hook has no implementation" }
    require(implementation.registerCount == 43) { "BigTree resource-request register layout changed" }
    val instructions = implementation.instructions.toList()
    require(instructions.size == 917 && instructions[0].opcode == Opcode.MOVE_OBJECT_FROM16 &&
        instructions[1].opcode == Opcode.MOVE_OBJECT_FROM16) {
        "BigTree resource-request control flow changed"
    }
    val strings = instructions.mapNotNull { (it as? ReferenceInstruction)?.reference as? StringReference }.map { it.string }
    require("transfer-encoding" in strings && "requestHeaders" in strings && "morphe-snap-media-url" !in strings) {
        "BigTree resource-request fingerprint changed"
    }

    // The WebViewClient sees requests made by cross-origin iframes that page
    // JavaScript cannot inspect. Clear the saved candidate for each main-frame
    // navigation, then retain only likely full media/manifest requests. v7-v11
    // are overwritten by the original method before their original values are read.
    method.addInstructions(9, """
        invoke-interface {v2}, Landroid/webkit/WebResourceRequest;->isForMainFrame()Z
        move-result v7
        if-eqz v7, :morphe_capture_request
        iget-object v7, v1, LG1/m0;->a Lcom/app/bigtree/MainActivity;
        const-string v8, "js_store"
        const/4 v9, 0x0
        invoke-virtual {v7, v8, v9}, Landroid/content/Context;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;
        move-result-object v7
        invoke-interface {v7}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences${'$'}Editor;
        move-result-object v7
        const-string v8, "morphe-snap-media-url"
        const-string v9, ""
        invoke-interface {v7, v8, v9}, Landroid/content/SharedPreferences${'$'}Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences${'$'}Editor;
        move-result-object v7
        const-string v8, "morphe-snap-manifest-url"
        invoke-interface {v7, v8, v9}, Landroid/content/SharedPreferences${'$'}Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences${'$'}Editor;
        move-result-object v7
        invoke-interface {v7}, Landroid/content/SharedPreferences${'$'}Editor;->apply()V
        goto :morphe_capture_done
        :morphe_capture_request
        invoke-interface {v2}, Landroid/webkit/WebResourceRequest;->getUrl()Landroid/net/Uri;
        move-result-object v7
        invoke-virtual {v7}, Landroid/net/Uri;->toString()Ljava/lang/String;
        move-result-object v7
        const-string v8, ".ts"
        invoke-virtual {v7, v8}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
        move-result v8
        if-nez v8, :morphe_capture_done
        const-string v8, ".m4s"
        invoke-virtual {v7, v8}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
        move-result v8
        if-nez v8, :morphe_capture_done
        const-string v8, ".cmfv"
        invoke-virtual {v7, v8}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
        move-result v8
        if-nez v8, :morphe_capture_done
        const-string v8, ".cmfa"
        invoke-virtual {v7, v8}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
        move-result v8
        if-nez v8, :morphe_capture_done
        const-string v8, "init.mp4"
        invoke-virtual {v7, v8}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
        move-result v8
        if-nez v8, :morphe_capture_done
        const-string v8, ".m3u8"
        invoke-virtual {v7, v8}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
        move-result v8
        if-nez v8, :morphe_capture_manifest
        const-string v8, ".mpd"
        invoke-virtual {v7, v8}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
        move-result v8
        if-nez v8, :morphe_capture_manifest
        const-string v8, "manifest"
        invoke-virtual {v7, v8}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
        move-result v8
        if-nez v8, :morphe_capture_manifest
        const-string v8, "playlist"
        invoke-virtual {v7, v8}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
        move-result v8
        if-nez v8, :morphe_capture_manifest
        const-string v8, ".mp4"
        invoke-virtual {v7, v8}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
        move-result v8
        if-nez v8, :morphe_capture_media
        const-string v8, ".webm"
        invoke-virtual {v7, v8}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
        move-result v8
        if-nez v8, :morphe_capture_media
        const-string v8, "videoplayback"
        invoke-virtual {v7, v8}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
        move-result v8
        if-eqz v8, :morphe_capture_done
        :morphe_capture_media
        const-string v10, "morphe-snap-media-url"
        goto :morphe_capture_write
        :morphe_capture_manifest
        const-string v10, "morphe-snap-manifest-url"
        :morphe_capture_write
        iget-object v8, v1, LG1/m0;->a Lcom/app/bigtree/MainActivity;
        const-string v9, "js_store"
        const/4 v11, 0x0
        invoke-virtual {v8, v9, v11}, Landroid/content/Context;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;
        move-result-object v8
        invoke-interface {v8}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences${'$'}Editor;
        move-result-object v8
        invoke-interface {v8, v10, v7}, Landroid/content/SharedPreferences${'$'}Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences${'$'}Editor;
        move-result-object v8
        invoke-interface {v8}, Landroid/content/SharedPreferences${'$'}Editor;->apply()V
        :morphe_capture_done
    """.trimIndent())
}

private fun compatibility() = Compatibility(
    name = "BigTree",
    packageName = "com.app.bigtree",
    targets = listOf(AppTarget(version = "1.14", minSdk = 24, isExperimental = true)),
)

@Suppress("unused")
val snapMediaPatch = bytecodePatch(
    name = "Snap Media",
    description = "Detects full video and stream-manifest URLs from page elements, fetch/XHR, same-origin frames, and native cross-origin iframe requests, then sends the best result through Android ACTION_VIEW so any compatible downloader can handle it. Individual stream segments are rejected.",
    default = false,
) {
    compatibleWith(compatibility())
    execute {
        injectPageScript(SNAP_MARKER, snapMediaScript)
        injectNativeMediaCapture()
    }
}

@Suppress("unused")
val translationToEnglishPatch = bytecodePatch(
    name = "Translation to English",
    description = "Adds automatic webpage translation to English through Google's hosted Translate Element. Page text is sent to an external Google service; network, CSP and live-site compatibility require device testing.",
    default = false,
) {
    compatibleWith(compatibility())
    execute { injectPageScript(TRANSLATE_MARKER, translateEnglishScript) }
}
