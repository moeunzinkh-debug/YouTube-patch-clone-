package app.morphe.extension.king;

import android.os.Build;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;

import java.io.File;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.math.BigInteger;
import java.security.KeyPairGenerator;
import java.security.KeyStore;
import java.security.PrivateKey;
import java.security.cert.Certificate;
import java.security.cert.X509Certificate;
import java.util.Collections;
import java.util.Date;
import java.util.List;
import javax.security.auth.x500.X500Principal;

/** Signs with a private, non-exportable per-install Android Keystore key. */
final class ApkSignerBridge {
    private static final String ALIAS = "morphe_king_output_signing_v1";
    private ApkSignerBridge() {}

    private static synchronized KeyStore keyStore() throws Exception {
        if (Build.VERSION.SDK_INT < 23) throw new IOException("Android 6 or newer is required for the local signing key");
        KeyStore store = KeyStore.getInstance("AndroidKeyStore"); store.load(null);
        if (!store.containsAlias(ALIAS)) {
            KeyPairGenerator generator = KeyPairGenerator.getInstance(KeyProperties.KEY_ALGORITHM_RSA, "AndroidKeyStore");
            KeyGenParameterSpec spec = new KeyGenParameterSpec.Builder(ALIAS,
                    KeyProperties.PURPOSE_SIGN | KeyProperties.PURPOSE_VERIFY)
                    .setKeySize(2048)
                    .setDigests(KeyProperties.DIGEST_SHA256, KeyProperties.DIGEST_SHA512)
                    .setSignaturePaddings(KeyProperties.SIGNATURE_PADDING_RSA_PKCS1, KeyProperties.SIGNATURE_PADDING_RSA_PSS)
                    .setCertificateSubject(new X500Principal("CN=Morphe King local output"))
                    .setCertificateSerialNumber(BigInteger.ONE)
                    .setCertificateNotBefore(new Date(1577836800000L))
                    .setCertificateNotAfter(new Date(4102444800000L))
                    .build();
            generator.initialize(spec); generator.generateKeyPair();
        }
        return store;
    }
    private static Object call(Object target, String method, Class<?>[] types, Object... args) throws Exception {
        return target.getClass().getMethod(method, types).invoke(target, args);
    }
    private static IOException failure(Throwable error) {
        while (error instanceof InvocationTargetException && ((InvocationTargetException) error).getCause() != null)
            error = ((InvocationTargetException) error).getCause();
        return new IOException("Unable to sign and independently verify the output APK", error);
    }
    static void signAndVerify(File input, File output) throws IOException {
        if (input == null || !input.isFile() || output == null || output.exists()
                || input.getCanonicalFile().equals(output.getCanonicalFile()))
            throw new IOException("Signing requires a new output file");
        boolean success = false;
        try {
            KeyStore store = keyStore();
            PrivateKey key = (PrivateKey) store.getKey(ALIAS, null);
            Certificate certificate = store.getCertificate(ALIAS);
            if (key == null || !(certificate instanceof X509Certificate)) throw new IOException("Local signing key unavailable");
            // The inspected APK supplies apksig. Reflection avoids packaging a second copy.
            Class<?> signerConfigBuilder = Class.forName("com.android.apksig.ApkSigner$SignerConfig$Builder");
            Object configBuilder = signerConfigBuilder.getConstructor(String.class, PrivateKey.class, List.class)
                    .newInstance("MORPHE", key, Collections.singletonList(certificate));
            Object config = call(configBuilder, "build", new Class<?>[0]);
            Class<?> signerBuilderClass = Class.forName("com.android.apksig.ApkSigner$Builder");
            Object signerBuilder = signerBuilderClass.getConstructor(List.class).newInstance(Collections.singletonList(config));
            call(signerBuilder, "setInputApk", new Class<?>[]{File.class}, input);
            call(signerBuilder, "setOutputApk", new Class<?>[]{File.class}, output);
            call(signerBuilder, "setMinSdkVersion", new Class<?>[]{int.class}, 23);
            call(signerBuilder, "setV1SigningEnabled", new Class<?>[]{boolean.class}, true);
            call(signerBuilder, "setV2SigningEnabled", new Class<?>[]{boolean.class}, true);
            call(signerBuilder, "setV3SigningEnabled", new Class<?>[]{boolean.class}, false);
            call(signerBuilder, "setOtherSignersSignaturesPreserved", new Class<?>[]{boolean.class}, false);
            Object signer = call(signerBuilder, "build", new Class<?>[0]);
            call(signer, "sign", new Class<?>[0]);
            if (!output.isFile() || output.length() <= 0) throw new IOException("Signing produced no APK");

            Class<?> verifierBuilderClass = Class.forName("com.android.apksig.ApkVerifier$Builder");
            Object verifierBuilder = verifierBuilderClass.getConstructor(File.class).newInstance(output);
            call(verifierBuilder, "setMinCheckedPlatformVersion", new Class<?>[]{int.class}, 23);
            Object verifier = call(verifierBuilder, "build", new Class<?>[0]);
            Object result = call(verifier, "verify", new Class<?>[0]);
            if (!Boolean.TRUE.equals(call(result, "isVerified", new Class<?>[0]))) throw new IOException("APK signature verification failed");
            Object certificates = call(result, "getSignerCertificates", new Class<?>[0]);
            if (!(certificates instanceof List) || ((List<?>) certificates).size() != 1
                    || !certificate.equals(((List<?>) certificates).get(0)))
                throw new IOException("APK signer does not match the local key");
            success = true;
        } catch (Exception error) {
            if (error instanceof IOException) throw (IOException) error;
            throw failure(error);
        } finally {
            if (!success && output.exists()) output.delete();
        }
    }
}
