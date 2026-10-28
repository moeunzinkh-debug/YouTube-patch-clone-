import app.morphe.extension.simsimi.ConversationScreen;
public final class ConversationScreenTest {
    public static void main(String[] args) {
        int heading = ConversationScreen.flags("Conversation", 48);
        int rooms = ConversationScreen.flags("Chat room you're participating in", 180);
        int interests = ConversationScreen.flags("Group chat rooms by interest", 340);
        check(ConversationScreen.allows(heading | rooms), "participating rooms screen");
        check(ConversationScreen.allows(heading | interests), "interest rooms screen");
        check(!ConversationScreen.allows(heading), "heading alone is insufficient");
        check(!ConversationScreen.allows(rooms | interests), "missing Conversation heading");
        check(!ConversationScreen.allows(ConversationScreen.flags("Rin SimSimi", 48) | rooms), "inside chat");
        check(!ConversationScreen.allows(ConversationScreen.flags("Conversation", 400) | rooms), "chat message is not heading");
        check(!ConversationScreen.allows(ConversationScreen.flags(null, 48) | rooms), "null text");
        check(!ConversationScreen.allows(ConversationScreen.flags("Home", 48) | rooms), "other tab");
        System.out.println("8 Conversation screen checks passed");
    }
    private static void check(boolean value, String name) {
        if (!value) throw new AssertionError(name);
    }
}
