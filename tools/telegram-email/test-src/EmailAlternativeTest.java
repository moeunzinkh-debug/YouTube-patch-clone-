import android.app.AlertDialog;
import android.os.Bundle;
import android.os.Handler;
import android.view.View;
import android.widget.TextView;
import android.widget.Toast;
import app.template.extension.telegram.EmailAlternative;
import org.telegram.tgnet.TLRPC;
import org.telegram.ui.LoginActivity;

/** Synthetic-only JVM tests. They send no network traffic and use no real account data. */
public final class EmailAlternativeTest {
    private static final String PREFIX = "morphe.telegram.email_alternative.";
    private static int checks;
    private static void check(boolean condition, String what) {
        checks++;
        if (!condition) throw new AssertionError(what);
    }

    private static Bundle params() {
        Bundle b = new Bundle();
        b.putString("phone", "TEST-DISPLAY");
        b.putString("ephone", "TEST-DISPLAY");
        b.putString("phoneFormated", "TEST-PHONE");
        return b;
    }

    private static TLRPC.TL_auth_sentCode response(Object next, int timeout) {
        TLRPC.TL_auth_sentCode r = new TLRPC.TL_auth_sentCode();
        r.flags = 2 | 4;
        r.type = new TLRPC.TL_auth_sentCodeTypeSetUpEmailRequired();
        r.next_type = next;
        r.phone_code_hash = "TEST-HASH";
        r.timeout = timeout;
        return r;
    }

    private static final class Fixture {
        final LoginActivity login = new LoginActivity();
        final LoginActivity.LoginActivitySetupEmail screen = login.new LoginActivitySetupEmail();
        final Bundle params = params();
        TLRPC.TL_auth_sentCode sent;
        TextView button;
        Fixture(Object next, int timeout) {
            Handler.reset(); AlertDialog.last = null; Toast.last = null;
            sent = response(next, timeout);
            EmailAlternative.observe(params, sent);
            params.putString("phoneHash", sent.phone_code_hash); // Telegram's native code does this.
            screen.setParams(params);
            if (screen.getChildCount() > 0) button = (TextView) screen.getChildAt(0);
        }
        void readyAndConfirm() {
            Handler.advance(60000);
            check(button != null && button.getVisibility() == View.VISIBLE && button.isEnabled(), "button ready");
            check(button.performClick(), "button clicked");
            check(AlertDialog.last != null, "explicit confirmation dialog");
            AlertDialog.last.accept();
        }
    }

    private static void noOfferTests() {
        Fixture a = new Fixture(null, 5);
        check(a.button == null && a.login.manager.sends == 0, "no server next type, no button");
        Fixture b = new Fixture(new TLRPC.TL_auth_codeTypeFragmentSms(), 5);
        check(b.button == null, "Fragment is not presented as a phone OTP");
        Fixture c = new Fixture(new TLRPC.TL_auth_codeTypeSms(), 5);
        Bundle stale = params();
        stale.putInt("nextType", 2);
        TLRPC.TL_auth_sentCode noFlag = response(new TLRPC.TL_auth_codeTypeSms(), 5);
        noFlag.flags = 4; // non-null field alone must not override the server TL flags.
        EmailAlternative.observe(stale, noFlag);
        stale.putString("phoneHash", noFlag.phone_code_hash);
        c.screen.setParams(stale);
        check(c.button.getVisibility() == View.GONE, "no server next_type flag, no stale alternative");
        TLRPC.TL_auth_sentCode emailCode = response(new TLRPC.TL_auth_codeTypeSms(), 5);
        emailCode.type = new TLRPC.TL_auth_sentCodeTypeEmailCode();
        EmailAlternative.observe(stale, emailCode);
        c.screen.setParams(stale);
        check(c.button.getVisibility() == View.GONE, "existing-email code is not Add Email setup");
        TLRPC.TL_auth_sentCode huge = response(new TLRPC.TL_auth_codeTypeSms(), 2_147_484);
        EmailAlternative.observe(stale, huge);
        c.screen.setParams(stale);
        check(c.button.getVisibility() == View.GONE, "timeout is never shortened on overflow");
        Fixture mode = new Fixture(new TLRPC.TL_auth_codeTypeCall(), 5);
        mode.login.changeMode(3);
        mode.screen.setParams(mode.params);
        check(mode.button.getVisibility() == View.GONE, "email changes are excluded");
    }

    private static void offerAndErrorTests() {
        Object[] types = { new TLRPC.TL_auth_codeTypeSms(), new TLRPC.TL_auth_codeTypeFlashCall(),
                new TLRPC.TL_auth_codeTypeCall(), new TLRPC.TL_auth_codeTypeMissedCall() };
        for (Object type : types) {
            Fixture f = new Fixture(type, 5);
            check(f.button != null && !f.button.isEnabled(), "supported offer starts disabled");
            Handler.advance(4999);
            check(!f.button.isEnabled() && f.login.manager.sends == 0, "no early resend");
            Handler.advance(1);
            check(f.button.isEnabled(), "enabled only after server timeout");
            f.button.performClick();
            AlertDialog.last.cancel();
            check(f.login.manager.sends == 0, "cancel confirmation sends nothing");
            f.button.performClick(); AlertDialog.last.accept();
            check(f.login.manager.sends == 1 && f.login.manager.flags == 10, "one native resend request");
            TLRPC.TL_auth_resendCode req = (TLRPC.TL_auth_resendCode) f.login.manager.lastRequest;
            check("TEST-PHONE".equals(req.phone_number) && "TEST-HASH".equals(req.phone_code_hash), "request uses current challenge");
            check(f.screen.busy(), "native email submission guarded while request is in flight");
            f.login.manager.respond(null, new TLRPC.TL_error()); Handler.runDue();
            check(!f.screen.busy() && f.login.page() == 12 && f.login.fills == 0, "error preserves Add Email control");
            check(!f.button.isEnabled() && Toast.last != null, "single attempt, visible error");
            f.screen.setParams(f.params);
            check(f.button.getVisibility() == View.GONE, "attempt marker prevents retry loop");
        }
        Fixture defaultWait = new Fixture(new TLRPC.TL_auth_codeTypeSms(), 0);
        Handler.advance(59999); check(!defaultWait.button.isEnabled(), "default waits full 60 seconds");
        Handler.advance(1); check(defaultWait.button.isEnabled(), "default wait finishes");
        Fixture restored = new Fixture(new TLRPC.TL_auth_codeTypeSms(), 5);
        restored.params.remove(PREFIX + "started_elapsed");
        Handler.advance(3000);
        restored.screen.setParams(restored.params);
        Handler.advance(4999); check(!restored.button.isEnabled(), "restored state waits a full period");
        Handler.advance(1); check(restored.button.isEnabled(), "restored wait eventually finishes");
    }

