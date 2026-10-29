package app.morphe.telegramemailtest;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.Context;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;

import java.lang.reflect.Array;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.concurrent.atomic.AtomicReference;

/**
 * Test-only instrumentation APK. It constructs synthetic Telegram TL objects
 * and Add Email UI locally, without any account, OTP, or network request.
 */
public final class SyntheticEmailHarness extends Instrumentation {
    private final AtomicReference<Throwable> failure = new AtomicReference<>();
    private View experimentButton;

    @Override public void onCreate(Bundle arguments) {
        super.onCreate(arguments);
        start();
    }

    private static Field field(Class<?> owner, String name) throws Exception {
        Field f = owner.getDeclaredField(name);
        f.setAccessible(true);
        return f;
    }

    private void onUi(Checked task) {
        runOnMainSync(() -> {
            try { task.run(); } catch (Throwable t) { failure.compareAndSet(null, t); }
        });
        Throwable t = failure.get();
        if (t != null) throw new RuntimeException(t);
    }

    private interface Checked { void run() throws Exception; }

    private static void check(boolean condition, String label) {
        if (!condition) throw new AssertionError(label);
    }

    private static View experiment(ViewGroup group) {
        for (int i = 0; i < group.getChildCount(); i++) {
            View child = group.getChildAt(i);
            Object tag = child.getTag();
            if (tag != null && tag.getClass().getName().equals("app.template.extension.telegram.EmailAlternative$State")) {
                return child;
            }
        }
        return null;
    }

    @Override public void onStart() {
        Bundle report = new Bundle();
        try {
            ClassLoader cl = getTargetContext().getClassLoader();
            Class<?> loginClass = Class.forName("org.telegram.ui.LoginActivity", true, cl);
            Class<?> setupClass = Class.forName("org.telegram.ui.LoginActivity$LoginActivitySetupEmail", true, cl);
            Class<?> base = Class.forName("org.telegram.tgnet.TLRPC$auth_SentCode", true, cl);
            Class<?> sentClass = Class.forName("org.telegram.tgnet.TLRPC$TL_auth_sentCode", true, cl);
            Class<?> requiredClass = Class.forName("org.telegram.tgnet.TLRPC$TL_auth_sentCodeTypeSetUpEmailRequired", true, cl);
            Class<?> smsClass = Class.forName("org.telegram.tgnet.TLRPC$TL_auth_codeTypeSms", true, cl);
            Class<?> helper = Class.forName("app.template.extension.telegram.EmailAlternative", true, cl);
            Method observe = helper.getMethod("observe", Bundle.class, Object.class);
            Method setParams = setupClass.getMethod("setParams", Bundle.class, boolean.class);

            onUi(() -> {
                Object login = loginClass.getConstructor().newInstance();
                ViewGroup screen = (ViewGroup) setupClass.getConstructor(loginClass, Context.class)
                        .newInstance(login, getTargetContext());
                Object views = field(loginClass, "views").get(login);
                Array.set(views, 12, screen);
                field(loginClass, "currentViewNum").setInt(login, 12);

                Object sent = sentClass.getConstructor().newInstance();
                base.getField("flags").setInt(sent, 6);
                base.getField("type").set(sent, requiredClass.getConstructor().newInstance());
                base.getField("phone_code_hash").set(sent, "TEST-HASH");
                base.getField("timeout").setInt(sent, 1);
                Bundle params = new Bundle();
                params.putString("phone", "TEST-DISPLAY");
                params.putString("ephone", "TEST-DISPLAY");
                params.putString("phoneFormated", "TEST-PHONE");
                params.putString("phoneHash", "TEST-HASH");

                int nativeChildren = screen.getChildCount();
                observe.invoke(null, params, sent); // next_type is null: no server offer.
                setParams.invoke(screen, params, false);
                check(screen.getChildCount() == nativeChildren && experiment(screen) == null, "no-offer fallback");

                base.getField("next_type").set(sent, smsClass.getConstructor().newInstance());
                observe.invoke(null, params, sent); // synthetic server explicitly offers SMS.
                setParams.invoke(screen, params, false); // executes the real injected bytecode.
                experimentButton = experiment(screen);
                check(experimentButton != null && screen.getChildCount() == nativeChildren + 1, "offered button");
                check(!experimentButton.isEnabled(), "server wait enforced");
            });
            Thread.sleep(1600);
            onUi(() -> check(experimentButton != null && experimentButton.isEnabled(), "button enabled after timeout"));
            report.putString("synthetic_email_ui", "passed_no_offer_and_server_offered_timeout");
            report.putString("account_and_login_requests", "not_used_by_test");
            finish(Activity.RESULT_OK, report);
        } catch (Throwable t) {
            report.putString("synthetic_email_ui", "failed");
            report.putString("error_class", t.getClass().getName());
            report.putString("error", String.valueOf(t.getCause() != null ? t.getCause() : t));
            finish(Activity.RESULT_CANCELED, report);
        }
    }
}
