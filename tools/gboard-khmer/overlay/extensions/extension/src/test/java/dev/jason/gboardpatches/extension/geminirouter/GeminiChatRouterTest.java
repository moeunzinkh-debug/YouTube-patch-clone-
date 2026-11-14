package dev.jason.gboardpatches.extension.geminirouter;

import android.text.InputType;
import android.view.inputmethod.EditorInfo;

import org.junit.Assert;
import org.junit.Test;

public final class GeminiChatRouterTest {
    @Test public void usesOnlyTheRequestedGeminiWebRoute() {
        Assert.assertEquals("https://gemini.google.com/app", GeminiChatRouter.GEMINI_URL);
    }

    @Test public void buildsBoundedTranslationPromptWithoutCredentials() {
        String prompt = GeminiChatRouter.buildPrompt("  hello world  ", "Khmer");
        Assert.assertTrue(prompt.contains("into Khmer"));
        Assert.assertTrue(prompt.endsWith("hello world"));
        Assert.assertFalse(prompt.toLowerCase().contains("api key"));
        String longText = "x".repeat(9000);
        String bounded = GeminiChatRouter.buildPrompt(longText, "English");
        Assert.assertTrue(bounded.endsWith("x".repeat(8000)));
        Assert.assertFalse(bounded.endsWith("x".repeat(8001)));
    }

    @Test public void refusesPasswordAndPrivateEditors() {
        EditorInfo info = new EditorInfo();
        info.inputType = InputType.TYPE_CLASS_TEXT;
        Assert.assertFalse(GeminiChatRouter.isSensitive(info));
        info.inputType = InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD;
        Assert.assertTrue(GeminiChatRouter.isSensitive(info));
        info.inputType = InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_VARIATION_PASSWORD;
        Assert.assertTrue(GeminiChatRouter.isSensitive(info));
        info.inputType = InputType.TYPE_CLASS_TEXT;
        info.imeOptions = EditorInfo.IME_FLAG_NO_PERSONALIZED_LEARNING;
        Assert.assertTrue(GeminiChatRouter.isSensitive(info));
        Assert.assertTrue(GeminiChatRouter.isSensitive(null));
    }
}