    private static void serverResponseTests() {
        Fixture normal = new Fixture(new TLRPC.TL_auth_codeTypeSms(), 5);
        normal.params.putInt("nextType", 4); // Stale value must not propagate to the next challenge.
        normal.readyAndConfirm();
        TLRPC.TL_auth_sentCode another = response(new TLRPC.TL_auth_codeTypeCall(), 5);
        normal.login.manager.respond(another, null); Handler.runDue();
        check(normal.login.fills == 1 && normal.login.lastResponse == another, "native handler receives actual sent-code response");
        check(!normal.login.lastParams.containsKey("nextType"), "fresh Bundle avoids stale next type");
        check(normal.login.lastParams.getBoolean(PREFIX + "attempted", false), "one-shot marker propagated");
        check(!normal.login.lastParams.containsKey(PREFIX + "offer"), "no new offer after one retry");

        Fixture payment = new Fixture(new TLRPC.TL_auth_codeTypeCall(), 5);
        payment.readyAndConfirm();
        TLRPC.TL_auth_sentCodePaymentRequired pay = new TLRPC.TL_auth_sentCodePaymentRequired();
        payment.login.manager.respond(pay, null); Handler.runDue();
        check(payment.login.lastResponse == pay && payment.login.fills == 1, "payment is handed to Telegram, not hidden");

        Fixture signup = new Fixture(new TLRPC.TL_auth_codeTypeSms(), 5);
        signup.readyAndConfirm();
        TLRPC.TL_auth_sentCodeSuccess success = new TLRPC.TL_auth_sentCodeSuccess();
        TLRPC.TL_auth_authorizationSignUpRequired auth = new TLRPC.TL_auth_authorizationSignUpRequired();
        auth.terms_of_service = new TLRPC.TL_help_termsOfService(); success.authorization = auth;
        signup.login.manager.respond(success, null); Handler.runDue();
        check(signup.login.page() == 5 && signup.login.terms() == auth.terms_of_service, "native signup and terms preserved");

        Fixture authorized = new Fixture(new TLRPC.TL_auth_codeTypeSms(), 5);
        authorized.readyAndConfirm();
        TLRPC.TL_auth_sentCodeSuccess done = new TLRPC.TL_auth_sentCodeSuccess();
        done.authorization = new TLRPC.TL_auth_authorization();
        authorized.login.manager.respond(done, null); Handler.runDue();
        check(authorized.login.successes == 1, "actual authorization handed to native login handler");
    }

    private static void lifecycleTests() {
        Fixture away = new Fixture(new TLRPC.TL_auth_codeTypeSms(), 5);
        away.readyAndConfirm(); away.login.page(0);
        away.login.manager.respond(response(null, 0), null); Handler.runDue();
        check(!away.screen.busy() && away.login.fills == 0, "late result cannot navigate over another page");
        Fixture timeout = new Fixture(new TLRPC.TL_auth_codeTypeSms(), 5);
        timeout.readyAndConfirm(); Handler.advance(90000);
        check(timeout.login.manager.cancels == 1 && !timeout.screen.busy(), "timeout cancels and releases guard");
        timeout.login.manager.respond(response(null, 0), null); Handler.runDue();
        check(timeout.login.fills == 0, "callback after timeout ignored");
        Fixture reuse = new Fixture(new TLRPC.TL_auth_codeTypeSms(), 5);
        reuse.readyAndConfirm();
        Bundle replacement = params();
        reuse.screen.setParams(replacement);
        check(reuse.login.manager.cancels == 1 && !reuse.screen.busy(), "reusing view cancels and unlocks prior request");
        reuse.login.manager.respond(response(null, 0), null); Handler.runDue();
        check(reuse.login.fills == 0, "old response cannot change replacement screen");
        Fixture busy = new Fixture(new TLRPC.TL_auth_codeTypeSms(), 5);
        Handler.advance(5000); busy.screen.busy(true); busy.button.performClick(); AlertDialog.last.accept();
        check(busy.login.manager.sends == 0 && busy.screen.busy(), "existing email request is not overwritten");
    }

    public static void main(String[] args) throws Exception {
        check(LoginActivity.LoginActivitySetupEmail.class.getDeclaredField("this$0") != null,
                "test stub must preserve the real view's outer-instance field");
        noOfferTests(); offerAndErrorTests(); serverResponseTests(); lifecycleTests();
        System.out.println("EmailAlternative synthetic JVM checks passed: " + checks);
    }
}
