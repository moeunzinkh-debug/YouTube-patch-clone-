package dev.jason.gboardpatches.extension.khmerlish;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import android.os.Build;

import java.io.File;
import java.util.Collections;
import java.util.ConcurrentModificationException;
import java.util.LinkedHashMap;
import java.util.Map;

/** App-private, no-backup SQLite store. Only explicitly added/imported pairs are saved. */
final class KhmerlishPersonalStore {
    private static final Object LOCK = new Object();
    private static Helper helper;

    private KhmerlishPersonalStore() {}

    private static Helper helper(Context context) {
        if (context == null) throw new IllegalArgumentException("Context required");
        Context app = context.getApplicationContext();
        if (app == null) app = context;
        synchronized (LOCK) {
            if (helper == null) {
                // Do not accidentally create a second dictionary in device-
                // protected storage. The ordinary application context uses
                // credential-protected storage and is unavailable before unlock.
                if (Build.VERSION.SDK_INT >= 24 && app.isDeviceProtectedStorage()) {
                    throw new IllegalStateException("Credential-protected storage required");
                }
                helper = new Helper(app);
            }
            return helper;
        }
    }

    private static String databasePath(Context context) {
        File directory = context.getNoBackupFilesDir();
        if (directory == null) throw new IllegalStateException("Personal storage unavailable");
        return new File(directory, "khmerlish_personal_dictionary_v1.db").getAbsolutePath();
    }

