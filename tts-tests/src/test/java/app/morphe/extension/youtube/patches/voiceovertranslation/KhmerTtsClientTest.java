package app.morphe.extension.youtube.patches.voiceovertranslation;

import com.sun.net.httpserver.HttpServer;
import org.json.JSONArray;
import org.json.JSONObject;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.Assert.*;

/** Exercises the production client against a local fake of the MST-DUBBERS API. */
public class KhmerTtsClientTest {
    private HttpServer server;
    private URL endpoint;
    private final AtomicInteger requests = new AtomicInteger();
    private volatile String method;
    private volatile String path;
    private volatile String contentType;
    private volatile String requestBody;
    private volatile int responseStatus = 200;
    private volatile String responseType = "audio/mpeg";
    private volatile byte[] responseBytes = audioFixture();

    private static byte[] audioFixture() {
        byte[] bytes = new byte[1024];
        Arrays.fill(bytes, (byte) 42);
        System.arraycopy("ID3".getBytes(StandardCharsets.US_ASCII), 0, bytes, 0, 3);
        return bytes;
    }

    @Before
    public void startServer() throws Exception {
        server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        endpoint = new URL("http://127.0.0.1:" + server.getAddress().getPort() + "/api/process-multi");
        server.createContext("/", exchange -> {
            requests.incrementAndGet();
            method = exchange.getRequestMethod();
            path = exchange.getRequestURI().getPath();
            contentType = exchange.getRequestHeaders().getFirst("Content-Type");
            requestBody = new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
            if (responseType != null) exchange.getResponseHeaders().add("Content-Type", responseType);
            if (responseStatus == 307) exchange.getResponseHeaders().add("Location", "/other");
            exchange.sendResponseHeaders(responseStatus, responseBytes.length == 0 ? -1 : responseBytes.length);
            try (var output = exchange.getResponseBody()) {
                if (responseBytes.length > 0) output.write(responseBytes);
            } finally {
                exchange.close();
            }
        });
        server.start();
    }

    @After
    public void stopServer() {
        if (server != null) server.stop(0);
    }

    private byte[] speak(String text, String voice) throws Exception {
        return KhmerTtsClient.requestAudio(endpoint, text, voice);
    }

    private String field(String name) {
        String marker = "Content-Disposition: form-data; name=\"" + name + "\"\r\n\r\n";
        int start = requestBody.indexOf(marker);
        assertTrue("Missing multipart field " + name, start >= 0);
        start += marker.length();
        return requestBody.substring(start, requestBody.indexOf("\r\n--", start));
    }

    @Test(timeout = 10000)
    public void postsExactMultipartContractAndPreservesKhmerText() throws Exception {
        String text = "សួស្តី \"YouTube\"\nសូមស្វាគមន៍";
        assertArrayEquals(responseBytes, speak(text, KhmerTtsClient.PISETH_VOICE_ID));
        assertEquals("POST", method);
        assertEquals("/api/process-multi", path);
        assertTrue(contentType.startsWith("multipart/form-data; boundary="));
        String boundary = contentType.substring(contentType.indexOf("boundary=") + 9);
        assertTrue(requestBody.startsWith("--" + boundary + "\r\n"));
        assertTrue(requestBody.endsWith("--" + boundary + "--\r\n"));
        JSONArray data = new JSONArray(field("data"));
        assertEquals(1, data.length());
        JSONObject part = data.getJSONObject(0);
        assertEquals(4, part.length());
        assertEquals(text, part.getString("text"));
        assertEquals("piseth", part.getString("voiceName"));
        assertEquals(1.0, part.getDouble("speed"), 0);
        assertEquals(0, part.getInt("pitch"));
        assertEquals("false", field("autoSpeed"));
        assertEquals(1, requests.get()); // No /openapi.json dependency or extra endpoint probes.
    }

    @Test(timeout = 10000)
    public void femaleSelectionUsesSreymom() throws Exception {
        speak("សួស្តី", KhmerTtsClient.SREYMOM_VOICE_ID);
        assertEquals("sreymom", new JSONArray(field("data")).getJSONObject(0).getString("voiceName"));
    }

