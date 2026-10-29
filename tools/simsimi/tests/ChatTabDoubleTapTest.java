import app.morphe.extension.simsimi.ChatTabDoubleTap;

public final class ChatTabDoubleTapTest {
    private static int checks;
    private static void check(boolean value, String label) {
        if (!value) throw new AssertionError(label);
        checks++;
    }
    public static void main(String[] args) {
        ChatTabDoubleTap taps = new ChatTabDoubleTap();
        check(!taps.tap(1, true, true, 100), "first selected Chat tap is unchanged");
        check(taps.tap(1, true, true, 350), "double tap within interval");
        check(!taps.tap(1, true, true, 400), "a third tap starts a new pair");
        check(!taps.tap(0, true, true, 450), "other tab resets the pair");
        check(!taps.tap(1, true, true, 500), "return to Chat is not a pair");
        check(!taps.tap(1, false, true, 600), "selecting Chat from another tab resets");
        check(!taps.tap(1, true, true, 650), "single reselect stays unchanged");
        check(!taps.tap(1, true, false, 750), "room or unknown screen resets");
        check(!taps.tap(1, true, true, 800), "new Conversation pair starts fresh");
        check(!taps.tap(1, true, true, 1351), "slower than 550ms is not a double tap");
        check(taps.tap(1, true, true, 1901), "550ms inclusive");
        check(!taps.tap(1, true, true, 2000), "new pair after success");
        check(!taps.tap(1, true, true, 2030), "duplicate callback below 40ms is not a double tap");
        check(taps.tap(1, true, true, 2070), "40ms inclusive");
        check(!taps.tap(1, true, true, 3000), "start before clock reversal");
        check(!taps.tap(1, true, true, 2500), "clock reversal resets timing");
        check(taps.tap(1, true, true, 2600), "new pair after clock reversal");
        check(!taps.tap(1, true, true, -1), "negative time resets");
        check(!taps.tap(1, true, true, 3200), "one tap after invalid time");
        taps.reset();
        check(!taps.tap(1, true, true, 3300), "explicit reset");
        System.out.println(checks + " Chat-tab double-tap checks passed");
    }
}
