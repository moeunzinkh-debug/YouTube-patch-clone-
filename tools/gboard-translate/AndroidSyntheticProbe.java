/* Standalone Android VM probe. It is not bundled into the released patch. */
package dev.jason.gboardpatches.extension.directtranslate;

public final class AndroidSyntheticProbe {
    public static void main(String[] args) throws Exception {
        GtxClient client = new GtxClient();
        check(client.translate("Hello world", "en", "km"));
        System.out.println("PASS synthetic Android POST en-to-km");
        check(client.translate("សួស្តី", "km", "en"));
        System.out.println("PASS synthetic Android POST km-to-en");
        check(client.translate("How are you?", "auto", "km"));
        System.out.println("PASS synthetic Android POST auto-to-km");
    }

    private static void check(GtxClient.Translation result) {
        if (result == null || result.text == null || result.text.isEmpty()) {
            throw new IllegalStateException("Empty synthetic translation");
        }
    }
}
