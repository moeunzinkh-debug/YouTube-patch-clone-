package app.morphe.patches.genv

import app.morphe.patcher.extensions.InstructionExtensions.addInstructionsWithLabels
import app.morphe.patcher.extensions.InstructionExtensions.replaceInstruction
import app.morphe.patcher.patch.AppTarget
import app.morphe.patcher.patch.Compatibility
import app.morphe.patcher.patch.bytecodePatch
import app.morphe.patcher.patch.resourcePatch
import app.morphe.patcher.util.proxy.mutableTypes.MutableMethod
import com.android.tools.smali.dexlib2.AccessFlags
import com.android.tools.smali.dexlib2.Opcode
import com.android.tools.smali.dexlib2.builder.instruction.BuilderInstruction21c
import com.android.tools.smali.dexlib2.iface.instruction.OneRegisterInstruction
import com.android.tools.smali.dexlib2.iface.instruction.ReferenceInstruction
import com.android.tools.smali.dexlib2.iface.reference.MethodReference
import com.android.tools.smali.dexlib2.iface.reference.StringReference
import com.android.tools.smali.dexlib2.immutable.reference.ImmutableStringReference
import org.w3c.dom.Document
import org.w3c.dom.Element

private const val GENV_PACKAGE = "com.ainate.ai.video.generate"
private const val MICROG_PACKAGE = "app.revanced.android.gms"
private const val ANDROID_NS = "http://schemas.android.com/apk/res/android"
private const val GUARD = "Lapp/morphe/extension/genv/MicroGGuard;"
// V3.0 APK signer (not the distinct source-stamp signer) of the reviewed
// SHA-pinned GenV 3.7.2 base. This is public certificate metadata, not a key.
private const val ORIGINAL_GENV_SIGNER_SHA1 = "be4c81d3869d726ea9f0229ab937f2e11ab1ccc7"

private val genvExtension = bytecodePatch { extendWith("extensions/genv.mpe") }

private fun Element.androidAttr(name: String): String =
    getAttributeNS(ANDROID_NS, name).ifEmpty { getAttribute("android:$name") }

/** Only package visibility, known C2DM routing and the reviewed GenV identity. */
internal fun addMorpheMicroGManifestEntries(document: Document) {
    val root = document.documentElement
    require(root.tagName == "manifest" && root.getAttribute("package") == GENV_PACKAGE) {
        "Unexpected GenV manifest package"
    }
    val applications = root.getElementsByTagName("application")
    require(applications.length == 1) { "Unexpected GenV application element" }
    val application = applications.item(0) as Element
    val queryNodes = root.getElementsByTagName("queries")
    require(queryNodes.length <= 1) { "Unexpected multiple queries elements" }
    val queries = (queryNodes.item(0) as? Element) ?: document.createElement("queries").also {
        root.insertBefore(it, application)
    }
    val packages = queries.getElementsByTagName("package")
    if ((0 until packages.length).none { (packages.item(it) as Element).androidAttr("name") == MICROG_PACKAGE }) {
        queries.appendChild(document.createElement("package").apply {
            setAttributeNS(ANDROID_NS, "android:name", MICROG_PACKAGE)
        })
    }

    val expected = mapOf(
        "app.revanced.android.gms.SPOOFED_PACKAGE_NAME" to GENV_PACKAGE,
        "app.revanced.android.gms.SPOOFED_PACKAGE_SIGNATURE" to ORIGINAL_GENV_SIGNER_SHA1,
        "app.revanced.MICROG_PACKAGE_NAME" to MICROG_PACKAGE,
    )
    expected.forEach { (key, value) ->
        // Only direct application children can supply application metadata.
        val matching = (0 until application.childNodes.length).mapNotNull { application.childNodes.item(it) as? Element }
            .filter { it.tagName == "meta-data" && it.androidAttr("name") == key }
        require(matching.size <= 1 && (matching.isEmpty() || matching.single().androidAttr("value") == value)) {
            "Conflicting Morphe MicroG application metadata"
        }
        if (matching.isEmpty()) application.appendChild(document.createElement("meta-data").apply {
            setAttributeNS(ANDROID_NS, "android:name", key)
            setAttributeNS(ANDROID_NS, "android:value", value)
        })
    }

    // Match the action/permission namespace of Morphe MicroG's push service.
    // Do not change Java class names, Binder interface descriptors, IDs, or
    // arbitrary manifest attributes.
    val all = root.getElementsByTagName("*")
    val elements = (0 until all.length).map { all.item(it) as Element }
    val attributeNames = listOf("name", "permission", "readPermission", "writePermission")
    elements.forEach { element ->
        attributeNames.forEach { name ->
            val value = element.androidAttr(name)
            if (value.startsWith("com.google.android.c2dm.") ||
                value == "com.google.android.gtalkservice.permission.GTALK_SERVICE") {
                element.setAttributeNS(ANDROID_NS, "android:$name", value.replaceFirst("com.google", "app.revanced"))
            }
        }
    }
}

