package app.template.extension.telegram;

import android.app.Activity;
import android.app.AlertDialog;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.util.Locale;

/**
 * Opt-in experiment for Telegram 12.10.1. Nothing is sent without an explicit
 * server-provided next_type, its waiting period, and a user confirmation.
 * Normal Add Email, verification, payment and account-reset logic stay intact.
 * This class never logs phone numbers, hashes, codes, errors, or server objects.
 */
public final class EmailAlternative {
    private EmailAlternative() { }

    private static final String PREFIX = "morphe.telegram.email_alternative.";
    private static final String OFFER = PREFIX + "offer";
    private static final String WAIT_MS = PREFIX + "wait_ms";
    private static final String STARTED = PREFIX + "started_elapsed";
    private static final String ATTEMPTED = PREFIX + "attempted";
    private static final int LOGIN_MODE = 0;
    private static final int ADD_EMAIL_PAGE = 12;
    private static final int REGISTER_PAGE = 5;
    private static final int REQUEST_FLAGS = 2 | 8; // Same flags as Telegram's email-code resend.
    private static final long REQUEST_LIMIT_MS = 90_000L;
    private static final Handler MAIN = new Handler(Looper.getMainLooper());

    private static boolean is(Object value, String nestedName) throws Exception {
        return value != null && Class.forName("org.telegram.tgnet.TLRPC$" + nestedName).isInstance(value);
    }

    private static int phoneOffer(Object next) throws Exception {
        if (is(next, "TL_auth_codeTypeSms")) return 2;
        if (is(next, "TL_auth_codeTypeFlashCall")) return 3;
        if (is(next, "TL_auth_codeTypeCall")) return 4;
        if (is(next, "TL_auth_codeTypeMissedCall")) return 11;
        // Fragment and unknown methods are deliberately not presented as phone OTP.
        return 0;
    }

    /** Called at the start of the real, three-argument fillNextCodeParams. */
    public static void observe(Bundle params, Object response) {
        if (params == null) return;
        // Do not trust Telegram's possibly stale "nextType" in a reused Bundle.
        params.remove(OFFER);
        params.remove(WAIT_MS);
        params.remove(STARTED);
        try {
            if (params.getBoolean(ATTEMPTED, false) || !is(response, "TL_auth_sentCode")) return;
            Class<?> sent = Class.forName("org.telegram.tgnet.TLRPC$auth_SentCode");
            Object type = sent.getField("type").get(response);
            int flags = sent.getField("flags").getInt(response);
            if (!is(type, "TL_auth_sentCodeTypeSetUpEmailRequired") || (flags & 2) == 0) return;
            String hash = (String) sent.getField("phone_code_hash").get(response);
            int offer = phoneOffer(sent.getField("next_type").get(response));
            if (offer == 0 || hash == null || hash.isEmpty()) return;

            int seconds = (flags & 4) != 0 ? sent.getField("timeout").getInt(response) : 0;
            // Telegram itself uses 60 seconds if a timeout is not supplied/zero.
            long millis = seconds > 0 ? (long) seconds * 1000L : 60_000L;
            // Bundle persistence in this Telegram version preserves ints, not longs.
            // Oversized timeouts are ignored rather than shortened.
            if (millis > Integer.MAX_VALUE) return;
            params.putInt(OFFER, offer);
            params.putInt(WAIT_MS, (int) millis);
            params.putLong(STARTED, SystemClock.elapsedRealtime());
        } catch (Throwable ignored) {
            // Fail open: let the unmodified login screen handle the response.
            params.remove(OFFER);
            params.remove(WAIT_MS);
            params.remove(STARTED);
        }
    }

    private static Field privateField(Class<?> owner, String name) throws Exception {
        Field field = owner.getDeclaredField(name);
        field.setAccessible(true);
        return field;
    }

    private static Method privateMethod(Class<?> owner, String name, Class<?>... parameters) throws Exception {
        Method method = owner.getDeclaredMethod(name, parameters);
        method.setAccessible(true);
        return method;
    }

    private static final class Api {
        final Class<?> loginClass, sentBase, sent, payment, success, signUp, authorized, delegate;
        final Field outer, currentParams, nextPressed, mode, page, terms;
        final Method connections, parent, send, cancel, fill, onSuccess, setPage;
        final Class<?> resend;

