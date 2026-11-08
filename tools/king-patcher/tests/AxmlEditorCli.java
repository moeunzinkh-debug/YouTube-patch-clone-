import app.morphe.extension.king.AxmlEditor;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

/** Test-only entry point; not part of the Android extension. */
public final class AxmlEditorCli {
    public static void main(String[] args) throws Exception {
        if (args.length < 2) throw new IllegalArgumentException("list <xml> | hide <input> <output> <ordinals...>");
        byte[] input = Files.readAllBytes(Paths.get(args[1]));
        if ("list".equals(args[0]) && args.length == 2) {
            for (AxmlEditor.Node node : AxmlEditor.list(input))
                System.out.println(node.ordinal + " " + node.depth + " " + node.tag + " " + node.text);
        } else if ("hide".equals(args[0]) && args.length >= 4) {
            Set<Integer> selected = new HashSet<>();
            for (int i = 3; i < args.length; i++) selected.add(Integer.parseInt(args[i]));
            Files.write(Paths.get(args[2]), AxmlEditor.hide(input, selected));
        } else throw new IllegalArgumentException("Invalid arguments: " + Arrays.toString(args));
    }
}
