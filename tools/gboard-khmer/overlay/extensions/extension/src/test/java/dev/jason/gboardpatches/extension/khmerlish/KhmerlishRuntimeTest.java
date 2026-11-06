package dev.jason.gboardpatches.extension.khmerlish;

import android.app.Application;
import android.os.Bundle;
import android.text.InputType;
import android.view.inputmethod.EditorInfo;
import android.view.inputmethod.InputConnection;
import android.view.inputmethod.ExtractedText;
import android.view.inputmethod.SurroundingText;

import org.junit.Assert;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;

import java.lang.reflect.Proxy;

import dev.jason.gboardpatches.extension.settings.GboardPatchesSettingsContract;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = 33)
public final class KhmerlishRuntimeTest {
    @Test public void excludesPasswordsEmailUriNumbersAndPrivateFields() {
        EditorInfo info = new EditorInfo();
        info.inputType = InputType.TYPE_CLASS_TEXT;
        Assert.assertTrue(KhmerlishRuntime.isSafeField(info));
        int[] excluded = {
                InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD,
                InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_VISIBLE_PASSWORD,
                InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_WEB_PASSWORD,
                InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS,
                InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_WEB_EMAIL_ADDRESS,
                InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI,
                InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS,
                InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_VARIATION_PASSWORD,
                InputType.TYPE_CLASS_PHONE,
        };
        for (int type : excluded) {
            info.inputType = type;
            Assert.assertFalse("inputType " + type, KhmerlishRuntime.isSafeField(info));
        }
        info.inputType = InputType.TYPE_CLASS_TEXT;
        info.imeOptions = EditorInfo.IME_FLAG_NO_PERSONALIZED_LEARNING;
        Assert.assertFalse(KhmerlishRuntime.isSafeField(info));
        Assert.assertFalse(KhmerlishRuntime.isSafeField(null));
    }

    @Test public void togglesAreOffByDefaultAndScreenIsFeatureGated() {
        Application app = RuntimeEnvironment.getApplication();
        KhmerlishSettings.setEnabled(app, false);
        Assert.assertFalse(KhmerlishSettings.isEnabled(app));
        if (app.getApplicationInfo().metaData == null) app.getApplicationInfo().metaData = new Bundle();
        app.getApplicationInfo().metaData.putBoolean("dev.jason.gboardpatches.feature.khmerlish", true);
        KhmerlishSettingsFeature feature = new KhmerlishSettingsFeature(app);
        Assert.assertTrue(feature.isAvailable(app));
        java.util.List<GboardPatchesSettingsContract.Feature> entries = new java.util.ArrayList<>();
        KhmerlishSettingsFeature.append(app, entries);
        Assert.assertEquals(1, entries.size());
        Assert.assertEquals(feature.getEntryTitle(), entries.get(0).getEntryTitle());
        GboardPatchesSettingsContract.FeatureHost host = new GboardPatchesSettingsContract.FeatureHost() {
            @Override public android.content.Context getContext() { return app; }
            @Override public void submit(GboardPatchesSettingsContract.Intent ignored) {}
        };
        GboardPatchesSettingsContract.ToggleRow toggle =
                (GboardPatchesSettingsContract.ToggleRow) feature.buildScreen(host)
                        .getSections().get(0).getItems().get(0);
        Assert.assertFalse(toggle.isChecked());
        toggle.getToggleAction().accept(true);
        Assert.assertTrue(KhmerlishSettings.isEnabled(app));
        toggle.getToggleAction().accept(false);
        Assert.assertFalse(KhmerlishSettings.isEnabled(app));
        app.getApplicationInfo().metaData.putBoolean("dev.jason.gboardpatches.feature.khmerlish", false);
        Assert.assertFalse(feature.isAvailable(app));
    }