    @Test
    public void voiceIdsAreStableDistinctAndSupportLegacySelections() {
        assertEquals(KhmerTtsClient.PISETH_VOICE_ID, KhmerTtsClient.resolveVoiceId(null));
        assertEquals(KhmerTtsClient.PISETH_VOICE_ID, KhmerTtsClient.resolveVoiceId(KhmerTtsClient.VOICE_ID));
        assertEquals(KhmerTtsClient.PISETH_VOICE_ID, KhmerTtsClient.resolveVoiceId("km-KH-PisethNeural"));
        assertEquals(KhmerTtsClient.SREYMOM_VOICE_ID, KhmerTtsClient.resolveVoiceId("km-KH-SreymomNeural"));
        assertEquals(KhmerTtsClient.SREYMOM_VOICE_ID, KhmerTtsClient.resolveVoiceId("female"));
        assertNotEquals(KhmerTtsClient.PISETH_VOICE_ID, KhmerTtsClient.SREYMOM_VOICE_ID);
    }

    @Test
    public void onlyKhmerUsesThisClient() {
        assertTrue(KhmerTtsClient.supports("km"));
        assertTrue(KhmerTtsClient.supports("KM-kh"));
        assertFalse(KhmerTtsClient.supports("en-US"));
        assertFalse(KhmerTtsClient.supports(null));
    }

    @Test(timeout = 10000)
    public void blankAndSymbolOnlySegmentsDoNotCallServer() throws Exception {
        assertEquals(0, speak(null, null).length);
        assertEquals(0, speak("  ", null).length);
        assertEquals(0, speak("♪ … !", null).length);
        assertEquals(0, requests.get());
    }

    @Test(timeout = 10000)
    public void reportsFastApiErrorWithoutTryingAnotherEndpoint() throws Exception {
        responseStatus = 400;
        responseType = "application/json";
        responseBytes = "{\"detail\":\"No audio generated\"}".getBytes(StandardCharsets.UTF_8);
        IOException error = assertThrows(IOException.class, () -> speak("សួស្តី", null));
        assertTrue(error.getMessage().contains("HTTP 400: No audio generated"));
        assertEquals(1, requests.get());
    }

    @Test(timeout = 10000)
    public void missingEndpointIsReportedWithoutGuessingUrls() throws Exception {
        responseStatus = 404;
        IOException error = assertThrows(IOException.class, () -> speak("សួស្តី", null));
        assertTrue(error.getMessage().contains("HTTP 404"));
        assertEquals(1, requests.get());
    }

    @Test(timeout = 10000)
    public void doesNotFollowRedirectsOrSendTextElsewhere() throws Exception {
        responseStatus = 307;
        IOException error = assertThrows(IOException.class, () -> speak("សួស្តី", null));
        assertTrue(error.getMessage().contains("HTTP 307"));
        assertEquals(1, requests.get());
    }

    @Test(timeout = 10000)
    public void emptyAudioIsAnError() throws Exception {
        responseBytes = new byte[0];
        IOException error = assertThrows(IOException.class, () -> speak("សួស្តី", null));
        assertTrue(error.getMessage().contains("no audio"));
    }

    @Test(timeout = 10000)
    public void rejectsHtmlEvenWhenMislabeledAsAudio() throws Exception {
        responseBytes = ("<html>server unavailable" + " ".repeat(300)).getBytes(StandardCharsets.UTF_8);
        IOException error = assertThrows(IOException.class, () -> speak("សួស្តី", null));
        assertTrue(error.getMessage().contains("text instead of audio"));
    }

    @Test(timeout = 10000)
    public void acceptsBinaryAudioWithoutContentType() throws Exception {
        responseType = null;
        assertArrayEquals(responseBytes, speak("សួស្តី", null));
    }

    @Test
    public void boundsResponseSize() {
        IOException error = assertThrows(IOException.class,
                () -> KhmerTtsClient.readAll(new ByteArrayInputStream(new byte[100]), 99));
        assertTrue(error.getMessage().contains("size limit"));
    }
}
