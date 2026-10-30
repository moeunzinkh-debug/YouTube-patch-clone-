package app.morphe.extension.instanttranslate;

import org.junit.Test;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;

import static org.junit.Assert.*;

public class GtxClientTest {
    @Test public void postsUnicodeTextInBodyAndPreservesLanguageSelection() throws Exception {
        FakeConnection connection = new FakeConnection(200, "[[[\"សួស្តី\",\"hello\"]],null,\"en\"]");
        GtxClient client = new GtxClient(url -> { connection.actualUrl = url; return connection; });
        String result = client.translate("hello & សួស្តី + ?", "en", "km");
        assertEquals("សួស្តី", result);
        assertEquals("translate.googleapis.com", connection.actualUrl.getHost());
        assertEquals("https", connection.actualUrl.getProtocol());
        assertEquals("/translate_a/single", connection.actualUrl.getPath());
        assertEquals("client=gtx&sl=en&tl=km&dt=t", connection.actualUrl.getQuery());
        assertEquals("hello & សួស្តី + ?", URLDecoder.decode(connection.body.toString("UTF-8").substring(2), "UTF-8"));
        assertFalse(connection.getInstanceFollowRedirects());
        assertEquals("POST", connection.getRequestMethod());
        assertEquals(6000, connection.getConnectTimeout());
        assertEquals(10000, connection.getReadTimeout());
        assertTrue(connection.disconnected);
    }

    @Test public void joinsSegmentsAndHandlesEscapesAndAutoSource() throws Exception {
        FakeConnection connection = new FakeConnection(200, "[[[\"first \\\"\",\"x\"],[\"line\\nsecond\",\"y\"],[null]],null,\"km\"]");
        String result = new GtxClient(url -> { connection.actualUrl = url; return connection; })
                .translate("ខ្មែរ", "", "en");
        assertEquals("first \"line\nsecond", result);
        assertTrue(connection.actualUrl.getQuery().contains("sl=auto"));
        assertTrue(connection.actualUrl.getQuery().contains("tl=en"));
    }

    @Test public void rejectsRedirectRateLimitMalformedAndOversize() throws Exception {
        for (int status : new int[]{301, 302, 429, 500}) {
            FakeConnection c = new FakeConnection(status, "not used");
            Exception error = assertThrows(Exception.class, () -> new GtxClient(url -> c).translate("secret", "en", "km"));
            assertFalse(error.toString().contains("secret"));
            assertTrue(c.disconnected);
            assertFalse(c.getInstanceFollowRedirects());
        }
        assertThrows(Exception.class, () -> GtxClient.parse("not json"));
        assertThrows(Exception.class, () -> GtxClient.parse("[[],null,\"en\"]"));
        assertThrows(Exception.class, () -> GtxClient.parse("[[[42]],null,\"en\"]"));
        String oversized = "x".repeat(1024 * 1024 + 1);
        FakeConnection c = new FakeConnection(200, oversized);
        assertThrows(Exception.class, () -> new GtxClient(url -> c).translate("hello", "en", "km"));
        assertTrue(c.disconnected);
    }

    @Test public void rejectsInvalidInputsBeforeOpeningConnection() throws Exception {
        GtxClient client = new GtxClient(url -> { throw new AssertionError("must not open"); });
        assertThrows(Exception.class, () -> client.translate("", "en", "km"));
        assertThrows(Exception.class, () -> client.translate("a".repeat(8193), "en", "km"));
        assertThrows(Exception.class, () -> client.translate("hello", "en&bad=1", "km"));
        assertThrows(Exception.class, () -> client.translate("hello", "en", null));
    }

    private static final class FakeConnection extends HttpURLConnection {
        final int status;
        final byte[] response;
        final ByteArrayOutputStream body = new ByteArrayOutputStream();
        boolean disconnected;
        URL actualUrl;
        FakeConnection(int status, String response) throws Exception {
            super(new URL(GtxClient.ENDPOINT));
            this.status = status;
            this.response = response.getBytes(StandardCharsets.UTF_8);
        }
        @Override public int getResponseCode() { return status; }
        @Override public OutputStream getOutputStream() { return body; }
        @Override public InputStream getInputStream() { return new ByteArrayInputStream(response); }
        @Override public void disconnect() { disconnected = true; }
        @Override public boolean usingProxy() { return false; }
        @Override public void connect() {}
    }
}
