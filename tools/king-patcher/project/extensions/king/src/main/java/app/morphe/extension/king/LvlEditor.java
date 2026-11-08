package app.morphe.extension.king;

import org.jf.dexlib2.DexFileFactory;
import org.jf.dexlib2.Opcode;
import org.jf.dexlib2.Opcodes;
import org.jf.dexlib2.iface.ClassDef;
import org.jf.dexlib2.iface.DexFile;
import org.jf.dexlib2.iface.Method;
import org.jf.dexlib2.iface.instruction.FiveRegisterInstruction;
import org.jf.dexlib2.iface.instruction.Instruction;
import org.jf.dexlib2.iface.instruction.NarrowLiteralInstruction;
import org.jf.dexlib2.iface.instruction.OneRegisterInstruction;
import org.jf.dexlib2.iface.instruction.ReferenceInstruction;
import org.jf.dexlib2.iface.reference.MethodReference;
import org.jf.dexlib2.immutable.ImmutableMethod;
import org.jf.dexlib2.immutable.ImmutableMethodImplementation;
import org.jf.dexlib2.immutable.instruction.ImmutableInstruction10x;
import org.jf.dexlib2.immutable.instruction.ImmutableInstruction21s;
import org.jf.dexlib2.immutable.instruction.ImmutableInstruction35c;
import org.jf.dexlib2.immutable.reference.ImmutableMethodReference;
import org.jf.dexlib2.rewriter.DexRewriter;
import org.jf.dexlib2.rewriter.Rewriter;
import org.jf.dexlib2.rewriter.RewriterModule;
import org.jf.dexlib2.rewriter.Rewriters;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.zip.Adler32;

/**
 * Experimental, exact-pattern Google Play LVL editor. It handles only the
 * unobfuscated classic LicenseChecker/LicenseCheckerCallback API. It does not
 * claim to remove server-side, custom, obfuscated, native, billing or integrity
 * checks. Unsupported or ambiguous inputs fail without a rewritten output.
 */
public final class LvlEditor {
    private static final String CHECKER = "Lcom/android/vending/licensing/LicenseChecker;";
    private static final String CALLBACK = "Lcom/android/vending/licensing/LicenseCheckerCallback;";
    private static final int PUBLIC = 0x1, STATIC = 0x8, NATIVE = 0x100, INTERFACE = 0x200, ABSTRACT = 0x400;
    private static final int LICENSED = 0x100;
    private static final long MAX_DEX_SIZE = 128L * 1024 * 1024;
    private static final int MAX_DEX_COUNT = 32;

    private LvlEditor() {}

