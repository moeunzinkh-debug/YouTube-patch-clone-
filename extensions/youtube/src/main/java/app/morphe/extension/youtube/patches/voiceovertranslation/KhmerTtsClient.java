/*
 * Copyright 2026 Morphe.
 * https://github.com/MorpheApp/morphe-patches
 *
 * See the included NOTICE file for GPLv3 Section 7 terms that apply to this code.
 */

package app.morphe.extension.youtube.patches.voiceovertranslation;

import android.util.Base64;

import org.json.JSONArray;
import org.json.JSONObject;
import org.json.JSONTokener;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Locale;

import app.morphe.extension.shared.Utils;

/** Direct client for FastAPI's process-multi multipart contract (see server script.js). */
final class KhmerTtsClient {

    static final String VOICE_ID = "takumi-khmer-server";

    private static final String BASE_URL = "https://takumi0002-tts-kh.hf.space";
    static final String SYNTHESIS_URL = BASE_URL + "/api/process-multi";
    private static final int CONNECT_TIMEOUT_MS = 15_000;
    // Hugging Face Spaces may need time to wake from sleep before synthesizing audio.
    private static final int READ_TIMEOUT_MS = 120_000;
    private static final int MAX_AUDIO_BYTES = 32 * 1024 * 1024;
    private static final String MULTIPART_BOUNDARY = "----YouTubePatchKhmerTtsBoundary7MA4YWxkTrZu0gW";

    private KhmerTtsClient() {}

    static boolean supports(String languageTag) {
        return "km".equalsIgnoreCase(VoiceCatalog.getIso639(languageTag));
    }