        Api(View view) throws Exception {
            loginClass = Class.forName("org.telegram.ui.LoginActivity");
            Class<?> setup = Class.forName("org.telegram.ui.LoginActivity$LoginActivitySetupEmail");
            if (!setup.isInstance(view)) throw new IllegalArgumentException();
            outer = privateField(setup, "this$0");
            currentParams = privateField(setup, "currentParams");
            nextPressed = privateField(setup, "nextPressed");
            mode = privateField(loginClass, "activityMode");
            page = privateField(loginClass, "currentViewNum");
            terms = privateField(loginClass, "currentTermsOfService");
            connections = loginClass.getMethod("getConnectionsManager");
            parent = loginClass.getMethod("getParentActivity");
            sentBase = Class.forName("org.telegram.tgnet.TLRPC$auth_SentCode");
            sent = Class.forName("org.telegram.tgnet.TLRPC$TL_auth_sentCode");
            payment = Class.forName("org.telegram.tgnet.TLRPC$TL_auth_sentCodePaymentRequired");
            success = Class.forName("org.telegram.tgnet.TLRPC$TL_auth_sentCodeSuccess");
            signUp = Class.forName("org.telegram.tgnet.TLRPC$TL_auth_authorizationSignUpRequired");
            authorized = Class.forName("org.telegram.tgnet.TLRPC$TL_auth_authorization");
            delegate = Class.forName("org.telegram.tgnet.RequestDelegate");
            resend = Class.forName("org.telegram.tgnet.TLRPC$TL_auth_resendCode");
            Class<?> object = Class.forName("org.telegram.tgnet.TLObject");
            Class<?> manager = Class.forName("org.telegram.tgnet.ConnectionsManager");
            send = manager.getMethod("sendRequest", object, delegate, int.class);
            cancel = manager.getMethod("cancelRequest", int.class, boolean.class);
            fill = privateMethod(loginClass, "fillNextCodeParams", Bundle.class, sentBase);
            onSuccess = privateMethod(loginClass, "onAuthSuccess", authorized);
            setPage = loginClass.getMethod("setPage", int.class, boolean.class, Bundle.class, boolean.class);
            // Resolve every field used later before adding a visible control.
            resend.getConstructor();
            resend.getField("phone_number");
            resend.getField("phone_code_hash");
            sentBase.getField("authorization");
            signUp.getField("terms_of_service");
        }
    }

    private static final class State {
        final Api api;
        final ViewGroup screen;
        final TextView button;
        final Bundle params;
        final Object login;
        final long deadline;
        boolean inFlight, ownsGuard;
        Object manager;
        int token;

        State(Api api, ViewGroup screen, TextView button, Bundle params, Object login, long deadline) {
            this.api = api;
            this.screen = screen;
            this.button = button;
            this.params = params;
            this.login = login;
            this.deadline = deadline;
        }
    }

    private static TextView existing(ViewGroup screen) {
        for (int i = 0; i < screen.getChildCount(); i++) {
            View child = screen.getChildAt(i);
            if (child instanceof TextView && child.getTag() instanceof State) return (TextView) child;
        }
        return null;
    }

