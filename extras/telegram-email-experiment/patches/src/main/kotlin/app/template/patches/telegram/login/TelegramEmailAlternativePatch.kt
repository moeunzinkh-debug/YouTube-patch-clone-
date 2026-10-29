package app.template.patches.telegram.login

import app.morphe.patcher.Fingerprint
import app.morphe.patcher.extensions.InstructionExtensions.addInstructions
import app.morphe.patcher.patch.PatchException
import app.morphe.patcher.patch.bytecodePatch
import app.template.patches.shared.Constants.TELEGRAM_COMPATIBILITY
import app.template.patches.shared.Constants.TELEGRAM_WEB_COMPATIBILITY
import app.template.patches.telegram.signature.telegramSpoofDependency

// This is a separate opt-in experiment, not an upstream rushiranpise patch.
// The exact Telegram 12.10.1 names are verified before injecting any code.
private val setupEmailParams = Fingerprint(
    definingClass = "Lorg/telegram/ui/LoginActivity\$LoginActivitySetupEmail;",
    name = "setParams",
    returnType = "V",
    parameters = listOf("Landroid/os/Bundle;", "Z"),
)

private val nextCodeParams = Fingerprint(
    definingClass = "Lorg/telegram/ui/LoginActivity;",
    name = "fillNextCodeParams",
    returnType = "V",
    parameters = listOf("Landroid/os/Bundle;", "Lorg/telegram/tgnet/TLRPC\$auth_SentCode;", "Z"),
)

private val nextCodeParamsShort = Fingerprint(
    definingClass = "Lorg/telegram/ui/LoginActivity;",
    name = "fillNextCodeParams",
    returnType = "V",
    parameters = listOf("Landroid/os/Bundle;", "Lorg/telegram/tgnet/TLRPC\$auth_SentCode;"),
)

private val resendConstructor = Fingerprint(
    definingClass = "Lorg/telegram/tgnet/TLRPC\$TL_auth_resendCode;",
    name = "<init>",
    returnType = "V",
    parameters = emptyList(),
)

private val sendRequest = Fingerprint(
    definingClass = "Lorg/telegram/tgnet/ConnectionsManager;",
    name = "sendRequest",
    returnType = "I",
    parameters = listOf("Lorg/telegram/tgnet/TLObject;", "Lorg/telegram/tgnet/RequestDelegate;", "I"),
)

private val cancelRequest = Fingerprint(
    definingClass = "Lorg/telegram/tgnet/ConnectionsManager;",
    name = "cancelRequest",
    returnType = "V",
    parameters = listOf("I", "Z"),
)

private val getConnections = Fingerprint(
    definingClass = "Lorg/telegram/ui/ActionBar/BaseFragment;",
    name = "getConnectionsManager",
    returnType = "Lorg/telegram/tgnet/ConnectionsManager;",
    parameters = emptyList(),
)

private val requestCallback = Fingerprint(
    definingClass = "Lorg/telegram/tgnet/RequestDelegate;",
    name = "run",
    returnType = "V",
    parameters = listOf("Lorg/telegram/tgnet/TLObject;", "Lorg/telegram/tgnet/TLRPC\$TL_error;"),
)

private val authSuccess = Fingerprint(
    definingClass = "Lorg/telegram/ui/LoginActivity;",
    name = "onAuthSuccess",
    returnType = "V",
    parameters = listOf("Lorg/telegram/tgnet/TLRPC\$TL_auth_authorization;"),
)

private val setPage = Fingerprint(
    definingClass = "Lorg/telegram/ui/LoginActivity;",
    name = "setPage",
    returnType = "V",
    parameters = listOf("I", "Z", "Landroid/os/Bundle;", "Z"),
)

private const val HOOK = "Lapp/template/extension/telegram/EmailAlternative;"

@Suppress("unused")
val telegramEmailAlternativePatch = bytecodePatch(
    name = "Try another login method (experimental)",
    description = "On Add Email, offers one manual retry only if Telegram supplies a phone-code next_type. " +
        "Waits for the server timeout. Telegram may refuse, require email or payment, or rate-limit. " +
        "No guarantee of SMS, free login, or bypass; normal email remains available.",
    default = false,
) {
    compatibleWith(TELEGRAM_COMPATIBILITY, TELEGRAM_WEB_COMPATIBILITY)
    dependsOn(telegramSpoofDependency())
    extendWith("extensions/extension.mpe")

    execute {
        val setup = setupEmailParams.originalClassDef
        val login = nextCodeParams.originalClassDef
        val resend = resendConstructor.originalClassDef
        val setupFields = setup.fields.map { it.name to it.type }.toSet()
        val loginFields = login.fields.map { it.name to it.type }.toSet()
        val resendFields = resend.fields.map { it.name to it.type }.toSet()
        if (!setupFields.containsAll(setOf(
                "this\$0" to "Lorg/telegram/ui/LoginActivity;",
                "currentParams" to "Landroid/os/Bundle;",
                "nextPressed" to "Z",
            )) || !loginFields.containsAll(setOf(
                "activityMode" to "I", "currentViewNum" to "I",
                "currentTermsOfService" to "Lorg/telegram/tgnet/TLRPC\$TL_help_termsOfService;",
            )) || !resendFields.containsAll(setOf(
                "phone_number" to "Ljava/lang/String;", "phone_code_hash" to "Ljava/lang/String;",
            ))) {
            throw PatchException("Telegram email-login internals do not match the tested 12.10.1 layout")
        }
        // Resolve all reflective entry points at patch time. If one is missing,
        // fail the selector instead of producing an APK that looks functional.
        nextCodeParamsShort.method
        sendRequest.method
        cancelRequest.method
        getConnections.method
        requestCallback.method
        authSuccess.method
        setPage.method

        // Observe the actual Telegram server response, not a possibly stale
        // Bundle nextType. The helper only records explicit non-email offers.
        nextCodeParams.method.addInstructions(0, """
            invoke-static/range {p1 .. p2}, $HOOK->observe(Landroid/os/Bundle;Ljava/lang/Object;)V
        """)
        // Keep the native Add Email UI intact; the helper may insert one
        // initially disabled, user-initiated alternative control.
        setupEmailParams.method.addInstructions(0, """
            invoke-static/range {p0 .. p1}, $HOOK->install(Landroid/view/View;Landroid/os/Bundle;)V
        """)
    }
}