private val microgManifest = resourcePatch {
    execute { document("AndroidManifest.xml").use(::addMorpheMicroGManifestEntries) }
}

private data class RouteSite(val method: MutableMethod, val index: Int, val register: Int, val original: String)

/**
 * Exact 3.7.2 routing strings reviewed against the APK and Morphe MicroG-RE.
 * Binder descriptors, class names and arbitrary strings are deliberately absent.
 */
private val routeCounts = linkedMapOf(
    "com.google" to 7,
    "com.google.android.gms" to 44,
    "com.google.android.gms.auth.GOOGLE_SIGN_IN" to 2,
    "com.google.android.gms.auth.account.authapi.START" to 1,
    "com.google.android.gms.auth.api.credentials.service.START" to 1,
    "com.google.android.gms.auth.api.signin.service.START" to 1,
    "com.google.android.gms.signin.service.START" to 1,
    "com.google.android.gms.chimera" to 3,
    "com.google.android.gms.phenotype" to 4,
    "com.google.android.gms.common.telemetry.service.START" to 1,
    "com.google.android.gms.gass.START" to 1,
    "com.google.android.gms.measurement.START" to 3,
    "com.google.android.c2dm.intent.RECEIVE" to 2,
    "com.google.android.c2dm.intent.REGISTER" to 4,
    "com.google.android.c2dm.intent.REGISTRATION" to 1,
    "com.google.android.c2dm.permission.SEND" to 2,
    "com.google.android.gtalkservice.permission.GTALK_SERVICE" to 1,
    "content://com.google.android.gsf.gservices" to 2,
)