    /** Called at the start of LoginActivitySetupEmail.setParams. */
    public static void install(View view, Bundle params) {
        if (!(view instanceof LinearLayout)) return;
        ViewGroup screen = (ViewGroup) view;
        TextView button = existing(screen);
        try {
            if (button != null) {
                State old = (State) button.getTag();
                abandon(old);
                button.setVisibility(View.GONE);
                button.setTag(null);
            }
            if (params == null || params.getBoolean(ATTEMPTED, false) || params.getInt(OFFER, 0) == 0 ||
                    params.getInt(WAIT_MS, 0) <= 0 || empty(params.getString("phoneFormated")) ||
                    empty(params.getString("phoneHash"))) return;
            Api api = new Api(view);
            Object login = api.outer.get(view);
            if (!api.loginClass.isInstance(login) || api.mode.getInt(login) != LOGIN_MODE) return;

            long now = SystemClock.elapsedRealtime();
            long started = params.getLong(STARTED, -1L);
            // If state was restored (or the phone rebooted), wait the full time.
            if (started < 0 || started > now) {
                started = now;
                params.putLong(STARTED, now);
            }
            long deadline = started + params.getInt(WAIT_MS);
            if (button == null) {
                button = new TextView(screen.getContext());
                button.setGravity(Gravity.CENTER);
                button.setTextSize(14);
                button.setTextColor(0xff168ac8);
                int pad = (int) (12 * screen.getResources().getDisplayMetrics().density + 0.5f);
                button.setPadding(pad, pad, pad, pad);
                button.setMinimumHeight((int) (48 * screen.getResources().getDisplayMetrics().density + 0.5f));
                // After the native email input, before its flexible bottom spacer.
                screen.addView(button, Math.min(4, screen.getChildCount()),
                        new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
            }
            State state = new State(api, screen, button, params, login, deadline);
            button.setTag(state);
            button.setVisibility(View.VISIBLE);
            button.setText(text("សាកវិធីទទួលកូដផ្សេង (ត្រូវរង់ចាំ)", "Try another code method (after waiting)"));
            button.setOnClickListener(ignored -> confirm(state));
            updateButton(state);
        } catch (Throwable ignored) {
            // Keep Add Email usable if an APK implementation differs.
            if (button != null) {
                button.setTag(null);
                button.setVisibility(View.GONE);
            }
        }
    }

    private static boolean empty(String value) { return value == null || value.isEmpty(); }
    private static String text(String khmer, String english) {
        return "km".equals(Locale.getDefault().getLanguage()) ? khmer : english;
    }

    private static boolean current(State s) {
        try {
            return s.button.getTag() == s && s.api.page.getInt(s.login) == ADD_EMAIL_PAGE &&
                    s.api.mode.getInt(s.login) == LOGIN_MODE && s.api.currentParams.get(s.screen) == s.params;
        } catch (Throwable ignored) {
            return false;
        }
    }

    private static void updateButton(State s) {
        if (s.button.getTag() != s || s.params.getBoolean(ATTEMPTED, false)) return;
        long remaining = s.deadline - SystemClock.elapsedRealtime();
        boolean ready = remaining <= 0;
        s.button.setEnabled(ready && !s.inFlight);
        s.button.setAlpha(ready && !s.inFlight ? 1f : 0.5f);
        if (!ready) {
            // One scheduled update at the deadline, not repeated network traffic.
            MAIN.postDelayed(() -> updateButton(s), remaining);
        }
    }

    private static void confirm(State s) {
        if (!current(s) || s.inFlight || s.params.getBoolean(ATTEMPTED, false) ||
                SystemClock.elapsedRealtime() < s.deadline) return;
        try {
            Activity activity = (Activity) s.api.parent.invoke(s.login);
            if (activity == null || activity.isFinishing()) return;
            new AlertDialog.Builder(activity)
                    .setTitle(text("សាកវិធីកូដផ្សេង?", "Try another code method?"))
                    .setMessage(text(
                            "Telegram ជាអ្នកសម្រេចវិធី និងអាចបដិសេធ ស្នើ email ឬគិតថ្លៃ។ ការស្នើញឹកញាប់អាចជាប់កំណត់។",
                            "Telegram decides the next method and may refuse, require email or charge a fee. Repeated requests can be rate-limited."))
                    .setNegativeButton(text("បោះបង់", "Cancel"), (dialog, which) -> { })
                    .setPositiveButton(text("សាកម្ដង", "Try once"), (dialog, which) -> begin(s))
                    .show();
        } catch (Throwable ignored) {
            message(s, text("មិនអាចសាកបាន។ សូមបន្តតាម email ឬត្រឡប់ក្រោយ។",
                    "Could not try this method. Continue with email or go back."));
        }
    }

    private static void begin(State s) {
        if (!current(s) || s.inFlight || s.params.getBoolean(ATTEMPTED, false) ||
                SystemClock.elapsedRealtime() < s.deadline) return;
        try {
            if (s.api.nextPressed.getBoolean(s.screen)) {
                message(s, text("សូមរង់ចាំសំណើបច្ចុប្បន្ន។", "Please wait for the current request."));
                return;
            }
            Object request = s.api.resend.getConstructor().newInstance();
            s.api.resend.getField("phone_number").set(request, s.params.getString("phoneFormated"));
            s.api.resend.getField("phone_code_hash").set(request, s.params.getString("phoneHash"));
            Object manager = s.api.connections.invoke(s.login);
            if (manager == null) throw new IllegalStateException();
            Object callback = Proxy.newProxyInstance(s.api.delegate.getClassLoader(), new Class<?>[]{s.api.delegate},
                    (proxy, method, args) -> {
                        if (method.getName().equals("run") && args != null && args.length == 2) {
                            Object response = args[0], error = args[1];
                            MAIN.post(() -> finish(s, response, error));
                            return null;
                        }
                        if (method.getName().equals("hashCode")) return System.identityHashCode(proxy);
                        if (method.getName().equals("equals")) return proxy == args[0];
                        if (method.getName().equals("toString")) return "EmailAlternative callback";
                        return null;
                    });
            s.params.putBoolean(ATTEMPTED, true);
            s.inFlight = true;
            s.ownsGuard = true;
            s.api.nextPressed.setBoolean(s.screen, true);
            s.manager = manager;
            s.button.setEnabled(false);
            s.button.setAlpha(0.5f);
            s.token = (Integer) s.api.send.invoke(manager, request, callback, REQUEST_FLAGS);
            MAIN.postDelayed(() -> {
                if (!s.inFlight) return;
                abandon(s);
                if (current(s)) message(s, text("សំណើអស់ពេល។ សូមបន្តតាម email ឬត្រឡប់ក្រោយ។",
                        "Request timed out. Continue with email or go back."));
            }, REQUEST_LIMIT_MS);
        } catch (Throwable ignored) {
            abandon(s);
            message(s, text("សំណើមិនជោគជ័យ។ សូមបន្តតាម email ឬត្រឡប់ក្រោយ។",
                    "Request failed. Continue with email or go back."));
        }
    }

    private static void releaseGuard(State s) {
        if (s.ownsGuard) {
            try { s.api.nextPressed.setBoolean(s.screen, false); } catch (Throwable ignored) { }
            s.ownsGuard = false;
        }
    }

    private static void abandon(State s) {
        if (s.inFlight) {
            s.inFlight = false;
            try {
                if (s.manager != null && s.token != 0) s.api.cancel.invoke(s.manager, s.token, true);
            } catch (Throwable ignored) { }
        }
        releaseGuard(s);
    }

    private static void finish(State s, Object response, Object error) {
        if (!s.inFlight) return; // Ignore late callbacks after cancellation/timeout.
        s.inFlight = false;
        releaseGuard(s);
        if (!current(s)) return; // Never navigate over another screen.
        if (error != null || response == null) {
            message(s, text("Telegram មិនទទួលយកជម្រើសនេះទេ។ សូមបន្តតាម email ឬរង់ចាំ។",
                    "Telegram did not accept this alternative. Continue with email or wait."));
            return;
        }
        try {
            Bundle next = new Bundle();
            next.putString("phone", s.params.getString("phone"));
            next.putString("ephone", s.params.getString("ephone"));
            next.putString("phoneFormated", s.params.getString("phoneFormated"));
            // Never loop retries even if Telegram returns another Add Email response.
            next.putBoolean(ATTEMPTED, true);
            if (s.api.sent.isInstance(response) || s.api.payment.isInstance(response)) {
                // Telegram's native handler decides which actual screen to show,
                // including the payment screen when the server requires payment.
                s.api.fill.invoke(s.login, next, response);
            } else if (s.api.success.isInstance(response)) {
                Object authorization = s.api.sentBase.getField("authorization").get(response);
                if (s.api.signUp.isInstance(authorization)) {
                    Object terms = s.api.signUp.getField("terms_of_service").get(authorization);
                    if (terms != null) s.api.terms.set(s.login, terms);
                    s.api.setPage.invoke(s.login, REGISTER_PAGE, true, next, false);
                } else if (s.api.authorized.isInstance(authorization)) {
                    s.api.onSuccess.invoke(s.login, authorization);
                } else {
                    message(s, text("ចម្លើយមិនស្គាល់។ សូមត្រឡប់ក្រោយ។", "Unexpected response. Please go back."));
                }
            } else {
                message(s, text("ចម្លើយមិនស្គាល់។ សូមត្រឡប់ក្រោយ។", "Unexpected response. Please go back."));
            }
        } catch (Throwable ignored) {
            message(s, text("មិនអាចបន្តបាន។ សូមត្រឡប់ក្រោយ ហើយសាកម្ដងទៀតពេលក្រោយ។",
                    "Could not continue. Go back and try again later."));
        }
    }

    private static void message(State s, String message) {
        try {
            Activity activity = (Activity) s.api.parent.invoke(s.login);
            if (activity != null && !activity.isFinishing()) Toast.makeText(activity, message, Toast.LENGTH_LONG).show();
        } catch (Throwable ignored) { }
    }
}
