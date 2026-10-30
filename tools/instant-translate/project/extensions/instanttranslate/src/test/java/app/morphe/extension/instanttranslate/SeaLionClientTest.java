package app.morphe.extension.instanttranslate;

import org.json.JSONArray;
import org.json.JSONObject;
import org.junit.Test;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.TimeUnit;

import static org.junit.Assert.*;

public class SeaLionClientTest {
    private static final String RESULT = "{\"choices\":[{\"finish_reason\":\"stop\",\"message\":{\"role\":\"assistant\",\"content\":\"សួស្តី\",\"refusal\":null}}]}";
    private static SeaLionClient.Config config() {
        return new SeaLionClient.Config(SeaLionClient.DEFAULT_BASE, SeaLionClient.DEFAULT_MODEL, "test-key-not-real");
    }
    private static SeaLionClient client(FakeConnection connection) {
        return new SeaLionClient(SeaLionClientTest::config, url -> {
            connection.actual = url;
            return connection;
        }, new SeaLionClient.RateGate(System::nanoTime));
    }

    @Test public void sendsOpenAiCompatibleRequestWithoutTextOrKeyInUrl() throws Exception {
        FakeConnection c = new FakeConnection(200, RESULT);
        assertEquals("សួស្តី", client(c).translate("hello & សួស្តី", "en", "km"));
        assertEquals("https://api.sea-lion.ai/v1/chat/completions", c.actual.toExternalForm());
        assertEquals("POST", c.getRequestMethod());
        assertFalse(c.getInstanceFollowRedirects());
        assertEquals("Bearer test-key-not-real", c.getRequestProperty("Authorization"));
        assertEquals(10000, c.getConnectTimeout());
        assertEquals(45000, c.getReadTimeout());
        JSONObject payload = new JSONObject(c.body.toString("UTF-8"));
        assertEquals(SeaLionClient.DEFAULT_MODEL, payload.getString("model"));
        assertFalse(payload.getBoolean("stream"));
        assertEquals(0, payload.getInt("temperature"));
        JSONArray messages = payload.getJSONArray("messages");
        assertEquals("system", messages.getJSONObject(0).getString("role"));
        assertTrue(messages.getJSONObject(0).getString("content").contains("km"));
        assertEquals("hello & សួស្តី", messages.getJSONObject(1).getString("content"));
        assertEquals("user", messages.getJSONObject(1).getString("role"));
        assertTrue(c.disconnected);
    }

    @Test public void rejectsBadConfigBeforeOpeningAndDoesNotLeakCredentials() throws Exception {
        String[] bad = {"", "white space", "bad\r\nHeader: value", "x".repeat(1025)};
        for (String key : bad) {
            SeaLionClient x = new SeaLionClient(() -> new SeaLionClient.Config(SeaLionClient.DEFAULT_BASE,
                    SeaLionClient.DEFAULT_MODEL, key), url -> { throw new AssertionError("must not open"); },
                    new SeaLionClient.RateGate(System::nanoTime));
            assertThrows(Exception.class, () -> x.translate("hello", "en", "km"));
        }
        assertFalse(SeaLionClient.validModel("model with spaces"));
        assertTrue(SeaLionClient.validModel(SeaLionClient.DEFAULT_MODEL));
        assertThrows(Exception.class, () -> client(new FakeConnection(200, RESULT)).translate("", "en", "km"));
        assertThrows(Exception.class, () -> client(new FakeConnection(200, RESULT)).translate("hello", "en", "bad&value"));
        FakeConnection failed = new FakeConnection(401, "test-key-not-real and hello");
        Exception error = assertThrows(Exception.class, () -> client(failed).translate("hello", "en", "km"));
        assertFalse(error.toString().contains("hello"));
        assertFalse(error.toString().contains("test-key-not-real"));
        assertTrue(failed.disconnected);
    }

    @Test public void rejectsRedirectsProviderErrorsAndTruncatedOrUnsafeResponses() throws Exception {
        for (int code : new int[]{301, 302, 401, 429, 500}) {
            FakeConnection c = new FakeConnection(code, RESULT);
            assertThrows(Exception.class, () -> client(c).translate("hola", "es", "en"));
            assertFalse(c.getInstanceFollowRedirects());
            assertTrue(c.disconnected);
        }
        assertThrows(Exception.class, () -> SeaLionClient.parse("not-json"));
        assertThrows(Exception.class, () -> SeaLionClient.parse("{\"choices\":[]}"));
        assertThrows(Exception.class, () -> SeaLionClient.parse("{\"choices\":[{\"finish_reason\":\"length\",\"message\":{\"content\":\"partial\"}}]}"));
        assertThrows(Exception.class, () -> SeaLionClient.parse("{\"choices\":[{\"finish_reason\":\"stop\",\"message\":{\"content\":\"answer\",\"refusal\":\"no\"}}]}"));
        assertThrows(Exception.class, () -> SeaLionClient.parse("{\"choices\":[{\"finish_reason\":\"stop\",\"message\":{\"content\":\"  \"}}]}"));
        FakeConnection c = new FakeConnection(200, "x".repeat(1024 * 1024 + 1));
        assertThrows(Exception.class, () -> client(c).translate("hola", "es", "en"));
    }

    @Test public void allowsOnlyHttpsBaseUrlWithoutCredentialsOrLocalAddress() throws Exception {
        assertEquals("https://api.sea-lion.ai/v1/chat/completions", SeaLionClient.endpoint("https://api.sea-lion.ai/v1/").toString());
        assertEquals("https://example.com/v1/chat/completions", SeaLionClient.endpoint("https://example.com/v1").toString());
        for (String value : new String[]{"http://api.sea-lion.ai/v1", "https://api.sea-lion.ai/v1?key=secret",
                "https://name:password@api.sea-lion.ai/v1", "https://127.0.0.1/v1", "https://localhost/v1",
                "https://x.local/v1", "https://example.com/v1/../private", "https://example.com/%2e%2e"}) {
            assertThrows(Exception.class, () -> SeaLionClient.endpoint(value));
        }
    }

    @Test public void localRateGuardRejectsWithoutRetryAndRecoversAfterOneMinute() {
        final long[] now = {1};
        SeaLionClient.RateGate gate = new SeaLionClient.RateGate(() -> now[0]);
        for (int i = 0; i < 9; i++) assertTrue(gate.acquire());
        assertFalse(gate.acquire());
        now[0] += TimeUnit.MINUTES.toNanos(1);
        assertTrue(gate.acquire());
    }

    private static final class FakeConnection extends HttpURLConnection {
        final int code;
        final byte[] response;
        final ByteArrayOutputStream body = new ByteArrayOutputStream();
        boolean disconnected;
        URL actual;
        final java.util.Map<String, String> headers = new java.util.HashMap<>();
        FakeConnection(int code, String response) throws Exception {
            super(new URL("https://api.sea-lion.ai/v1/chat/completions"));
            this.code = code;
            this.response = response.getBytes(StandardCharsets.UTF_8);
        }
        @Override public int getResponseCode() { return code; }
        @Override public void setRequestProperty(String key, String value) { headers.put(key, value); }
        @Override public String getRequestProperty(String key) { return headers.get(key); }
        @Override public OutputStream getOutputStream() { return body; }
        @Override public InputStream getInputStream() { return new ByteArrayInputStream(response); }
        @Override public void disconnect() { disconnected = true; }
        @Override public boolean usingProxy() { return false; }
        @Override public void connect() {}
    }
}
