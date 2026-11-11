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
  function toast(message){try{if(window.Android&&Android.showToast)Android.showToast(message);}catch(e){}}
  function documents(){
    var result=[document],seen=[document];
    for(var index=0;index<result.length;index++){
      var frames=[];
      try{frames=result[index].querySelectorAll('iframe,frame');}catch(e){}
      Array.prototype.forEach.call(frames,function(frame){
        try{var child=frame.contentDocument;if(child&&seen.indexOf(child)<0){seen.push(child);result.push(child);}}catch(e){}
      });
    }
    return result;
  }
  function metadata(element){
    var values=[];
    ['id','class','title','aria-label','name','data-action','data-command','data-role','data-title'].forEach(function(name){
      try{values.push(element.getAttribute(name)||'');}catch(e){}
    });
    try{var text=(element.textContent||'').trim();if(text.length<80)values.push(text);}catch(e){}
    return values.join(' ').toLowerCase();
  }
  function playerAncestor(element){
    var parent=element;
    for(var depth=0;parent&&depth<7;depth++,parent=parent.parentElement){
      try{
        var info=metadata(parent);
        if(/player|video|media/.test(info)||parent.querySelector('video,iframe,[class*="player"],[class*="video"]'))return true;
      }catch(e){}
    }
    return false;
  }
  function downloadControl(){
    var matches=[];
    documents().forEach(function(doc){
      var nodes=[];
      try{nodes=doc.querySelectorAll('button,a,[role="button"],[data-action],[data-command],[onclick]');}catch(e){}
      Array.prototype.forEach.call(nodes,function(element){
        try{
          if(element.id==='morphe-snap-media'||element.closest('#morphe-google-translate'))return;
          var box=element.getBoundingClientRect(),info=metadata(element);
          if(box.width<20||box.height<20||box.bottom<0||box.top>(doc.defaultView.innerHeight||10000))return;
          var keyword=/download|save.?video|下载|下載|缓存|緩存|离线|離線/.test(info);
          if(!keyword)return;
          var score=(playerAncestor(element)?1000:0)+(info.indexOf('download')>=0?100:0)+(box.width*box.height<20000?20:0);
          matches.push({element:element,score:score});
        }catch(e){}
      });
    });
    matches.sort(function(a,b){return b.score-a.score;});
    return matches.length?matches[0].element:null;
  }
  function openOriginalDownload(){
    var control=downloadControl();
    if(!control){toast('Open the video player controls, then tap Save media again.');return false;}
    try{
      control.scrollIntoView({block:'center',inline:'center'});
      control.click();
      toast('Opening the original download panel...');
      return true;
    }catch(e){toast('Unable to open the original download panel');return false;}
  }
  var button=document.createElement('button');
  button.id='morphe-snap-media';
  button.textContent='Save media';
  button.setAttribute('aria-label','Open original media download');
  button.style.cssText='position:fixed;right:14px;bottom:74px;z-index:2147483647;padding:10px 14px;border:0;border-radius:22px;background:#1769e0;color:white;font:600 14px sans-serif;box-shadow:0 2px 8px #0008';
  button.addEventListener('click',openOriginalDownload);
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

private fun compatibility() = Compatibility(
    name = "BigTree",
    packageName = "com.app.bigtree",
    targets = listOf(AppTarget(version = "1.14", minSdk = 24, isExperimental = true)),
)

@Suppress("unused")
val snapMediaPatch = bytecodePatch(
    name = "Snap Media",
    description = "Adds a Save media shortcut that opens the webpage player's original download control, preserving its full-file URL and configured external downloader such as IDM. It does not save preview or partial playback resources.",
    default = false,
) {
    compatibleWith(compatibility())
    execute { injectPageScript(SNAP_MARKER, snapMediaScript) }
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