    /** Synthesizes one natural-speed clip. The player applies its own rate/pitch and timings. */
    static byte[] synthesize(String text) throws Exception {
        Utils.verifyOffMainThread();
        if (text == null || text.trim().isEmpty()) return new byte[0];

        HttpURLConnection connection = null;
        try {
            URL requestUrl = new URL(SYNTHESIS_URL);
            connection = (HttpURLConnection) requestUrl.openConnection();
            connection.setConnectTimeout(CONNECT_TIMEOUT_MS);
            connection.setReadTimeout(READ_TIMEOUT_MS);
            connection.setRequestMethod("POST");
            connection.setInstanceFollowRedirects(false);
            connection.setRequestProperty("Accept", "audio/*, application/octet-stream, application/json");
            connection.setRequestProperty("User-Agent", "YouTube-Patch-Clone/1.0");

            byte[] requestBody = buildRequestBody(text);
            connection.setDoOutput(true);
            connection.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + MULTIPART_BOUNDARY);
            connection.setFixedLengthStreamingMode(requestBody.length);
            try (OutputStream output = connection.getOutputStream()) {
                output.write(requestBody);
            }

            int status = connection.getResponseCode();
            InputStream responseStream = status >= 400
                    ? connection.getErrorStream()
                    : connection.getInputStream();
            byte[] response = responseStream == null ? new byte[0] : readAll(responseStream, MAX_AUDIO_BYTES);
            if (status < 200 || status >= 300) {
                String detail = new String(response, StandardCharsets.UTF_8);
                if (detail.length() > 700) detail = detail.substring(0, 700);
                throw new IOException("Khmer TTS server returned HTTP " + status + ": " + detail);
            }

            String contentType = connection.getContentType();
            if (response.length == 0) throw new IOException("Khmer TTS server returned no audio");
            if (isAudioContentType(contentType)) return response;
            return extractAudio(response, contentType, 0);
        } finally {
            if (connection != null) connection.disconnect();
        }
    }

    /** Same fields as the deployed frontend: FormData(data=JSON parts, autoSpeed=false).
     * Do not send video-relative start/end: this endpoint must return a standalone clip,
     * otherwise the server may prepend silence that the player would schedule a second time.
     */
    static byte[] buildRequestBody(String text) throws Exception {
        JSONObject part = new JSONObject()
                .put("text", text)
                .put("voiceName", "piseth")
                .put("speed", 1.0)
                .put("pitch", 0);
        String data = new JSONArray().put(part).toString();
        String form = "--" + MULTIPART_BOUNDARY
                + "\r\nContent-Disposition: form-data; name=\"data\"\r\n\r\n"
                + data + "\r\n--" + MULTIPART_BOUNDARY
                + "\r\nContent-Disposition: form-data; name=\"autoSpeed\"\r\n\r\n"
                + "false\r\n--" + MULTIPART_BOUNDARY + "--\r\n";
        return form.getBytes(StandardCharsets.UTF_8);
    }

    private static boolean isAudioContentType(String contentType) {
        if (contentType == null) return false;
        String type = contentType.toLowerCase(Locale.ROOT);
        return type.startsWith("audio/") || type.contains("octet-stream") || type.contains("application/binary");
    }

    private static byte[] extractAudio(byte[] response, String contentType, int depth) throws Exception {
        if (response == null || response.length == 0) throw new IOException("Khmer TTS server returned no audio");
        if (isAudioContentType(contentType)) return response;
        if (depth > 4) throw new IOException("Could not extract audio from the TTS response");

        String text = new String(response, StandardCharsets.UTF_8).trim();
        if (text.isEmpty()) throw new IOException("Khmer TTS server returned an empty response");
        if (text.startsWith("data:audio/") && text.contains(";base64,")) {
            return decodeBase64(text.substring(text.indexOf(",") + 1));
        }

        if (contentType != null && contentType.toLowerCase(Locale.ROOT).contains("json")
                || text.startsWith("{") || text.startsWith("[")) {
            Object json = new JSONTokener(text).nextValue();
            byte[] audio = extractFromJson(json, depth + 1);
            if (audio != null) return audio;
        }

        if (text.startsWith("https://") || text.startsWith("http://") || text.startsWith("/")) {
            return downloadAudio(resolveAudioUrl(text));
        }
        throw new IOException("The TTS endpoint response was not audio or a recognized audio URL/base64 field");
    }

    private static byte[] extractFromJson(Object value, int depth) throws Exception {
        if (depth > 4 || value == null || value == JSONObject.NULL) return null;
        if (value instanceof JSONObject object) {
            String[] keys = {"audio", "audio_base64", "audio_url", "url", "file", "file_url",
                    "audio_path", "path", "data", "output", "result", "base64"};
            for (String key : keys) {
                Object item = object.opt(key);
                if (item == null || item == JSONObject.NULL) continue;
                if (item instanceof String string) {
                    if (key.toLowerCase(Locale.ROOT).contains("base64")) return decodeBase64(string);
                    byte[] audio = extractAudioValue(string, depth + 1);
                    if (audio != null) return audio;
                } else {
                    byte[] audio = extractFromJson(item, depth + 1);
                    if (audio != null) return audio;
                }
            }
            return null;
        }
        if (value instanceof JSONArray array) {
            for (int i = 0; i < array.length(); i++) {
                byte[] audio = extractFromJson(array.opt(i), depth + 1);
                if (audio != null) return audio;
            }
        }
        if (value instanceof String string) return extractAudioValue(string, depth + 1);
        return null;
    }

    private static byte[] extractAudioValue(String value, int depth) throws Exception {
        String text = value.trim();
        if (text.startsWith("data:audio/") && text.contains(";base64,")) {
            return decodeBase64(text.substring(text.indexOf(",") + 1));
        }
        if (text.startsWith("https://") || text.startsWith("http://") || text.startsWith("/")) {
            return downloadAudio(resolveAudioUrl(text));
        }
        if (text.length() > 128 && text.matches("[A-Za-z0-9+/=_-]+")) {
            try {
                return decodeBase64(text);
            } catch (Exception ignored) {
                // It was a regular string field rather than audio data.
            }
        }
        return null;
    }

    private static byte[] decodeBase64(String data) throws IOException {
        String encoded = data.replaceAll("\\s", "");
        try {
            return Base64.decode(encoded, Base64.DEFAULT);
        } catch (IllegalArgumentException ex) {
            throw new IOException("The TTS server returned invalid base64 audio", ex);
        }
    }

    private static String resolveAudioUrl(String value) throws Exception {
        if (value.startsWith("https://") || value.startsWith("http://")) return value;
        return new URL(new URL(BASE_URL + "/"), value.startsWith("/") ? value.substring(1) : value).toString();
    }

    private static byte[] downloadAudio(String url) throws Exception {
        HttpURLConnection connection = null;
        try {
            connection = (HttpURLConnection) new URL(url).openConnection();
            connection.setConnectTimeout(CONNECT_TIMEOUT_MS);
            connection.setReadTimeout(READ_TIMEOUT_MS);
            connection.setRequestMethod("GET");
            connection.setRequestProperty("Accept", "audio/*, application/octet-stream, application/json");
            int status = connection.getResponseCode();
            InputStream stream = status >= 400 ? connection.getErrorStream() : connection.getInputStream();
            byte[] bytes = stream == null ? new byte[0] : readAll(stream, MAX_AUDIO_BYTES);
            if (status < 200 || status >= 300) throw new IOException("Audio download returned HTTP " + status);
            String contentType = connection.getContentType();
            if (isAudioContentType(contentType)) return bytes;
            return extractAudio(bytes, contentType, 1);
        } finally {
            if (connection != null) connection.disconnect();
        }
    }

    private static byte[] readAll(InputStream stream, int maxBytes) throws IOException {
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