    @Test public void staleSelectionAndUnavailableOffsetsFailSafely() {
        FakeEditor editor = new FakeEditor("nv ");
        InputConnection connection = editor.connection();
        Assert.assertEquals("nv ", KhmerlishRuntime.readBeforeAtCursor(connection, 3, 3).toString());
        Assert.assertNull(KhmerlishRuntime.readBeforeAtCursor(connection, 2, 2));
        Assert.assertNull(KhmerlishRuntime.readBeforeAtCursor(connection, 2, 3));
        editor.noSurroundingOffset = true;
        Assert.assertEquals("nv ", KhmerlishRuntime.readBeforeAtCursor(connection, 3, 3).toString());
        Assert.assertNull(KhmerlishRuntime.readBeforeAtCursor(connection, 2, 2));
        editor.noExtracted = true;
        Assert.assertNull(KhmerlishRuntime.readBeforeAtCursor(connection, 3, 3));
    }

    @Test public void batchedEditRechecksSuffixAndRestoresOnFailedInsertion() {
        FakeEditor success = new FakeEditor("nv ");
        KhmerlishController.Edit edit = new KhmerlishController.Edit(3, "នៅ ", 4);
        Assert.assertTrue(KhmerlishRuntime.applyEdit(success.connection(), "nv ", edit));
        Assert.assertEquals("នៅ ", success.text.toString());
        Assert.assertEquals(1, success.batchEnds);

        FakeEditor stale = new FakeEditor("na ");
        Assert.assertFalse(KhmerlishRuntime.applyEdit(stale.connection(), "nv ", edit));
        Assert.assertEquals("na ", stale.text.toString());
        Assert.assertEquals(0, stale.batchEnds);

        FakeEditor failed = new FakeEditor("nv ");
        failed.failFirstCommit = true;
        Assert.assertFalse(KhmerlishRuntime.applyEdit(failed.connection(), "nv ", edit));
        Assert.assertEquals("nv ", failed.text.toString());
        Assert.assertEquals(1, failed.batchEnds);

        FakeEditor noBatch = new FakeEditor("nv ");
        noBatch.supportBatch = false;
        Assert.assertFalse(KhmerlishRuntime.applyEdit(noBatch.connection(), "nv ", edit));
        Assert.assertEquals("nv ", noBatch.text.toString());
    }

    private static final class FakeEditor {
        final StringBuilder text;
        boolean failFirstCommit;
        boolean supportBatch = true;
        boolean noSurroundingOffset;
        boolean noExtracted;
        int batchEnds;
        FakeEditor(String value) { text = new StringBuilder(value); }
        InputConnection connection() {
            return (InputConnection) Proxy.newProxyInstance(getClass().getClassLoader(),
                    new Class<?>[]{InputConnection.class}, (proxy, method, args) -> {
                        switch (method.getName()) {
                            case "getSelectedText": return null;
                            case "getSurroundingText":
                                return new SurroundingText(text.toString(), text.length(), text.length(),
                                        noSurroundingOffset ? -1 : 0);
                            case "getExtractedText":
                                if (noExtracted) return null;
                                ExtractedText extracted = new ExtractedText();
                                extracted.startOffset = 0;
                                extracted.selectionStart = extracted.selectionEnd = text.length();
                                return extracted;
                            case "getTextBeforeCursor":
                                int count = (Integer) args[0];
                                return text.substring(Math.max(0, text.length() - count));
                            case "beginBatchEdit": return supportBatch;
                            case "endBatchEdit": batchEnds++; return true;
                            case "deleteSurroundingText":
                                int before = (Integer) args[0];
                                text.delete(text.length() - before, text.length());
                                return true;
                            case "commitText":
                                if (failFirstCommit) { failFirstCommit = false; return false; }
                                text.append((CharSequence) args[0]);
                                return true;
                            case "toString": return "FakeEditor";
                            default:
                                if (method.getReturnType() == boolean.class) return false;
                                if (method.getReturnType() == int.class) return 0;
                                return null;
                        }
                    });
        }
    }
}
