/* Copyright (C) 2026. This fork is distributed under GPL-3.0-or-later. */
package dev.jason.gboardpatches.extension.directtranslate;

import org.json.JSONArray;
import org.json.JSONException;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.regex.Pattern;

/** Narrow client for Google's undocumented, unsupported GTX endpoint. */
final class GtxClient implements TranslateCoordinator.Client {
    static final String ENDPOINT = "https://translate.googleapis.com/translate_a/single";
    private static final Pattern LANGUAGE = Pattern.compile("[A-Za-z0-9_-]{1,24}");
    private static final int MAX_TEXT_CHARS = 8192;
    private static final int MAX_RESPONSE_BYTES = 1024 * 1024;

    interface ConnectionFactory {
        HttpURLConnection open(URL url) throws IOException;
    }

    static final class Translation {
        final String text;
        final String detectedLanguage;

        Translation(String text, String detectedLanguage) {
            this.text = text;
            this.detectedLanguage = detectedLanguage;
        }
    }

    private final ConnectionFactory connections;

    GtxClient() {
        this(url -> (HttpURLConnection) url.openConnection());
    }

    GtxClient(ConnectionFactory connections) {
        this.connections = connections;
    }

    @Override
    public Translation translate(String text, String source, String target) throws IOException, JSONException {
        if (text == null || text.isEmpty() || text.length() > MAX_TEXT_CHARS) {
            throw new IOException("Invalid text length");
        }
        String from = source == null || source.isEmpty() ? "auto" : source;
        if (!LANGUAGE.matcher(from).matches() || target == null || !LANGUAGE.matcher(target).matches()) {
            throw new IOException("Invalid language code");
        }
        // User text is in the POST body, never in the URL or application logs.
        String query = "?client=gtx&sl=" + encode(from) + "&tl=" + encode(target) + "&dt=t";
        URL url = new URL(ENDPOINT + query);
        byte[] body = ("q=" + encode(text)).getBytes(StandardCharsets.UTF_8);
        HttpURLConnection connection = connections.open(url);
        try {
            connection.setInstanceFollowRedirects(false);
            connection.setUseCaches(false);
            connection.setConnectTimeout(6000);
            connection.setReadTimeout(10000);
            connection.setRequestMethod("POST");
            connection.setDoOutput(true);
            connection.setRequestProperty("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8");
            connection.setRequestProperty("Accept", "application/json");
            connection.setRequestProperty("User-Agent", "Mozilla/5.0");
            connection.setFixedLengthStreamingMode(body.length);
            try (OutputStream output = connection.getOutputStream()) {
                output.write(body);
            }
            if (connection.getResponseCode() != HttpURLConnection.HTTP_OK) {
                // Do not follow redirects, retry, or include response bodies/URLs in errors.
                throw new IOException("Google Translate request failed");
            }
            try (InputStream input = connection.getInputStream()) {
                ByteArrayOutputStream result = new ByteArrayOutputStream();
                byte[] buffer = new byte[4096];
                int count;
                while ((count = input.read(buffer)) != -1) {
                    if (result.size() + count > MAX_RESPONSE_BYTES) {
                        throw new IOException("Response too large");
                    }
                    result.write(buffer, 0, count);
                }
                return parse(result.toString("UTF-8"));
            }
        } finally {
            connection.disconnect();
        }
    }

    static Translation parse(String json) throws JSONException, IOException {
        JSONArray root = new JSONArray(json);
        JSONArray segments = root.optJSONArray(0);
        if (segments == null) throw new IOException("Invalid translation response");
        StringBuilder translated = new StringBuilder();
        for (int index = 0; index < segments.length(); index++) {
            JSONArray segment = segments.optJSONArray(index);
            if (segment == null || segment.isNull(0)) continue;
            Object piece = segment.opt(0);
            if (!(piece instanceof String)) throw new IOException("Invalid translation segment");
            translated.append((String) piece);
        }
        if (translated.length() == 0) throw new IOException("Empty translation");
        Object detected = root.opt(2);
        String detectedLanguage = detected instanceof String && LANGUAGE.matcher((String) detected).matches()
                ? (String) detected : null;
        return new Translation(translated.toString(), detectedLanguage);
    }

    private static String encode(String value) throws IOException {
        return URLEncoder.encode(value, "UTF-8");
    }
}
