package app.morphe.extension.youtube.patches.voiceovertranslation;

import com.sun.net.httpserver.HttpServer;

import org.json.JSONObject;
import org.junit.Test;

import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.Assert.*;

/** Local JVM tests: no live TTS service or Android device required. */
public class KhmerTtsClientTest {
    private static Object invoke(Class<?> type, Object instance, String name,
                                 Class<?>[] parameters, Object... arguments) throws Exception {
        Method method = type.getDeclaredMethod(name, parameters);
        method.setAccessible(true);
        try {
            return method.invoke(instance, arguments);
        } catch (InvocationTargetException ex) {
            if (ex.getCause() instanceof Exception) throw (Exception) ex.getCause();
            throw ex;
        }
    }

    private static byte[] extract(byte[] bytes, String type) throws Exception {
        return (byte[]) invoke(KhmerTtsClient.class, null, "extractAudio",
                new Class<?>[]{byte[].class, String.class, int.class}, bytes, type, 0);
    }

    @Test
    public void emptyAudioIsAnError() throws Exception {
        try {
            extract(new byte[0], "audio/wav");
            fail("Empty audio must fail rather than leave synthesis pending");
        } catch (IOException ex) {
            assertTrue(ex.getMessage().contains("no audio"));
        }
    }

    @Test
    public void binaryAudioIsReturnedUnchanged() throws Exception {
        byte[] audio = "RIFF-test-fixture".getBytes(StandardCharsets.UTF_8);
        assertArrayEquals(audio, extract(audio, "audio/wav"));
    }

    @Test
    public void selfReferencingAudioUrlIsBounded() throws Exception {
        AtomicInteger requests = new AtomicInteger();
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        String url = "http://127.0.0.1:" + server.getAddress().getPort() + "/audio";
        byte[] body = url.getBytes(StandardCharsets.UTF_8);
        server.createContext("/audio", exchange -> {
            requests.incrementAndGet();
            exchange.getResponseHeaders().add("Content-Type", "text/plain");
            exchange.sendResponseHeaders(200, body.length);
            try (var output = exchange.getResponseBody()) {
                output.write(body);
            } finally {
                exchange.close();
            }
        });
        server.start();
        try {
            extract(body, "text/plain");
            fail("Repeated audio URL must not recurse indefinitely");
        } catch (IOException ex) {
            assertTrue(ex.getMessage().contains("nested"));
            assertEquals(4, requests.get());
        } finally {
            server.stop(0);
        }
    }

    @Test
    public void discoversFastApiSchemaAndEncodesKhmerText() throws Exception {
        JSONObject schema = new JSONObject("{\"paths\":{\"/tts\":{\"post\":{"
                + "\"requestBody\":{\"content\":{\"application/json\":{\"schema\":{"
                + "\"$ref\":\"#/components/schemas/Request\"}}}},"
                + "\"responses\":{\"200\":{\"content\":{\"audio/wav\":{}}}}}}},"
                + "\"components\":{\"schemas\":{\"Request\":{\"type\":\"object\","
                + "\"required\":[\"text\"],\"properties\":{\"text\":{\"type\":\"string\"}}}}}}");
        Object endpoint = invoke(KhmerTtsClient.class, null, "discoverEndpoint",
                new Class<?>[]{JSONObject.class}, schema);
        assertNotNull(endpoint);
        byte[] body = (byte[]) invoke(endpoint.getClass(), endpoint, "buildBody",
                new Class<?>[]{String.class}, "សួស្តី");
        assertEquals("សួស្តី", new JSONObject(new String(body, StandardCharsets.UTF_8)).getString("text"));
    }
}
