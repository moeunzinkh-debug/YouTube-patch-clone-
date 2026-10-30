/* Copyright (C) 2026. This fork is distributed under GPL-3.0-or-later. */
package app.morphe.extension.instanttranslate;

import android.content.Context;
import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.AtomicFile;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import java.util.Arrays;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/** Local provider settings. The API key is encrypted and excluded from Android backup. */
final class ProviderSettings {
    private static final String PREFS = "morphe_instant_translate_settings";
    private static final String ALIAS = "morphe.instanttranslate.sealion.key.v1";
    private static final String SECRET = "morphe-instant-sealion-key.v1";
    private static final Object LOCK = new Object();
    private static volatile Context appContext;

    private ProviderSettings() {}

    static void initialize(Context context) {
        if (context == null) return;
        Context application = context.getApplicationContext();
        if (application != null) appContext = application;
    }

    static Context context() { return appContext; }
    private static SharedPreferences prefs(Context context) { return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE); }

    static String selected() {
        Context context = appContext;
        // The original standalone patch explicitly selected Google before this
        // settings patch existed; retain that behavior when no settings UI exists.
        if (context == null) return ProviderRouter.GOOGLE;
        String value = prefs(context).getString("provider", ProviderRouter.GOOGLE);
        if (ProviderRouter.GOOGLE.equals(value) || ProviderRouter.SEA_LION.equals(value) || ProviderRouter.ORIGINAL.equals(value)) return value;
        return ProviderRouter.ORIGINAL;
    }

    static String name(Context context) { return prefs(context).getString("name", SeaLionClient.DEFAULT_NAME); }
    static String base(Context context) { return prefs(context).getString("base", SeaLionClient.DEFAULT_BASE); }
    static String model(Context context) { return prefs(context).getString("model", SeaLionClient.DEFAULT_MODEL); }
    static boolean hasKey(Context context) { return new File(context.getNoBackupFilesDir(), SECRET).isFile(); }

    static SeaLionClient.Config seaLionConfig() throws IOException {
        synchronized (LOCK) {
            Context context = appContext;
            if (context == null || !ProviderRouter.SEA_LION.equals(selected())) throw new IOException("Provider not selected");
            // Keep endpoint, model and encrypted key consistent if settings are
            // edited while background translations are running.
            return new SeaLionClient.Config(base(context), model(context), readSecret(context));
        }
    }

    static void save(Context context, String provider, String name, String base, String model, String newKey) throws IOException {
        if (context == null || !(ProviderRouter.ORIGINAL.equals(provider) || ProviderRouter.GOOGLE.equals(provider) || ProviderRouter.SEA_LION.equals(provider))) {
            throw new IOException("Invalid provider");
        }
        // Switching back to Original or Google must remain possible even if the
        // stored SEA-LION fields are invalid or the keystore is unavailable.
        if (!ProviderRouter.SEA_LION.equals(provider)) {
            synchronized (LOCK) {
                if (!prefs(context).edit().putString("provider", provider).commit()) {
                    throw new IOException("Settings could not be saved");
                }
            }
            return;
        }
        if (name == null || name.trim().isEmpty() || name.length() > 100 || containsControl(name)) throw new IOException("Invalid name");
        SeaLionClient.endpoint(base);
        if (!SeaLionClient.validModel(model)) throw new IOException("Invalid model");
        if (newKey == null) newKey = "";
        if (!newKey.isEmpty() && !SeaLionClient.validKey(newKey)) throw new IOException("Invalid key");
        synchronized (LOCK) {
            if (ProviderRouter.SEA_LION.equals(provider) && newKey.isEmpty() && !hasKey(context)) {
                throw new IOException("API key required");
            }
            SharedPreferences pref = prefs(context);
            // Fail closed during a credential/endpoint change: a failed write must
            // not send a new key to an old endpoint (or the converse).
            if (ProviderRouter.SEA_LION.equals(pref.getString("provider", ProviderRouter.GOOGLE)) &&
                    !pref.edit().putString("provider", ProviderRouter.ORIGINAL).commit()) {
                throw new IOException("Settings could not be saved");
            }
            if (!newKey.isEmpty()) writeSecret(context, newKey);
            boolean saved = pref.edit().putString("provider", provider).putString("name", name.trim())
                    .putString("base", base.trim()).putString("model", model).commit();
            if (!saved) throw new IOException("Settings could not be saved");
        }
    }

    static void clearKey(Context context) throws IOException {
        synchronized (LOCK) {
            SharedPreferences pref = prefs(context);
            if (ProviderRouter.SEA_LION.equals(pref.getString("provider", ProviderRouter.GOOGLE)) &&
                    !pref.edit().putString("provider", ProviderRouter.ORIGINAL).commit()) throw new IOException("Settings could not be saved");
            try {
                new AtomicFile(new File(context.getNoBackupFilesDir(), SECRET)).delete();
                KeyStore store = KeyStore.getInstance("AndroidKeyStore");
                store.load(null);
                if (store.containsAlias(ALIAS)) store.deleteEntry(ALIAS);
            } catch (Exception error) {
                throw new IOException("Key could not be cleared");
            }
        }
    }

    private static boolean containsControl(String value) {
        for (int i = 0; i < value.length(); i++) if (Character.isISOControl(value.charAt(i))) return true;
        return false;
    }

    private static SecretKey secretKey(boolean create) throws Exception {
        KeyStore store = KeyStore.getInstance("AndroidKeyStore");
        store.load(null);
        if (store.containsAlias(ALIAS)) {
            java.security.Key key = store.getKey(ALIAS, null);
            if (!(key instanceof SecretKey)) throw new IOException("Invalid key entry");
            return (SecretKey) key;
        }
        if (!create) throw new IOException("Missing encryption key");
        KeyGenerator generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
        generator.init(new KeyGenParameterSpec.Builder(ALIAS, KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256).build());
        return generator.generateKey();
    }

    private static void writeSecret(Context context, String value) throws IOException {
        byte[] plaintext = value.getBytes(StandardCharsets.UTF_8);
        AtomicFile target = new AtomicFile(new File(context.getNoBackupFilesDir(), SECRET));
        FileOutputStream output = null;
        try {
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            cipher.init(Cipher.ENCRYPT_MODE, secretKey(true));
            byte[] iv = cipher.getIV();
            if (iv == null || iv.length < 12 || iv.length > 32) throw new IOException("Invalid encryption nonce");
            byte[] encrypted = cipher.doFinal(plaintext);
            output = target.startWrite();
            output.write(1); output.write(iv.length); output.write(iv); output.write(encrypted);
            target.finishWrite(output);
            output = null;
        } catch (Exception error) {
            if (output != null) target.failWrite(output);
            throw new IOException("API key could not be stored securely");
        } finally {
            Arrays.fill(plaintext, (byte) 0);
        }
    }

    private static String readSecret(Context context) throws IOException {
        synchronized (LOCK) {
            AtomicFile file = new AtomicFile(new File(context.getNoBackupFilesDir(), SECRET));
            try (FileInputStream input = file.openRead(); ByteArrayOutputStream data = new ByteArrayOutputStream()) {
                byte[] buffer = new byte[512]; int count;
                while ((count = input.read(buffer)) != -1) {
                    if (data.size() + count > 4096) throw new IOException("Invalid key file");
                    data.write(buffer, 0, count);
                }
                byte[] bytes = data.toByteArray();
                if (bytes.length < 2 || bytes[0] != 1) throw new IOException("Invalid key file");
                int length = bytes[1] & 0xff;
                if (length < 12 || length > 32 || bytes.length < length + 2 + 16) throw new IOException("Invalid key file");
                byte[] iv = Arrays.copyOfRange(bytes, 2, 2 + length);
                Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
                cipher.init(Cipher.DECRYPT_MODE, secretKey(false), new GCMParameterSpec(128, iv));
                byte[] plaintext = cipher.doFinal(bytes, 2 + length, bytes.length - 2 - length);
                try {
                    String result = new String(plaintext, StandardCharsets.UTF_8);
                    if (!SeaLionClient.validKey(result)) throw new IOException("Invalid key");
                    return result;
                } finally {
                    Arrays.fill(plaintext, (byte) 0);
                }
            } catch (Exception error) {
                throw new IOException("API key unavailable; re-enter it in Settings Patch");
            }
        }
    }
}
