package app.morphe.extension.simsimi;

/** Fail-closed recognition of the English Conversation list shown by the user. */
public final class ConversationScreen {
    private ConversationScreen() { }
    public static int flags(CharSequence value, float topDp) {
        if (value == null) return 0;
        String text = value.toString().trim();
        if (topDp >= 0 && topDp <= 160 && "Conversation".equals(text)) return 1;
        if ("Chat room you're participating in".equals(text)
                || "Group chat rooms by interest".equals(text)) return 2;
        return 0;
    }
    public static boolean allows(int flags) { return (flags & 3) == 3; }
}
