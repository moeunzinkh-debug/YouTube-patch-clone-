package app.morphe.extension.king;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.FilterOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.zip.CRC32;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;
import java.util.zip.ZipOutputStream;

/** Bounded, opt-in APK archive transforms. All outputs are new and unsigned. */
public final class ApkArchive {
    private static final long MAX_ARCHIVE = 512L * 1024 * 1024;
    private static final long MAX_EXPANDED = 1024L * 1024 * 1024;
    private static final long MAX_ENTRY = 256L * 1024 * 1024;
    private static final int MAX_ENTRIES = 50000, MAX_XML = 4 * 1024 * 1024;
    private static final long MAX_XML_SCAN = 64L * 1024 * 1024;
    private static final int MAX_NODES = 5000;
    private static final long SAFE_ZIP_TIME = 315619200000L; // 1980-01-02, avoiding extended timestamps

    private ApkArchive() {}

    public static final class Layout {
        public final String path;
        public final List<AxmlEditor.Node> nodes;
        Layout(String path, List<AxmlEditor.Node> nodes) { this.path = path; this.nodes = nodes; }
    }
    public static final class Layouts {
        public final List<Layout> layouts;
        public final boolean truncated;
        Layouts(List<Layout> layouts, boolean truncated) { this.layouts = layouts; this.truncated = truncated; }
    }
    private static final class Source {
        final byte[] bytes;
        final File file;
        Source(byte[] bytes) { this.bytes = bytes; this.file = null; }
        Source(File file) { this.bytes = null; this.file = file; }
        long length() { return bytes != null ? bytes.length : file.length(); }
        InputStream open() throws IOException {
            return bytes != null ? new java.io.ByteArrayInputStream(bytes) : new BufferedInputStream(new FileInputStream(file));
        }
    }
    private static final class CountingOutput extends FilterOutputStream {
        long count;
        CountingOutput(OutputStream out) { super(out); }
        @Override public void write(int b) throws IOException { out.write(b); count++; }
        @Override public void write(byte[] b, int start, int length) throws IOException { out.write(b, start, length); count += length; }
    }