    private static final class Helper extends SQLiteOpenHelper {
        Helper(Context context) {
            // Explicit exports are available; Android automatic backup must not
            // silently copy a user's private word list into another app backup.
            super(context, databasePath(context), null, 1);
        }
        @Override public void onCreate(SQLiteDatabase db) {
            db.execSQL("CREATE TABLE words (roman TEXT PRIMARY KEY NOT NULL, khmer TEXT NOT NULL)");
        }
        @Override public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
            throw new IllegalStateException("Unsupported personal dictionary version");
        }
    }

    static Map<String, String> read(Context context) {
        synchronized (LOCK) {
            return Collections.unmodifiableMap(read(helper(context).getReadableDatabase()));
        }
    }

    private static LinkedHashMap<String, String> read(SQLiteDatabase db) {
        LinkedHashMap<String, String> words = new LinkedHashMap<>();
        try (Cursor cursor = db.query("words", new String[]{"roman", "khmer"},
                null, null, null, null, "roman ASC")) {
            while (cursor.moveToNext()) {
                String key = cursor.getString(0), value = cursor.getString(1);
                if (key == null || !key.equals(KhmerlishPersonalData.roman(key))
                        || value == null || !value.equals(KhmerlishPersonalData.khmer(value))
                        || words.size() >= KhmerlishPersonalData.MAX_ENTRIES
                        || words.put(key, value) != null) {
                    throw new IllegalStateException("Invalid personal dictionary data");
                }
            }
        }
        return words;
    }

    /** Add or edit one entry; refuse accidental replacement of another key. */
    static void save(Context context, String oldKey, String oldValue, String rawKey, String rawValue) {
        String key = KhmerlishPersonalData.roman(rawKey);
        String value = KhmerlishPersonalData.khmer(rawValue);
        if (key == null || value == null) throw new IllegalArgumentException("invalid_entry");
        synchronized (LOCK) {
            SQLiteDatabase db = helper(context).getWritableDatabase();
            db.beginTransaction();
            try {
                Map<String, String> existing = read(db);
                if (oldKey != null && (!existing.containsKey(oldKey)
                        || !existing.get(oldKey).equals(oldValue))) {
                    throw new ConcurrentModificationException();
                }
                if ((oldKey == null || !oldKey.equals(key)) && existing.containsKey(key)) {
                    throw new IllegalArgumentException("duplicate_key");
                }
                if (oldKey == null && existing.size() >= KhmerlishPersonalData.MAX_ENTRIES) {
                    throw new IllegalArgumentException("too_many_entries");
                }
                put(db, key, value);
                if (oldKey != null && !oldKey.equals(key)) {
                    db.delete("words", "roman = ?", new String[]{oldKey});
                }
                db.setTransactionSuccessful();
            } finally {
                db.endTransaction();
            }
        }
        KhmerlishRuntime.personalChanged(context);
    }

    static void delete(Context context, String key, String expectedValue) {
        synchronized (LOCK) {
            SQLiteDatabase db = helper(context).getWritableDatabase();
            db.beginTransaction();
            try {
                Map<String, String> existing = read(db);
                if (!existing.containsKey(key) || !existing.get(key).equals(expectedValue)) {
                    throw new ConcurrentModificationException();
                }
                db.delete("words", "roman = ?", new String[]{key});
                db.setTransactionSuccessful();
            } finally {
                db.endTransaction();
            }
        }
        KhmerlishRuntime.personalChanged(context);
    }

    static final class Preview {
        final Map<String, String> expected, incoming;
        final int added, conflicts, unchanged;
        Preview(Map<String, String> expected, Map<String, String> incoming,
                int added, int conflicts, int unchanged) {
            this.expected = expected;
            this.incoming = Collections.unmodifiableMap(new LinkedHashMap<>(incoming));
            this.added = added;
            this.conflicts = conflicts;
            this.unchanged = unchanged;
        }
    }

    static Preview preview(Context context, Map<String, String> incoming) {
        if (incoming == null || incoming.isEmpty() || incoming.size() > KhmerlishPersonalData.MAX_ENTRIES) {
            throw new IllegalArgumentException("invalid_import");
        }
        Map<String, String> existing = read(context);
        int added = 0, conflicts = 0, unchanged = 0;
        for (Map.Entry<String, String> entry : incoming.entrySet()) {
            String previous = existing.get(entry.getKey());
            if (previous == null) added++;
            else if (previous.equals(entry.getValue())) unchanged++;
            else conflicts++;
        }
        return new Preview(existing, incoming, added, conflicts, unchanged);
    }

    /** All-or-nothing merge; conflicts are preserved unless explicitly replaced. */
    static void importEntries(Context context, Preview preview, Map<String, String> incoming,
            boolean replaceConflicts) {
        if (preview == null || incoming == null || incoming.isEmpty()
                || incoming.size() > KhmerlishPersonalData.MAX_ENTRIES) {
            throw new IllegalArgumentException("invalid_import");
        }
        if (!preview.incoming.equals(incoming)) throw new ConcurrentModificationException();
        synchronized (LOCK) {
            SQLiteDatabase db = helper(context).getWritableDatabase();
            db.beginTransaction();
            try {
                Map<String, String> existing = read(db);
                if (!existing.equals(preview.expected)) throw new ConcurrentModificationException();
                if ((long) existing.size() + preview.added > KhmerlishPersonalData.MAX_ENTRIES) {
                    throw new IllegalArgumentException("too_many_entries");
                }
                for (Map.Entry<String, String> entry : incoming.entrySet()) {
                    String key = KhmerlishPersonalData.roman(entry.getKey());
                    String value = KhmerlishPersonalData.khmer(entry.getValue());
                    if (key == null || !key.equals(entry.getKey()) || value == null
                            || !value.equals(entry.getValue())) {
                        throw new IllegalArgumentException("invalid_entry");
                    }
                    if (!existing.containsKey(key) || replaceConflicts) put(db, key, value);
                }
                db.setTransactionSuccessful();
            } finally {
                db.endTransaction();
            }
        }
        KhmerlishRuntime.personalChanged(context);
    }

    private static void put(SQLiteDatabase db, String key, String value) {
        ContentValues row = new ContentValues();
        row.put("roman", key);
        row.put("khmer", value);
        if (db.insertWithOnConflict("words", null, row, SQLiteDatabase.CONFLICT_REPLACE) == -1) {
            throw new IllegalStateException("Personal dictionary write failed");
        }
    }
}
