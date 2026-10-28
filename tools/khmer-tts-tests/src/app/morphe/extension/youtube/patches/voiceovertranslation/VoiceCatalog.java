package app.morphe.extension.youtube.patches.voiceovertranslation;
final class VoiceCatalog {
    static String getIso639(String language) {
        return language == null ? "" : language.split("[-_]", 2)[0];
    }
}
