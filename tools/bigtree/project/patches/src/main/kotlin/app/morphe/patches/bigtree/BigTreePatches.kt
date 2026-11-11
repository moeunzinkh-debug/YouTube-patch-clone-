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
  function source(element){
    if(!element)return '';
    return element.currentSrc||element.src||element.poster||'';
  }
  function filename(url,element){
    try{
      var value=new URL(url,location.href).pathname.split('/').pop();
      if(value&&value.indexOf('.')>0)return decodeURIComponent(value);
    }catch(e){}
    var type=(element&&element.tagName==='VIDEO')?'mp4':'jpg';
    return 'bigtree-media-'+Date.now()+'.'+type;
  }
  function save(element){
    var url=source(element);
    if(!url){toast('No downloadable media found');return;}
    if(url.indexOf('blob:')===0||url.indexOf('data:')===0){toast('This media source cannot be downloaded directly');return;}
    try{
      if(!window.Android||!Android.saveFile){toast('Android media saver is unavailable');return;}
      var mime=(element&&element.tagName==='VIDEO')?'video/mp4':'image/jpeg';
      Android.saveFile(url,filename(url,element),mime,'morphe-snap-'+Date.now());
      toast('Saving media...');
    }catch(e){toast('Unable to save media');}
  }
  function candidates(){
    return Array.prototype.slice.call(document.querySelectorAll('video,img')).filter(function(element){
      var box=element.getBoundingClientRect();
      return source(element)&&box.width>48&&box.height>48&&box.bottom>0&&box.top<innerHeight;
    }).sort(function(a,b){
      var aa=a.getBoundingClientRect(),bb=b.getBoundingClientRect();
      return bb.width*bb.height-aa.width*aa.height;
    });
  }
  document.addEventListener('contextmenu',function(event){
    var element=event.target&&event.target.closest&&event.target.closest('video,img');
    if(element){event.preventDefault();save(element);}
  },true);
  var button=document.createElement('button');
  button.id='morphe-snap-media';
  button.textContent='Save media';
  button.setAttribute('aria-label','Save visible photo or video');
  button.style.cssText='position:fixed;right:14px;bottom:74px;z-index:2147483647;padding:10px 14px;border:0;border-radius:22px;background:#1769e0;color:white;font:600 14px sans-serif;box-shadow:0 2px 8px #0008';
  button.addEventListener('click',function(){var list=candidates();if(list.length)save(list[0]);else toast('No downloadable media found');});
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
    val calls = instructions.mapNotNull { (it as? ReferenceInstruction)?.reference as? MethodReference }
    require(calls.count {
        it.definingClass == "Landroid/webkit/WebView;" && it.name == "evaluateJavascript" &&
            it.parameterTypes.map { type -> type.toString() } == listOf("Ljava/lang/String;", "Landroid/webkit/ValueCallback;")
    } == 1) { "BigTree page JavaScript hook fingerprint changed" }

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
    description = "Adds a Save media control and long-press media saving to BigTree pages using the app's reviewed native saveFile bridge. Direct image/video URLs only; blob/data media and runtime site compatibility are not guaranteed.",
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