@Suppress("unused")
val morpheMicroGSupportPatch = bytecodePatch(
    name = "Morphe MicroG Google sign-in support (experimental)",
    description = "Route the reviewed GenV Google sign-in service and account type to MorpheApp MicroG-RE (app.revanced.android.gms). Requires a separately installed, compatible Morphe MicroG and complete GenV splits. OAuth, Firebase, server acceptance and real-device login are not guaranteed.",
    default = false,
) {
    dependsOn(genvExtension, microgManifest)
    compatibleWith(Compatibility(
        name = "GenV", packageName = GENV_PACKAGE,
        targets = listOf(AppTarget(version = "3.7.2", minSdk = 24, isExperimental = true)),
    ))
    execute {
        require(packageMetadata.packageName == GENV_PACKAGE && packageMetadata.versionName == "3.7.2" &&
            packageMetadata.versionCode == "163") {
            "Morphe MicroG support requires the reviewed GenV package, version 3.7.2 and build 163"
        }
        fun strings(method: com.android.tools.smali.dexlib2.iface.Method) = requireNotNull(method.implementation).instructions
            .mapNotNull { ((it as? ReferenceInstruction)?.reference as? StringReference)?.string }
        fun references(method: com.android.tools.smali.dexlib2.iface.Method) = requireNotNull(method.implementation).instructions
            .mapNotNull { (it as? ReferenceInstruction)?.reference as? MethodReference }
        fun reviewedMethod(owner: String, name: String, params: List<String>, result: String): MutableMethod =
            mutableClassDefBy(owner).methods.singleOrNull {
                it.name == name && it.returnType == result && it.parameterTypes.map { p -> p.toString() } == params
            } ?: error("Reviewed GenV auth method not found: $owner->$name")

        val availability = reviewedMethod("Li3/f;", "b", listOf("Landroid/content/Context;", "I"), "I")
        val body = requireNotNull(availability.implementation)
        require(AccessFlags.PUBLIC.isSet(availability.accessFlags) && !AccessFlags.STATIC.isSet(availability.accessFlags) &&
            body.registerCount == 12 && body.instructions.size == 284 &&
            body.instructions.take(3).map { it.opcode } == listOf(Opcode.SGET_OBJECT, Opcode.INVOKE_VIRTUAL, Opcode.MOVE_RESULT_OBJECT) &&
            strings(availability).containsAll(listOf("MetadataValueReader", "This should never happen.", "com.google.android.gms")) &&
            references(availability).any { it.definingClass == "Landroid/content/Context;" && it.name == "getPackageManager" }
        ) { "Reviewed Google Play Services availability implementation changed" }

        val servicePackage = reviewedMethod("Ll3/f;", "getStartServicePackage", emptyList(), "Ljava/lang/String;")
        val serviceAction = reviewedMethod("Lg3/e;", "getStartServiceAction", emptyList(), "Ljava/lang/String;")
        require(requireNotNull(servicePackage.implementation).instructions.map { it.opcode } == listOf(Opcode.CONST_STRING, Opcode.RETURN_OBJECT) &&
            strings(servicePackage).singleOrNull() == "com.google.android.gms" &&
            requireNotNull(serviceAction.implementation).instructions.map { it.opcode } == listOf(Opcode.CONST_STRING, Opcode.RETURN_OBJECT) &&
            strings(serviceAction).singleOrNull() == "com.google.android.gms.auth.api.signin.service.START"
        ) { "Reviewed Google sign-in service route changed" }

        val hub = reviewedMethod("Lcom/google/android/gms/auth/api/signin/internal/SignInHubActivity;", "onCreate", listOf("Landroid/os/Bundle;"), "V")
        require(requireNotNull(hub.implementation).instructions.size == 96 &&
            strings(hub).containsAll(listOf("com.google.android.gms", "com.google.android.gms.auth.GOOGLE_SIGN_IN")) &&
            references(hub).any { it.definingClass == "Landroid/content/Intent;" && it.name == "setPackage" }
        ) { "Reviewed Google sign-in activity route changed" }

        val sites = mutableListOf<RouteSite>()
        routeCounts.forEach { (original, expectedCount) ->
            val matches = mutableListOf<RouteSite>()
            classDefByStrings(original).forEach { clazz ->
                mutableClassDefBy(clazz).methods.forEach { method ->
                    method.implementation?.instructions?.forEachIndexed { index, instruction ->
                        val reference = (instruction as? ReferenceInstruction)?.reference as? StringReference
                        if (reference?.string == original) {
                            require(instruction.opcode == Opcode.CONST_STRING) { "Unexpected routing-string opcode" }
                            val register = (instruction as? OneRegisterInstruction)?.registerA
                                ?: error("Unexpected routing-string register")
                            matches.add(RouteSite(method, index, register, original))
                        }
                    }
                }
            }
            require(matches.size == expectedCount) { "Reviewed GenV routing sites changed for $original: ${matches.size}" }
            sites.addAll(matches)
        }
        sites.forEach { site ->
            val replacement = site.original.replaceFirst("com.google", "app.revanced")
            site.method.replaceInstruction(site.index, BuilderInstruction21c(
                Opcode.CONST_STRING, site.register, ImmutableStringReference(replacement),
            ))
        }
        // Return GMS success only when the separately installed Morphe MicroG
        // package has the reviewed signer and exports the sign-in service.
        // Otherwise execute GenV's original availability check unchanged.
        availability.addInstructionsWithLabels(0, """
            invoke-static/range {p1 .. p1}, $GUARD->isAvailable(Landroid/content/Context;)Z
            move-result v0
            if-eqz v0, :original_availability
            const/4 v0, 0x0
            return v0
            :original_availability
            nop
        """.trimIndent())
    }
}
