package org.microg.gms.auth.signin;

import android.app.Service;
import android.content.Intent;
import android.os.Binder;
import android.os.IBinder;

/** Wrong-signer fake for negative discovery tests only; contains no accounts. */
public final class AuthSignInService extends Service {
    @Override public IBinder onBind(Intent intent) { return new Binder(); }
}
