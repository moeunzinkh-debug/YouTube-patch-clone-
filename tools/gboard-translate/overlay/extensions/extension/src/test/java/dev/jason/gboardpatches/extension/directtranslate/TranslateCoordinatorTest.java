package dev.jason.gboardpatches.extension.directtranslate;

import org.junit.Test;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.List;
import java.util.concurrent.Executor;
import java.util.concurrent.RejectedExecutionException;

import static org.junit.Assert.*;

public class TranslateCoordinatorTest {
    @Test public void dispatchesBothDirectionsAndDetectionIntoNativeCallback() throws Exception {
        Manual worker = new Manual(), main = new Manual();
        TranslateCoordinator coordinator = new TranslateCoordinator(worker, main, worker::clear,
                (text, source, target) -> new GtxClient.Translation(target.equals("km") ? "សួស្តី" : "hello", "km"));
        Object callback1 = create("kli"), callback2 = create("kli");
        assertTrue(coordinator.tryDispatch(create("kjx"), request("hello", "en", "km"), callback1));
        worker.runOne(); main.runOne();
        assertEquals("សួស្តី", responseField(callback1, "c"));
        assertEquals(0, responseField(callback1, "b"));
        assertTrue(((List<?>) responseField(callback1, "a")).isEmpty());
        assertTrue(coordinator.tryDispatch(create("kjx"), request("សួស្តី", "auto", "en"), callback2));
        worker.runOne(); main.runOne();
        assertEquals("hello", responseField(callback2, "c"));
        assertEquals(List.of("km"), responseField(callback2, "a"));
    }

    @Test public void newerInputAndCloseDiscardQueuedAndCompletedOldResults() throws Exception {
        Manual worker = new Manual(), main = new Manual();
        int[] requests = {0};
        TranslateCoordinator coordinator = new TranslateCoordinator(worker, main, worker::clear,
                (text, source, target) -> { requests[0]++; return new GtxClient.Translation(text, "en"); });
        Object old = create("kli"), current = create("kli");
        assertTrue(coordinator.tryDispatch(create("kjx"), request("old", "en", "km"), old));
        worker.runOne(); // Old HTTP response is waiting on the UI thread.
        coordinator.cancel(); // A native input edit invalidates it immediately.
        assertTrue(coordinator.tryDispatch(create("kjx"), request("new", "en", "km"), current));
        worker.runOne(); main.runAll();
        assertEquals(0, value(old, "calls"));
        assertEquals(1, value(current, "calls"));
        assertEquals("new", responseField(current, "c"));
        assertEquals(2, requests[0]);
        Object closed = create("kli");
        assertTrue(coordinator.tryDispatch(create("kjx"), request("private", "en", "km"), closed));
        coordinator.cancel();
        assertTrue(worker.tasks.isEmpty());
        main.runAll();
        assertEquals(0, value(closed, "calls"));
        assertEquals(2, requests[0]);
    }

    @Test public void errorAndRejectionProduceNativeFailureWithoutText() throws Exception {
        Manual worker = new Manual(), main = new Manual();
        TranslateCoordinator coordinator = new TranslateCoordinator(worker, main, worker::clear,
                (text, source, target) -> { throw new IllegalStateException(text); });
        Object callback = create("kli");
        assertTrue(coordinator.tryDispatch(create("kjx"), request("sensitive", "en", "km"), callback));
        worker.runOne(); main.runAll();
        assertEquals(1, responseField(callback, "b"));
        assertEquals("", responseField(callback, "c"));
        Object rejected = create("kli");
        TranslateCoordinator rejecting = new TranslateCoordinator(task -> { throw new RejectedExecutionException(); },
                main, () -> {}, (text, source, target) -> { throw new AssertionError(); });
        assertTrue(rejecting.tryDispatch(create("kjx"), request("sensitive", "en", "km"), rejected));
        main.runAll();
        assertEquals(1, responseField(rejected, "b"));
    }

    @Test public void leavesHealthChecksAndOtherProvidersOnNativeRoute() throws Exception {
        Manual worker = new Manual(), main = new Manual();
        TranslateCoordinator coordinator = new TranslateCoordinator(worker, main, worker::clear,
                (text, source, target) -> { throw new AssertionError(); });
        assertFalse(coordinator.tryDispatch(create("kjx"), request("test", "en", "km"), new Object()));
        assertFalse(coordinator.tryDispatch(new Object(), request("test", "en", "km"), create("kli")));
        assertTrue(worker.tasks.isEmpty());
    }

    private static Object create(String name) throws Exception {
        return Class.forName(name).getDeclaredConstructor().newInstance();
    }
    private static Object request(String text, String source, String target) throws Exception {
        return Class.forName("klg").getDeclaredConstructor(String.class, String.class, String.class)
                .newInstance(text, source, target);
    }
    private static Object value(Object object, String field) throws Exception {
        return object.getClass().getField(field).get(object);
    }
    private static Object responseField(Object callback, String field) throws Exception {
        return value(value(callback, "response"), field);
    }
    private static final class Manual implements Executor {
        final Deque<Runnable> tasks = new ArrayDeque<>();
        @Override public void execute(Runnable task) { tasks.addLast(task); }
        void clear() { tasks.clear(); }
        void runOne() { tasks.removeFirst().run(); }
        void runAll() { while (!tasks.isEmpty()) runOne(); }
    }
}