    private static boolean dexName(String name) { return name.matches("classes(?:[2-9]|[1-9][0-9]+)?\\.dex"); }
    private static boolean signature(String name) {
        String upper = name.toUpperCase(Locale.ROOT);
        if (!upper.startsWith("META-INF/") || upper.indexOf('/', 9) >= 0) return false;
        String leaf = upper.substring(9);
        return leaf.equals("MANIFEST.MF") || leaf.endsWith(".SF") || leaf.endsWith(".RSA")
                || leaf.endsWith(".DSA") || leaf.endsWith(".EC") || leaf.startsWith("SIG-");
    }
    private static void safeName(String name) throws IOException {
        if (name == null || name.isEmpty() || name.length() > 1024 || name.startsWith("/") || name.indexOf('\\') >= 0
                || name.indexOf('\0') >= 0) throw new IOException("Unsafe ZIP entry name");
        for (String part : name.split("/", -1)) if (part.equals(".") || part.equals(".."))
            throw new IOException("Unsafe ZIP entry path");
    }
    private static List<ZipEntry> validate(File apk, ZipFile zip) throws IOException {
        if (apk == null || !apk.isFile() || apk.length() <= 0 || apk.length() > MAX_ARCHIVE)
            throw new IOException("APK missing or too large");
        List<ZipEntry> entries = new ArrayList<>();
        Set<String> names = new HashSet<>(); long expanded = 0;
        for (java.util.Enumeration<? extends ZipEntry> it = zip.entries(); it.hasMoreElements();) {
            ZipEntry entry = it.nextElement(); safeName(entry.getName());
            if (!names.add(entry.getName()) || entries.size() >= MAX_ENTRIES) throw new IOException("Duplicate or too many ZIP entries");
            if (!entry.isDirectory()) {
                long size = entry.getSize();
                if (size < 0 || size > MAX_ENTRY || entry.getCrc() < 0
                        || (entry.getMethod() != ZipEntry.STORED && entry.getMethod() != ZipEntry.DEFLATED))
                    throw new IOException("Unsupported or oversized ZIP entry");
                expanded += size;
                if (expanded > MAX_EXPANDED) throw new IOException("Expanded APK exceeds limit");
            }
            entries.add(entry);
        }
        if (!names.contains("AndroidManifest.xml") || !names.contains("classes.dex"))
            throw new IOException("Single base APK manifest or primary DEX missing");
        try {
            if (AxmlEditor.isSplitManifest(read(zip, zip.getEntry("AndroidManifest.xml"), MAX_XML)))
                throw new IOException("Split APKs are not supported; choose a complete single APK");
        } catch (IllegalArgumentException invalid) { throw new IOException("Unsupported APK manifest", invalid); }
        return entries;
    }
    private static byte[] read(ZipFile zip, ZipEntry entry, int limit) throws IOException {
        if (entry.getSize() > limit) throw new IOException("ZIP entry exceeds read limit");
        ByteArrayOutputStream out = new ByteArrayOutputStream((int) Math.max(0, entry.getSize()));
        copyChecked(zip.getInputStream(entry), out, entry.getSize(), entry.getCrc());
        return out.toByteArray();
    }
    private static void copyChecked(InputStream source, OutputStream destination, long expectedSize, long expectedCrc) throws IOException {
        CRC32 crc = new CRC32(); byte[] buffer = new byte[32768]; long count = 0;
        try (InputStream input = source) {
            int n;
            while ((n = input.read(buffer)) != -1) {
                if (n == 0) continue;
                count += n;
                if (count > expectedSize) throw new IOException("ZIP entry expands beyond declared size");
                crc.update(buffer, 0, n); destination.write(buffer, 0, n);
            }
        }
        if (count != expectedSize || (expectedCrc >= 0 && crc.getValue() != expectedCrc))
            throw new IOException("ZIP entry size or CRC mismatch");
    }
    private static boolean looksLikeLayout(List<AxmlEditor.Node> nodes) {
        if (nodes.isEmpty()) return false;
        String root = nodes.get(0).tag;
        return root.equals("merge") || root.equals("fragment") || root.equals("view") || root.equals("View")
                || root.endsWith("Layout") || root.endsWith("View") || root.endsWith("Button")
                || root.endsWith("ScrollView") || root.startsWith("androidx.");
    }
    public static Layouts listLayouts(File apk) throws IOException {
        List<Layout> result = new ArrayList<>(); boolean truncated = false; long scanned = 0; int nodes = 0;
        try (ZipFile zip = new ZipFile(apk)) {
            List<ZipEntry> entries = validate(apk, zip);
            Collections.sort(entries, (left, right) -> left.getName().compareTo(right.getName()));
            for (ZipEntry entry : entries) {
                String name = entry.getName();
                if (entry.isDirectory() || !name.startsWith("res/") || !name.endsWith(".xml")) continue;
                if (entry.getSize() > MAX_XML) { truncated = true; continue; }
                if (scanned + entry.getSize() > MAX_XML_SCAN || nodes >= MAX_NODES) { truncated = true; break; }
                scanned += entry.getSize();
                byte[] data = read(zip, entry, MAX_XML);
                try {
                    List<AxmlEditor.Node> found = AxmlEditor.list(data);
                    if (!looksLikeLayout(found)) continue;
                    if (nodes + found.size() > MAX_NODES) { truncated = true; break; }
                    nodes += found.size(); result.add(new Layout(name, found));
                } catch (IllegalArgumentException unsupported) {
                    // Other resources may not be binary layout XML. Never guess how to edit them.
                }
            }
        }
        return new Layouts(Collections.unmodifiableList(result), truncated);
    }
    public static void buildUi(File input, File unsignedOutput, Map<String, Set<Integer>> selection) throws IOException {
        if (selection == null || selection.isEmpty()) throw new IOException("No UI elements selected");
        Map<String, Source> replacements = new LinkedHashMap<>();
        try (ZipFile zip = new ZipFile(input)) {
            validate(input, zip);
            for (Map.Entry<String, Set<Integer>> selected : selection.entrySet()) {
                String path = selected.getKey(); safeName(path);
                if (!path.startsWith("res/") || !path.endsWith(".xml") || selected.getValue() == null || selected.getValue().isEmpty())
                    throw new IOException("Invalid UI selection");
                ZipEntry entry = zip.getEntry(path);
                if (entry == null || entry.isDirectory()) throw new IOException("Selected layout no longer exists");
                byte[] before = read(zip, entry, MAX_XML);
                try {
                    if (!looksLikeLayout(AxmlEditor.list(before))) throw new IOException("Selected XML is not a supported layout");
                    replacements.put(path, new Source(AxmlEditor.hide(before, selected.getValue())));
                } catch (IllegalArgumentException e) { throw new IOException("Selected binary layout is unsupported", e); }
            }
        }
        rewrite(input, unsignedOutput, replacements);
    }
    /** Extracts only DEX entries into an empty private directory, never into the APK's paths. */
    public static String buildLvl(File input, File workDirectory, File unsignedOutput) throws IOException {
        if (workDirectory == null || !workDirectory.isDirectory() || workDirectory.list() == null || workDirectory.list().length != 0)
            throw new IOException("A new empty private working directory is required");
        if (unsignedOutput == null || unsignedOutput.getCanonicalPath().startsWith(workDirectory.getCanonicalPath() + File.separator))
            throw new IOException("Output must be outside the private working directory");
        List<File> files = new ArrayList<>(); List<String> names = new ArrayList<>();
        try {
            try (ZipFile zip = new ZipFile(input)) {
                List<ZipEntry> entries = validate(input, zip);
                for (ZipEntry entry : entries) if (!entry.isDirectory() && dexName(entry.getName())) names.add(entry.getName());
                Collections.sort(names, (a, b) -> Integer.compare(dexIndex(a), dexIndex(b)));
                if (names.isEmpty() || names.size() > 32 || !names.get(0).equals("classes.dex")) throw new IOException("Unsupported multi-DEX archive");
                for (int i = 0; i < names.size(); i++) {
                    if (dexIndex(names.get(i)) != i + 1) throw new IOException("Non-contiguous or invalid DEX numbering");
                    ZipEntry entry = zip.getEntry(names.get(i));
                    File target = new File(workDirectory, "input-" + i + ".dex");
                    if (!target.createNewFile()) throw new IOException("DEX temporary path already exists");
                    try (OutputStream out = new BufferedOutputStream(new FileOutputStream(target))) {
                        copyChecked(zip.getInputStream(entry), out, entry.getSize(), entry.getCrc());
                    }
                    files.add(target);
                }
            }
            // Inspect both supported families, including when they live in the
            // same DEX. Unknown, incomplete or already modified implementations
            // never count as a successful removal.
            Map<String, Source> replacements = new LinkedHashMap<>();
            boolean classic = false, pairip = false;
            File classicOutput = new File(workDirectory, "classic-modified.dex");
            try {
                int index = LvlEditor.patch(files, classicOutput);
                files.set(index, classicOutput);
                replacements.put(names.get(index), new Source(classicOutput));
                classic = true;
            } catch (LvlEditor.ClassicNotFoundException absent) { /* Try PairIP too. */ }
            File pairOutput = new File(workDirectory, "pairip-modified.dex");
            try {
                int index = PairIpEditor.patch(files, pairOutput);
                replacements.put(names.get(index), new Source(pairOutput));
                pairip = true;
            } catch (PairIpEditor.PairIpNotFoundException absent) { /* Not a supported PairIP APK. */ }
            if (!classic && !pairip)
                throw new IOException("No supported classic LVL or reviewed PairIP license check was found. This APK may use a different, obfuscated, native, or server-side check.");
            rewrite(input, unsignedOutput, replacements);
            return classic && pairip ? "classic LVL and reviewed PairIP" : classic ? "classic LVL" : "reviewed PairIP";
        } finally {
            File[] children = workDirectory.listFiles();
            if (children != null) for (File child : children) if (child.isFile()) child.delete();
        }
    }
    private static int dexIndex(String name) {
        if (name.equals("classes.dex")) return 1;
        try { return Integer.parseInt(name.substring(7, name.length() - 4)); }
        catch (RuntimeException invalid) { return Integer.MAX_VALUE; }
    }
    private static long crc(Source source) throws IOException {
        CRC32 crc = new CRC32(); byte[] buffer = new byte[32768];
        try (InputStream in = source.open()) { int n; while ((n = in.read(buffer)) != -1) if (n > 0) crc.update(buffer, 0, n); }
        return crc.getValue();
    }
    private static byte[] padding(long offset, int nameBytes, int alignment) {
        int pad = (int) ((alignment - ((offset + 30L + nameBytes) % alignment)) % alignment);
        if (pad > 0 && pad < 4) pad += alignment;
        if (pad == 0) return null;
        byte[] extra = new byte[pad]; extra[0] = 0x35; extra[1] = (byte) 0xd9;
        int payload = pad - 4; extra[2] = (byte) payload; extra[3] = (byte) (payload >>> 8);
        return extra;
    }
    private static void rewrite(File input, File output, Map<String, Source> replacements) throws IOException {
        if (input == null || output == null || output.exists() || input.getCanonicalFile().equals(output.getCanonicalFile()))
            throw new IOException("Output must be a new file distinct from the input");
        if (!output.createNewFile()) throw new IOException("Cannot reserve output");
        boolean success = false;
        try (ZipFile zip = new ZipFile(input)) {
            List<ZipEntry> entries = validate(input, zip);
            Set<String> used = new HashSet<>();
            try (CountingOutput counting = new CountingOutput(new BufferedOutputStream(new FileOutputStream(output)));
                 ZipOutputStream out = new ZipOutputStream(counting)) {
                for (ZipEntry original : entries) {
                    String name = original.getName();
                    if (signature(name)) continue;
                    Source replacement = replacements.get(name);
                    if (replacement != null) used.add(name);
                    ZipEntry target = new ZipEntry(name); target.setTime(SAFE_ZIP_TIME); target.setMethod(original.getMethod());
                    long expectedSize = original.isDirectory() ? 0 : replacement == null ? original.getSize() : replacement.length();
                    long expectedCrc = original.isDirectory() ? 0 : replacement == null ? original.getCrc() : crc(replacement);
                    if (original.getMethod() == ZipEntry.STORED) {
                        target.setSize(expectedSize); target.setCompressedSize(expectedSize); target.setCrc(expectedCrc);
                        int alignment = name.startsWith("lib/") && name.endsWith(".so") ? 16384 : 4;
                        byte[] extra = padding(counting.count, name.getBytes(StandardCharsets.UTF_8).length, alignment);
                        if (extra != null) target.setExtra(extra);
                    }
                    out.putNextEntry(target);
                    if (!original.isDirectory()) {
                        if (original.getMethod() == ZipEntry.STORED) {
                            int alignment = name.startsWith("lib/") && name.endsWith(".so") ? 16384 : 4;
                            if (counting.count % alignment != 0) throw new IOException("ZIP entry alignment failed");
                        }
                        InputStream source = replacement == null ? zip.getInputStream(original) : replacement.open();
                        copyChecked(source, out, expectedSize, expectedCrc);
                    }
                    out.closeEntry();
                }
                if (!used.equals(replacements.keySet())) throw new IOException("A selected APK entry disappeared");
            }
            success = true;
        } finally {
            if (!success) output.delete();
        }
    }
}
