package app.morphe.extension.instanttranslate;

import org.junit.Test;

import java.lang.reflect.Constructor;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.Executor;
import java.util.concurrent.RejectedExecutionException;

import static org.junit.Assert.*;

public class FallbackCoordinatorTest {
    private static final class Queue implements Executor {
        final ArrayDeque<Runnable> tasks = new ArrayDeque<>();
        @Override public void execute(Runnable task) { tasks.add(task); }
        void run() { tasks.remove().run(); }
    }
    public static final class Continuation {
        Object value;
        int calls;
        public void resumeWith(Object result) { value = result; calls++; }
    }

    @Test public void waitsForOriginalFailureAndResumesOnceWithoutRepeating() {
        Queue queue = new Queue();
        List<String> requests = new ArrayList<>();
        FallbackCoordinator coordinator = new FallbackCoordinator((text, source, target) -> {
            requests.add(text + "/" + source + "/" + target);
            return "សួស្តី";
        }, queue);
        Object token = new Object();
        Continuation cont = new Continuation();
        assertFalse(coordinator.trySingle("existing", "hello", "en", "km", token, cont));
        assertTrue(coordinator.trySingle(null, "hello", "en", "km", token, cont));
        assertEquals(0, cont.calls);
        queue.run();
        assertEquals("សួស្តី", cont.value);
        assertEquals(1, cont.calls);
        assertEquals(Collections.singletonList("hello/en/km"), requests);
        // If a returned fallback were still blank, the coroutine's next visit
        // consumes its marker rather than scheduling an endless retry.
        assertFalse(coordinator.trySingle("", "hello", "en", "km", token, cont));
        assertTrue(queue.tasks.isEmpty());
    }

    @Test public void preservesOriginalFailureAndRejectsUnsafeInputs() {
        Queue queue = new Queue();
        FallbackCoordinator coordinator = new FallbackCoordinator((text, source, target) -> {
            throw new java.io.IOException("no network");
        }, queue);
        Object token = new Object();
        Continuation cont = new Continuation();
        assertFalse(coordinator.trySingle(null, "", "en", "km", token, cont));
        assertFalse(coordinator.trySingle(null, "x", "en", "bad&language", token, cont));
        assertFalse(coordinator.trySingle(null, "x", "en", "auto", token, cont));
        assertFalse(coordinator.trySingle(null, "x", "en", "km", token, new Object()));
        assertTrue(coordinator.trySingle(null, "x", "en", "km", token, cont));
        queue.run();
        assertEquals(1, cont.calls);
        assertNull(cont.value); // Preserve the native null failure.
        assertFalse(coordinator.trySingle(null, "x", "en", "km", token, cont));
    }

    @Test public void rejectedWorkLeavesOriginalPathAvailable() {
        Executor rejected = task -> { throw new RejectedExecutionException(); };
        FallbackCoordinator coordinator = new FallbackCoordinator((text, source, target) -> "unused", rejected);
        assertFalse(coordinator.trySingle(null, "hello", "en", "km", new Object(), new Continuation()));
    }

    @Test public void onlyRetriesFailedBatchItemsAndKeepsSuccessfulObjects() throws Exception {
        Queue queue = new Queue();
        List<String> requests = new ArrayList<>();
        FallbackCoordinator coordinator = new FallbackCoordinator((text, source, target) -> {
            requests.add(text + "/" + source + "/" + target);
            return "replacement";
        }, queue);
        Class<?> kind = Class.forName("a29");
        Object enumValue = kind.getField("b").get(null);
        Constructor<?> ctor = Class.forName("h19").getConstructor(String.class, String.class, Throwable.class, kind, boolean.class);
        Object good = ctor.newInstance("first", "valid", null, enumValue, false);
        Object bad = ctor.newInstance("second", null, new Exception("failure"), enumValue, false);
        Object req = Class.forName("eh7").getConstructor(String.class, String.class, List.class)
                .newInstance("en", "km", Arrays.asList("first", "second"));
        Object token = new Object();
        Continuation cont = new Continuation();
        assertTrue(coordinator.tryBatch(req, Arrays.asList(good, bad), token, cont));
        assertEquals(0, cont.calls);
        queue.run();
        assertEquals(1, cont.calls);
        List<?> output = (List<?>) cont.value;
        assertSame(good, output.get(0));
        assertEquals("replacement", output.get(1).getClass().getField("b").get(output.get(1)));
        assertNull(output.get(1).getClass().getField("c").get(output.get(1)));
        assertEquals(Collections.singletonList("second/en/km"), requests);
        assertFalse(coordinator.tryBatch(req, Arrays.asList(good, bad), token, cont));
    }

    @Test public void emptyOrMismatchedBatchUsesNativeRetry() throws Exception {
        Queue queue = new Queue();
        FallbackCoordinator coordinator = new FallbackCoordinator((text, source, target) -> "unused", queue);
        Object req = Class.forName("eh7").getConstructor(String.class, String.class, List.class)
                .newInstance("en", "km", Arrays.asList("first", "second"));
        assertFalse(coordinator.tryBatch(req, Collections.emptyList(), new Object(), new Continuation()));
        assertFalse(coordinator.tryBatch(req, Collections.singletonList(new Object()), new Object(), new Continuation()));
        assertTrue(queue.tasks.isEmpty());
    }
}
