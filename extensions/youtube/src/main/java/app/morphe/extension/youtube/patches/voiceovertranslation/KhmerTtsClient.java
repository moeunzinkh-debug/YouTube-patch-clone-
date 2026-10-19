/*
 * Copyright 2026 Morphe.
 * https://github.com/MorpheApp/morphe-patches
 *
 * See the included NOTICE file for GPLv3 Section 7 terms that apply to this code.
 */

package app.morphe.extension.youtube.patches.voiceovertranslation;

import android.util.Base64;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import org.json.JSONTokener;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Iterator;
import java.util.Locale;

import app.morphe.extension.shared.Utils;

/** Direct HTTPS client for the user's FastAPI-hosted Khmer TTS Space. */
final class KhmerTtsClient {

    static final String VOICE_ID = "takumi-khmer-server";

    private static final String BASE_URL = "https://takumi0002-tts-kh.hf.space";
    private static final String OPENAPI_URL = BASE_URL + "/openapi.json";
    private static final int CONNECT_TIMEOUT_MS = 15_000;
    // Hugging Face Spaces may need time to wake from sleep before synthesizing audio.
    private static final int READ_TIMEOUT_MS = 120_000;
    private static final int MAX_AUDIO_BYTES = 32 * 1024 * 1024;
    private static final String MULTIPART_BOUNDARY = "----YouTubePatchKhmerTtsBoundary7MA4YWxkTrZu0gW";
    private static final Object endpointLock = new Object();

    private static volatile Endpoint cachedEndpoint;

    private KhmerTtsClient() {}

    static boolean supports(String languageTag) {
        return "km".equalsIgnoreCase(VoiceCatalog.getIso639(languageTag));
    }