    private static int version(File file) throws IOException {
        if (!file.isFile() || file.length() < 8 || file.length() > MAX_DEX_SIZE)
            throw new IOException("Invalid or oversized DEX input");
        byte[] magic = new byte[8];
        try (FileInputStream in = new FileInputStream(file)) {
            int count = 0, read;
            while (count < magic.length && (read = in.read(magic, count, magic.length - count)) > 0) count += read;
            if (count != magic.length) throw new IOException("Truncated DEX header");
        }
        if (magic[0] != 'd' || magic[1] != 'e' || magic[2] != 'x' || magic[3] != '\n' || magic[7] != 0)
            throw new IOException("Not a supported DEX file");
        String version = new String(magic, 4, 3, "US-ASCII");
        if (!Arrays.asList("035", "037", "038", "039").contains(version))
            throw new IOException("Unsupported DEX version " + version);
        return Integer.parseInt(version);
    }
    private static MessageDigest sha1() throws IOException {
        try { return MessageDigest.getInstance("SHA-1"); }
        catch (NoSuchAlgorithmException unavailable) { throw new IOException("DEX SHA-1 is unavailable", unavailable); }
    }
    /**
     * Android requires the DEX SHA-1 signature and Adler-32 checksum in the
     * header. The inspected King's embedded writer can leave both as zero even
     * when dexlib2 itself can reload the file. Seal them independently.
     */
    private static void sealDexHeader(File file) throws IOException {
        try (RandomAccessFile dex = new RandomAccessFile(file, "rw")) {
            if (dex.length() < 112 || dex.length() > MAX_DEX_SIZE) throw new IOException("Invalid rewritten DEX length");
            byte[] buffer = new byte[32768]; int read;
            MessageDigest signature = sha1();
            dex.seek(32);
            while ((read = dex.read(buffer)) != -1) if (read > 0) signature.update(buffer, 0, read);
            dex.seek(12); dex.write(signature.digest());
            Adler32 checksum = new Adler32();
            dex.seek(12);
            while ((read = dex.read(buffer)) != -1) if (read > 0) checksum.update(buffer, 0, read);
            long value = checksum.getValue();
            dex.seek(8);
            for (int i = 0; i < 4; i++) dex.writeByte((int) (value >>> (8 * i)) & 0xff);
            dex.getFD().sync();
        }
    }
    private static void verifyDexHeader(File file) throws IOException {
        try (RandomAccessFile dex = new RandomAccessFile(file, "r")) {
            if (dex.length() < 112 || dex.length() > MAX_DEX_SIZE) throw new IOException("Invalid DEX length");
            byte[] header = new byte[32]; dex.readFully(header);
            long expected = 0;
            for (int i = 0; i < 4; i++) expected |= ((long) header[8 + i] & 0xff) << (8 * i);
            MessageDigest signature = sha1(); Adler32 checksum = new Adler32();
            checksum.update(header, 12, 20);
            byte[] buffer = new byte[32768]; int read;
            while ((read = dex.read(buffer)) != -1) if (read > 0) {
                signature.update(buffer, 0, read); checksum.update(buffer, 0, read);
            }
            if (checksum.getValue() != expected || !Arrays.equals(Arrays.copyOfRange(header, 12, 32), signature.digest()))
                throw new IOException("DEX header checksum or SHA-1 is invalid");
        }
    }
    private static DexFile load(File file) throws IOException {
        int dexVersion = version(file);
        verifyDexHeader(file);
        return DexFileFactory.loadDexFile(file, Opcodes.forDexVersion(dexVersion));
    }
    private static boolean signature(Method method, String name, String parameter) {
        return method.getName().equals(name) && method.getReturnType().equals("V")
                && method.getParameterTypes().size() == 1
                && method.getParameterTypes().get(0).toString().equals(parameter);
    }
    private static boolean checkerMethod(Method method) {
        return method.getDefiningClass().equals(CHECKER) && signature(method, "checkAccess", CALLBACK);
    }
    private static void validateCallback(ClassDef cls) throws IOException {
        if ((cls.getAccessFlags() & INTERFACE) == 0) throw new IOException("LVL callback is not an interface");
        for (String name : Arrays.asList("allow", "dontAllow", "applicationError")) {
            int matches = 0;
            for (Method method : cls.getMethods()) if (signature(method, name, "I")) {
                if ((method.getAccessFlags() & (PUBLIC | ABSTRACT)) != (PUBLIC | ABSTRACT)
                        || (method.getAccessFlags() & STATIC) != 0) throw new IOException("Unexpected LVL callback ABI");
                matches++;
            }
            if (matches != 1) throw new IOException("Incomplete or ambiguous LVL callback ABI");
        }
    }
    private static void validateChecker(ClassDef cls) throws IOException {
        int matches = 0;
        for (Method method : cls.getMethods()) if (checkerMethod(method)) {
            int flags = method.getAccessFlags();
            if ((flags & PUBLIC) == 0 || (flags & (STATIC | NATIVE | ABSTRACT)) != 0 || method.getImplementation() == null)
                throw new IOException("Unexpected LVL checker ABI");
            matches++;
        }
        if (matches != 1) throw new IOException("Incomplete or ambiguous LVL checker ABI");
    }
    private static Method rewrite(Method original) {
        MethodReference allow = new ImmutableMethodReference(CALLBACK, "allow", Collections.singletonList("I"), "V");
        List<Instruction> instructions = Arrays.asList(
                new ImmutableInstruction21s(Opcode.CONST_16, 0, LICENSED),
                new ImmutableInstruction35c(Opcode.INVOKE_INTERFACE, 2, 2, 0, 0, 0, 0, allow),
                new ImmutableInstruction10x(Opcode.RETURN_VOID));
        ImmutableMethodImplementation implementation = new ImmutableMethodImplementation(3, instructions,
                Collections.emptyList(), Collections.emptyList());
        return new ImmutableMethod(original.getDefiningClass(), original.getName(), original.getParameters(),
                original.getReturnType(), original.getAccessFlags(), original.getAnnotations(), implementation);
    }
    private static boolean isPatched(Method method) {
        if (method.getImplementation() == null || method.getImplementation().getRegisterCount() != 3) return false;
        List<Instruction> ops = new ArrayList<>();
        for (Instruction instruction : method.getImplementation().getInstructions()) ops.add(instruction);
        if (ops.size() != 3 || ops.get(0).getOpcode() != Opcode.CONST_16
                || ops.get(1).getOpcode() != Opcode.INVOKE_INTERFACE || ops.get(2).getOpcode() != Opcode.RETURN_VOID)
            return false;
        if (!(ops.get(0) instanceof NarrowLiteralInstruction) || !(ops.get(0) instanceof OneRegisterInstruction)
                || ((NarrowLiteralInstruction) ops.get(0)).getNarrowLiteral() != LICENSED
                || ((OneRegisterInstruction) ops.get(0)).getRegisterA() != 0
                || !(ops.get(1) instanceof FiveRegisterInstruction) || !(ops.get(1) instanceof ReferenceInstruction)) return false;
        FiveRegisterInstruction invoke = (FiveRegisterInstruction) ops.get(1);
        if (invoke.getRegisterCount() != 2 || invoke.getRegisterC() != 2 || invoke.getRegisterD() != 0) return false;
        Object reference = ((ReferenceInstruction) ops.get(1)).getReference();
        if (!(reference instanceof MethodReference)) return false;
        MethodReference ref = (MethodReference) reference;
        return ref.getDefiningClass().equals(CALLBACK) && ref.getName().equals("allow")
                && ref.getReturnType().equals("V") && ref.getParameterTypes().size() == 1
                && ref.getParameterTypes().get(0).toString().equals("I");
    }

