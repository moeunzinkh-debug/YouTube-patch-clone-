/*
 * Copyright 2026 Morphe.
 * https://github.com/MorpheApp/morphe-patches
 *
 * See the included NOTICE file for GPLv3 Section 7 terms that apply to this code.
 */

package app.morphe.extension.youtube.patches.voiceovertranslation;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Locale;

/**
 * Direct integration with the same Takumi API used by MST-DUBBERS EdgeTtsClient.
 * No OpenAPI discovery, guessed endpoints, or fallback to another voice service.
 * Must be called from a background thread (enforced by TTSEngine.prefetch).
 */
final class KhmerTtsClient {
    // Keep the legacy ID readable, but use distinct IDs for new voice/cache entries.
    static final String VOICE_ID = "takumi-khmer-server";
    static final String PISETH_VOICE_ID = "takumi-khmer-piseth-v1";
    static final String SREYMOM_VOICE_ID = "takumi-khmer-sreymom-v1";
    private static final String ENDPOINT_URL = "https://takumi0002-tts-kh.hf.space/api/process-multi";
    private static final String BOUNDARY = "----YouTubePatchKhmerTtsBoundary7MA4YWxkTrZu0gW";
    private static final int MAX_AUDIO_BYTES = 32 * 1024 * 1024;
    private static final int MIN_AUDIO_BYTES = 200;

    private KhmerTtsClient() {}

    static boolean supports(String languageTag) {
        return languageTag != null && (languageTag.equalsIgnoreCase("km")
                || languageTag.regionMatches(true, 0, "km-", 0, 3));
    }

    /** Preserve old Edge Khmer voice selections and the original single-server voice ID. */
    static String resolveVoiceId(String preferredVoice) {
        return "sreymom".equals(serverVoice(preferredVoice)) ? SREYMOM_VOICE_ID : PISETH_VOICE_ID;
    }

    private static String serverVoice(String voice) {
        String normalized = voice == null ? "" : voice.toLowerCase(Locale.ROOT);
        // Test 'female' before 'male': female contains male.
        return normalized.contains("sreymom") || normalized.contains("female") ? "sreymom" : "piseth";
    }

    static byte[] synthesize(String text, String voice) throws Exception {
        return requestAudio(new URL(ENDPOINT_URL), text, voice);
    }

    /** Package-private for contract tests against a local HTTP server, never a live service. */
    static byte[] requestAudio(URL endpoint, String text, String voice) throws Exception {
        if (text == null || text.trim().isEmpty()) return new byte[0];
        String cleanText = text.trim();
        // Avoid sending punctuation-only caption segments to the speech backend.
        if (!cleanText.codePoints().anyMatch(Character::isLetterOrDigit)) return new byte[0];

        byte[] body = buildBody(cleanText, voice);
        HttpURLConnection connection = (HttpURLConnection) endpoint.openConnection();
        try {
            connection.setConnectTimeout(45_000);
            // Allow a sleeping Hugging Face Space time to wake up.
            connection.setReadTimeout(120_000);
            connection.setRequestMethod("POST");
            // Do not silently turn a redirected POST into a GET or send text to another host.
            connection.setInstanceFollowRedirects(false);
            connection.setDoOutput(true);
            connection.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + BOUNDARY);
            connection.setRequestProperty("Accept", "audio/*, application/octet-stream");
            connection.setRequestProperty("User-Agent", "YouTube-Patch-Clone/1.0");
            connection.setFixedLengthStreamingMode(body.length);
            try (OutputStream output = connection.getOutputStream()) {
                output.write(body);
            }

            int status = connection.getResponseCode();
            InputStream stream = status >= 400 ? connection.getErrorStream() : connection.getInputStream();
            byte[] response = stream == null ? new byte[0] : readAll(stream, MAX_AUDIO_BYTES);
            if (status < 200 || status >= 300) {
                throw new IOException("Khmer TTS server returned HTTP " + status + ": " + errorDetail(response));
            }
            validateAudio(response, connection.getContentType());
            return response;
        } finally {
            connection.disconnect();
        }
    }

    static byte[] buildBody(String text, String voice) throws Exception {
        JSONObject part = new JSONObject();
        part.put("text", text);
        part.put("voiceName", serverVoice(voice));
        // Synthesize at natural speed; MediaPlayer applies the independent user controls.
        part.put("speed", 1.0);
        part.put("pitch", 0);
        String data = new JSONArray().put(part).toString();
        String form = "--" + BOUNDARY + "\r\n"
                + "Content-Disposition: form-data; name=\"data\"\r\n\r\n"
                + data + "\r\n"
                + "--" + BOUNDARY + "\r\n"
                + "Content-Disposition: form-data; name=\"autoSpeed\"\r\n\r\n"
                + "false\r\n"
                + "--" + BOUNDARY + "--\r\n";
        return form.getBytes(StandardCharsets.UTF_8);
    }

    static void validateAudio(byte[] bytes, String contentType) throws IOException {
        if (bytes.length <= MIN_AUDIO_BYTES) {
            throw new IOException("Khmer TTS server returned no audio (" + bytes.length + " bytes)");
        }
        String head = new String(bytes, 0, Math.min(bytes.length, 128), StandardCharsets.UTF_8).trim();
        String type = contentType == null ? "" : contentType.toLowerCase(Locale.ROOT);
        if (head.startsWith("<") || head.startsWith("{") || head.startsWith("[")
                || type.contains("json") || type.contains("text/")) {
            throw new IOException("Khmer TTS server returned text instead of audio: " + errorDetail(bytes));
        }
    }

    private static String errorDetail(byte[] bytes) {
        String text = new String(bytes, 0, Math.min(bytes.length, 2048), StandardCharsets.UTF_8).trim();
        try {
            Object detail = new JSONObject(text).opt("detail");
            if (detail != null && detail != JSONObject.NULL) text = detail.toString();
        } catch (Exception ignored) {
            // A proxy may return plain text or HTML rather than FastAPI JSON.
        }
        text = text.replaceAll("\\s+", " ");
        return text.substring(0, Math.min(text.length(), 300));
    }

    static byte[] readAll(InputStream stream, int maxBytes) throws IOException {
        try (InputStream input = stream; ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192];
            int count;
            while ((count = input.read(buffer)) != -1) {
                if (output.size() + count > maxBytes) throw new IOException("TTS response exceeds size limit");
                output.write(buffer, 0, count);
            }
            return output.toByteArray();
        }
    }
}