    /** Synthesizes Khmer text using the FastAPI endpoint discovered from its OpenAPI schema. */
    static byte[] synthesize(String text) throws Exception {
        Utils.verifyOffMainThread();
        if (text == null || text.trim().isEmpty()) return new byte[0];

        Endpoint endpoint = getEndpoint();
        HttpURLConnection connection = null;
        try {
            URL requestUrl = new URL(endpoint.buildUrl(text));
            connection = (HttpURLConnection) requestUrl.openConnection();
            connection.setConnectTimeout(CONNECT_TIMEOUT_MS);
            connection.setReadTimeout(READ_TIMEOUT_MS);
            connection.setRequestMethod(endpoint.method);
            connection.setRequestProperty("Accept", "audio/*, application/octet-stream, application/json");
            connection.setRequestProperty("User-Agent", "YouTube-Patch-Clone/1.0");

            byte[] requestBody = endpoint.buildBody(text);
            if (requestBody != null) {
                connection.setDoOutput(true);
                String requestContentType = endpoint.requestContentType;
                if ("multipart/form-data".equals(requestContentType)) {
                    requestContentType += "; boundary=" + MULTIPART_BOUNDARY;
                }
                connection.setRequestProperty("Content-Type", requestContentType);
                try (OutputStream output = connection.getOutputStream()) {
                    output.write(requestBody);
                }
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
            return extractAudio(response, contentType, 0);
        } finally {
            if (connection != null) connection.disconnect();
        }
    }

    private static Endpoint getEndpoint() throws Exception {
        Endpoint endpoint = cachedEndpoint;
        if (endpoint != null) return endpoint;

        synchronized (endpointLock) {
            endpoint = cachedEndpoint;
            if (endpoint != null) return endpoint;
            JSONObject openApi = getJson(OPENAPI_URL);
            endpoint = discoverEndpoint(openApi);
            if (endpoint == null) {
                throw new IOException("No Khmer text-to-speech endpoint was found in " + OPENAPI_URL);
            }
            cachedEndpoint = endpoint;
            return endpoint;
        }
    }

    private static JSONObject getJson(String url) throws Exception {
        HttpURLConnection connection = null;
        try {
            connection = (HttpURLConnection) new URL(url).openConnection();
            connection.setConnectTimeout(CONNECT_TIMEOUT_MS);
            connection.setReadTimeout(READ_TIMEOUT_MS);
            connection.setRequestMethod("GET");
            connection.setRequestProperty("Accept", "application/json");
            connection.setRequestProperty("User-Agent", "YouTube-Patch-Clone/1.0");
            int status = connection.getResponseCode();
            InputStream stream = status >= 400 ? connection.getErrorStream() : connection.getInputStream();
            byte[] bytes = stream == null ? new byte[0] : readAll(stream, 2 * 1024 * 1024);
            if (status < 200 || status >= 300) {
                throw new IOException("FastAPI OpenAPI discovery returned HTTP " + status);
            }
            return new JSONObject(new String(bytes, StandardCharsets.UTF_8));
        } finally {
            if (connection != null) connection.disconnect();
        }
    }

    /** Android's JSONObject exposes keys(), not the JSON-java keySet() API. */
    private static List<String> jsonKeys(JSONObject object) {
        List<String> keys = new ArrayList<>();
        Iterator<String> iterator = object.keys();
        while (iterator.hasNext()) keys.add(iterator.next());
        return keys;
    }

    private static Endpoint discoverEndpoint(JSONObject openApi) throws JSONException {
        JSONObject paths = openApi.optJSONObject("paths");
        if (paths == null) return null;

        Endpoint best = null;
        int bestScore = Integer.MIN_VALUE;
        String[] methods = {"post", "get", "put"};
        for (String path : jsonKeys(paths)) {
            if (path.contains("{")) continue; // Path parameters need API-specific values.
            JSONObject pathItem = paths.optJSONObject(path);
            if (pathItem == null) continue;

            for (String method : methods) {
                JSONObject operation = pathItem.optJSONObject(method);
                if (operation == null) continue;

                JSONObject bodySchema = null;
                String requestMime = null;
                JSONObject requestBody = operation.optJSONObject("requestBody");
                if (requestBody != null) {
                    JSONObject content = requestBody.optJSONObject("content");
                    if (content != null) {
                        String[] contentTypes = {
                                "application/json", "application/x-www-form-urlencoded", "multipart/form-data"
                        };
                        for (String candidate : contentTypes) {
                            JSONObject definition = content.optJSONObject(candidate);
                            if (definition != null) {
                                bodySchema = resolveSchema(openApi, definition.optJSONObject("schema"));
                                requestMime = candidate;
                                break;
                            }
                        }
                    }
                }

                JSONArray parameters = mergeParameters(
                        openApi, pathItem.optJSONArray("parameters"), operation.optJSONArray("parameters"));
                String bodyTextField = findTextField(bodySchema);
                String queryTextField = findQueryTextField(parameters);
                if (bodyTextField == null && queryTextField == null) continue;

                String operationName = describeOperation(path, operation).toLowerCase(Locale.ROOT);
                boolean nameLooksLikeTts = containsAny(operationName,
                        "tts", "text-to-speech", "text_to_speech", "speech", "synth", "voice", "audio", "generate");
                boolean returnsAudio = responseLooksLikeAudio(operation);
                if (!nameLooksLikeTts && !returnsAudio) continue;

                int score = method.equals("post") ? 100 : method.equals("put") ? 60 : 30;
                if (nameLooksLikeTts) score += 40;
                if (returnsAudio) score += 50;
                if (bodyTextField != null) score += 10;
                if (path.toLowerCase(Locale.ROOT).contains("tts")) score += 20;

                Endpoint candidate = new Endpoint(path, method.toUpperCase(Locale.ROOT), requestMime,
                        bodySchema, bodyTextField, parameters, queryTextField);
                if (score > bestScore) {
                    best = candidate;
                    bestScore = score;
                }
            }
        }
        return best;
    }

    private static JSONObject resolveSchema(JSONObject openApi, JSONObject schema) {
        if (schema == null) return null;
        String reference = schema.optString("$ref", "");
        if (reference.isEmpty() || !reference.startsWith("#/components/schemas/")) return schema;
        JSONObject components = openApi.optJSONObject("components");
        JSONObject schemas = components == null ? null : components.optJSONObject("schemas");
        JSONObject resolved = schemas == null ? null : schemas.optJSONObject(reference.substring(
                "#/components/schemas/".length()));
        return resolved == null ? schema : resolved;
    }

    private static JSONArray mergeParameters(JSONObject openApi, JSONArray pathParameters,
                                              JSONArray operationParameters) {
        JSONArray result = new JSONArray();
        appendResolvedParameters(result, openApi, pathParameters);
        appendResolvedParameters(result, openApi, operationParameters);
        return result;
    }

    private static void appendResolvedParameters(JSONArray destination, JSONObject openApi, JSONArray source) {
        if (source == null) return;
        for (int i = 0; i < source.length(); i++) {
            JSONObject parameter = source.optJSONObject(i);
            if (parameter == null) continue;
            String reference = parameter.optString("$ref", "");
            if (reference.startsWith("#/components/parameters/")) {
                JSONObject components = openApi.optJSONObject("components");
                JSONObject definitions = components == null ? null : components.optJSONObject("parameters");
                parameter = definitions == null ? null : definitions.optJSONObject(
                        reference.substring("#/components/parameters/".length()));
            }
            if (parameter != null) destination.put(parameter);
        }
    }

    private static String findTextField(JSONObject schema) {
        if (schema == null) return null;
        if ("string".equals(schema.optString("type"))) return "__raw_string__";
        JSONObject properties = schema.optJSONObject("properties");
        if (properties == null) return null;
        for (String name : jsonKeys(properties)) {
            if (isTextField(name)) return name;
        }
        return null;
    }

    private static String findQueryTextField(JSONArray parameters) {
        for (int i = 0; i < parameters.length(); i++) {
            JSONObject parameter = parameters.optJSONObject(i);
            if (parameter != null && "query".equals(parameter.optString("in"))
                    && isTextField(parameter.optString("name"))) {
                return parameter.optString("name");
            }
        }
        return null;
    }

    private static boolean isTextField(String name) {
        String normalized = name == null ? "" : name.toLowerCase(Locale.ROOT).replaceAll("[^a-z]", "");
        return normalized.equals("text") || normalized.equals("input") || normalized.equals("inputtext")
                || normalized.equals("textinput") || normalized.equals("sentence")
                || normalized.equals("prompt") || normalized.equals("content")
                || normalized.equals("utterance") || normalized.equals("texttospeak");
    }

    private static String describeOperation(String path, JSONObject operation) {
        StringBuilder result = new StringBuilder(path);
        result.append(' ').append(operation.optString("operationId", ""));
        result.append(' ').append(operation.optString("summary", ""));
        result.append(' ').append(operation.optString("description", ""));
        JSONArray tags = operation.optJSONArray("tags");
        if (tags != null) {
            for (int i = 0; i < tags.length(); i++) result.append(' ').append(tags.optString(i));
        }
        return result.toString();
    }

    private static boolean responseLooksLikeAudio(JSONObject operation) {
        JSONObject responses = operation.optJSONObject("responses");
        if (responses == null) return false;
        for (String status : jsonKeys(responses)) {
            JSONObject response = responses.optJSONObject(status);
            JSONObject content = response == null ? null : response.optJSONObject("content");
            if (content == null) continue;
            for (String type : jsonKeys(content)) {
                if (isAudioContentType(type)) return true;
            }
        }
        return false;
    }

    private static boolean containsAny(String value, String... choices) {
        for (String choice : choices) if (value.contains(choice)) return true;
        return false;
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
            return downloadAudio(resolveAudioUrl(text), depth + 1);
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
        if (depth > 4) throw new IOException("Too many nested TTS audio responses");
        String text = value.trim();
        if (text.startsWith("data:audio/") && text.contains(";base64,")) {
            return decodeBase64(text.substring(text.indexOf(",") + 1));
        }
        if (text.startsWith("https://") || text.startsWith("http://") || text.startsWith("/")) {
            return downloadAudio(resolveAudioUrl(text), depth + 1);
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

    private static byte[] downloadAudio(String url, int depth) throws Exception {
        if (depth > 4) throw new IOException("Too many nested TTS audio responses");
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
            return extractAudio(bytes, contentType, depth);
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

    private static final class Endpoint {
        final String path;
        final String method;
        final String requestContentType;
        final JSONObject bodySchema;
        final String bodyTextField;
        final JSONArray parameters;
        final String queryTextField;

        Endpoint(String path, String method, String requestContentType, JSONObject bodySchema,
                 String bodyTextField, JSONArray parameters, String queryTextField) {
            this.path = path;
            this.method = method;
            this.requestContentType = requestContentType;
            this.bodySchema = bodySchema;
            this.bodyTextField = bodyTextField;
            this.parameters = parameters;
            this.queryTextField = queryTextField;
        }

        String buildUrl(String text) throws Exception {
            List<String> query = new ArrayList<>();
            if (parameters != null) {
                for (int i = 0; i < parameters.length(); i++) {
                    JSONObject parameter = parameters.optJSONObject(i);
                    if (parameter == null || !"query".equals(parameter.optString("in"))) continue;
                    String name = parameter.optString("name");
                    Object value = valueForField(name, parameter.optJSONObject("schema"),
                            required(parameter.optBoolean("required", false)), text);
                    if (value != null) query.add(encode(name) + "=" + encode(String.valueOf(value)));
                }
            }
            return BASE_URL + path + (query.isEmpty() ? "" : "?" + String.join("&", query));
        }

        byte[] buildBody(String text) throws Exception {
            if (requestContentType == null || bodySchema == null) return null;
            String schemaType = bodySchema.optString("type");
            if ("string".equals(schemaType)) return JSONObject.quote(text).getBytes(StandardCharsets.UTF_8);

            JSONObject properties = bodySchema.optJSONObject("properties");
            if (properties == null) return null;
            JSONObject values = new JSONObject();
            for (String name : jsonKeys(properties)) {
                JSONObject property = properties.optJSONObject(name);
                Object value = valueForField(name, property, isRequired(name), text);
                if (value != null) values.put(name, value);
            }

            if (requestContentType.equals("application/json")) {
                return values.toString().getBytes(StandardCharsets.UTF_8);
            }
            if (requestContentType.equals("application/x-www-form-urlencoded")) {
                List<String> fields = new ArrayList<>();
                for (String name : jsonKeys(values)) {
                    fields.add(encode(name) + "=" + encode(String.valueOf(values.get(name))));
                }
                return String.join("&", fields).getBytes(StandardCharsets.UTF_8);
            }
            if (requestContentType.equals("multipart/form-data")) {
                // Let HttpURLConnection generate the boundary only when a file is sent; for the
                // text-only form used by TTS, a deterministic boundary is sufficient.
                String boundary = MULTIPART_BOUNDARY;
                StringBuilder form = new StringBuilder();
                for (String name : jsonKeys(values)) {
                    form.append("--").append(boundary).append("\r\n")
                            .append("Content-Disposition: form-data; name=\"").append(name).append("\"\r\n\r\n")
                            .append(values.get(name)).append("\r\n");
                }
                form.append("--").append(boundary).append("--\r\n");
                return form.toString().getBytes(StandardCharsets.UTF_8);
            }
            return null;
        }

        private boolean isRequired(String field) {
            JSONArray required = bodySchema.optJSONArray("required");
            if (required == null) return false;
            for (int i = 0; i < required.length(); i++) {
                if (field.equals(required.optString(i))) return true;
            }
            return false;
        }

        private Object valueForField(String name, JSONObject schema, boolean required, String text) throws IOException {
            if (isTextField(name)) return text;
            String normalized = name.toLowerCase(Locale.ROOT).replaceAll("[^a-z]", "");
            if (normalized.equals("language") || normalized.equals("lang")
                    || normalized.equals("languagecode") || normalized.equals("locale")) {
                JSONArray values = schema == null ? null : schema.optJSONArray("enum");
                if (values != null) {
                    for (int i = 0; i < values.length(); i++) {
                        String option = values.optString(i);
                        if (option.equalsIgnoreCase("km") || option.equalsIgnoreCase("km-KH")) return option;
                    }
                }
                return "km";
            }
            if (normalized.contains("speed") || normalized.equals("rate") || normalized.equals("pitch")) {
                if (schema != null && schema.has("default")) return schema.opt("default");
                return required ? 1.0 : null;
            }
            if (schema != null && schema.has("default")) return schema.opt("default");
            JSONArray choices = schema == null ? null : schema.optJSONArray("enum");
            if (choices != null && choices.length() == 1) return choices.opt(0);
            if (required) {
                throw new IOException("FastAPI TTS endpoint requires unsupported input '" + name + "'");
            }
            return null;
        }

        private static boolean required(boolean required) {
            return required;
        }

        private static String encode(String value) throws Exception {
            return URLEncoder.encode(value, StandardCharsets.UTF_8.name());
        }
    }
}
