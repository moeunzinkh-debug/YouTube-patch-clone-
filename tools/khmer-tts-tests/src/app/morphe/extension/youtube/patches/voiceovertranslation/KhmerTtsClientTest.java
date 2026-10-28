package app.morphe.extension.youtube.patches.voiceovertranslation;

import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import org.json.*;

public final class KhmerTtsClientTest {
    static int checks;
    static Fake connection;
    static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
        checks++;
    }
    static final class Fake extends HttpURLConnection {
        final ByteArrayOutputStream sent = new ByteArrayOutputStream();
        byte[] response = new byte[]{'I', 'D', '3', 0};
        int status = 200;
        boolean closed;
        Fake(URL url) { super(url); }
        public void connect() { }
        public boolean usingProxy() { return false; }
        public void disconnect() { closed = true; }
        public OutputStream getOutputStream() { return sent; }
        public int getResponseCode() { return status; }
        public String getContentType() { return "audio/mpeg"; }
        public InputStream getInputStream() { return new ByteArrayInputStream(response); }
        public InputStream getErrorStream() { return new ByteArrayInputStream(response); }
    }
    public static void main(String[] args) throws Exception {
        if (args.length == 2 && "--live".equals(args[0])) {
            byte[] audio = KhmerTtsClient.synthesize("សួស្តី នេះជាការសាកល្បងសំឡេង។");
            Files.write(Path.of(args[1]), audio);
            System.out.println("Actual Java client returned " + audio.length + " bytes");
            return;
        }
        for (String text : new String[]{"សួស្តី", "quotes \" & + = \\ newline\r\n emoji 🎤", "</data>\r\n--boundary"}) {
            byte[] body = KhmerTtsClient.buildRequestBody(text);
            String form = new String(body, StandardCharsets.UTF_8);
            String boundary = form.substring(2, form.indexOf("\r\n"));
            String marker = "name=\"data\"\r\n\r\n";
            int start = form.indexOf(marker) + marker.length();
            JSONArray parts = new JSONArray(form.substring(start, form.indexOf("\r\n--" + boundary, start)));
            JSONObject part = parts.getJSONObject(0);
            check(parts.length() == 1, "single standalone clip");
            check(part.getString("text").equals(text), "UTF-8 and JSON escaping roundtrip");
            check(part.getString("voiceName").equals("piseth"), "server voice name");
            check(part.getDouble("speed") == 1.0 && part.getInt("pitch") == 0, "natural speed and pitch");
            check(!part.has("start") && !part.has("endMs"), "no video-relative silence padding");
            check(form.contains("name=\"autoSpeed\"\r\n\r\nfalse\r\n"), "no server auto time stretch");
            check(form.endsWith("--" + boundary + "--\r\n"), "closed multipart framing");
        }
        URL.setURLStreamHandlerFactory(protocol -> !protocol.equals("https") ? null : new URLStreamHandler() {
            protected URLConnection openConnection(URL url) {
                if (connection == null) connection = new Fake(url);
                return connection;
            }
        });
        check(KhmerTtsClient.synthesize(" ").length == 0 && connection == null, "blank input makes no request");
        check(KhmerTtsClient.synthesize(null).length == 0, "null input makes no request");
        check(KhmerTtsClient.synthesize("សួស្តី").length == 4, "audio returned");
        check(connection.getURL().toString().equals(KhmerTtsClient.SYNTHESIS_URL), "direct process-multi URL, no discovery");
        check(connection.getRequestMethod().equals("POST"), "POST method");
        check(connection.getRequestProperty("Content-Type").startsWith("multipart/form-data; boundary="), "multipart header");
        check(!connection.getInstanceFollowRedirects(), "no automatic redirects");
        check(connection.closed, "success disconnects");
        connection = new Fake(new URL(KhmerTtsClient.SYNTHESIS_URL));
        connection.status = 400;
        connection.response = "{\"detail\":\"No data provided\"}".getBytes(StandardCharsets.UTF_8);
        try {
            KhmerTtsClient.synthesize("test");
            throw new AssertionError("HTTP error must fail");
        } catch (IOException e) {
            check(e.getMessage().contains("HTTP 400"), "HTTP errors reported");
            check(connection.closed, "error disconnects");
        }
        connection = new Fake(new URL(KhmerTtsClient.SYNTHESIS_URL));
        connection.response = new byte[0];
        try {
            KhmerTtsClient.synthesize("test");
            throw new AssertionError("empty audio must fail");
        } catch (IOException e) {
            check(e.getMessage().contains("no audio"), "empty response rejected");
        }
        System.out.println(checks + " Khmer TTS client checks passed");
    }
}
