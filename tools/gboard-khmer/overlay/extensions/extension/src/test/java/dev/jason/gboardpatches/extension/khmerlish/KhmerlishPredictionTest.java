package dev.jason.gboardpatches.extension.khmerlish;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class KhmerlishPredictionTest {
    private KhmerlishDictionary dictionary() throws Exception {
        String words = "maen\tមែន\nman\tមែន\nmean\tមាន\nmenu\tម៉ឺនុយ\n";
        String predictions = "men\tមែន\nmen\tមេន\nman\tម៉ាន\nman\tមែន\n";
        return KhmerlishDictionary.read(
                new ByteArrayInputStream(words.getBytes(StandardCharsets.UTF_8)),
                new ByteArrayInputStream(predictions.getBytes(StandardCharsets.UTF_8)));
    }

    @Test public void curatedExamplesKeepTheirRequestedOrder() throws Exception {
        KhmerlishDictionary dictionary = dictionary();
        assertEquals(List.of("មែន", "មេន", "មាន", "ម៉ឺនុយ"), dictionary.suggest("men", 5));
        assertEquals(List.of("ម៉ាន", "មែន"), dictionary.suggest("man", 5));
    }

    @Test public void personalCandidatesRankBeforeBundledCandidates() throws Exception {
        KhmerlishDictionary dictionary = dictionary();
        Map<String, String> personal = new LinkedHashMap<>();
        personal.put("men", "មិន");
        personal.put("menu", "បញ្ជីផ្ទាល់ខ្លួន");
        dictionary.setPersonal(personal);
        assertEquals(List.of("មិន", "មែន", "មេន", "បញ្ជីផ្ទាល់ខ្លួន"),
                dictionary.suggest("men", 4));
    }

    @Test public void suggestionsAreBoundedDistinctAndOffline() throws Exception {
        KhmerlishDictionary dictionary = dictionary();
        List<String> suggestions = dictionary.suggest("m", 3);
        assertEquals(3, suggestions.size());
        assertEquals(suggestions.size(), suggestions.stream().distinct().count());
        assertTrue(dictionary.suggest("", 5).isEmpty());
        assertTrue(dictionary.suggest("not-found", 5).isEmpty());
    }
}