    /**
     * Inspect all DEX files, then write only the single affected DEX to a new
     * private temporary path. Returns its zero-based index in dexFiles.
     */
    public static int patch(List<File> dexFiles, File output) throws IOException {
        if (dexFiles == null || dexFiles.isEmpty() || dexFiles.size() > MAX_DEX_COUNT || output == null || output.exists())
            throw new IOException("Invalid inputs or existing output");
        int checkerCount = 0, callbackCount = 0, checkerIndex = -1;
        DexFile checkerDex = null;
        for (int index = 0; index < dexFiles.size(); index++) {
            File file = dexFiles.get(index);
            if (file == null || file.getCanonicalFile().equals(output.getCanonicalFile())) throw new IOException("Output overlaps input");
            DexFile dex = load(file);
            for (ClassDef cls : dex.getClasses()) {
                if (CHECKER.equals(cls.getType())) {
                    checkerCount++; checkerIndex = index; checkerDex = dex; validateChecker(cls);
                    for (Method method : cls.getMethods()) if (checkerMethod(method) && isPatched(method))
                        throw new IOException("LVL checker already has the experimental replacement");
                } else if (CALLBACK.equals(cls.getType())) { callbackCount++; validateCallback(cls); }
            }
        }
        if (checkerCount != 1 || callbackCount != 1 || checkerDex == null)
            throw new IOException("Only one unobfuscated classic Google Play LVL checker is supported");
        final RewriterModule module = new RewriterModule() {
            @Override public Rewriter<Method> getMethodRewriter(Rewriters rewriters) {
                final Rewriter<Method> original = super.getMethodRewriter(rewriters);
                return new Rewriter<Method>() {
                    @Override public Method rewrite(Method method) {
                        return checkerMethod(method) ? LvlEditor.rewrite(method) : original.rewrite(method);
                    }
                };
            }
        };
        if (!output.createNewFile()) throw new IOException("Cannot reserve new DEX output");
        boolean success = false;
        try {
            DexFile rewritten = new DexRewriter(module).rewriteDexFile(checkerDex);
            DexFileFactory.writeDexFile(output.getAbsolutePath(), rewritten);
            sealDexHeader(output);
            DexFile verified = load(output);
            int verifiedClasses = 0, verifiedMethods = 0;
            for (ClassDef cls : verified.getClasses()) if (CHECKER.equals(cls.getType())) {
                verifiedClasses++;
                for (Method method : cls.getMethods()) if (checkerMethod(method) && isPatched(method)) verifiedMethods++;
            }
            if (verifiedClasses != 1 || verifiedMethods != 1) throw new IOException("Rewritten LVL DEX failed verification");
            success = true;
            return checkerIndex;
        } finally {
            if (!success) output.delete();
        }
    }
}
