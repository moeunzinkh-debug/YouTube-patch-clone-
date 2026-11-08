package app.morphe.extension.king;

import org.jf.dexlib2.DexFileFactory;
import org.jf.dexlib2.Opcode;
import org.jf.dexlib2.iface.ClassDef;
import org.jf.dexlib2.iface.DexFile;
import org.jf.dexlib2.iface.Method;
import org.jf.dexlib2.iface.instruction.Instruction;
import org.jf.dexlib2.iface.instruction.ReferenceInstruction;
import org.jf.dexlib2.iface.reference.MethodReference;
import org.jf.dexlib2.immutable.ImmutableMethod;
import org.jf.dexlib2.immutable.ImmutableMethodImplementation;
import org.jf.dexlib2.immutable.instruction.ImmutableInstruction10x;
import org.jf.dexlib2.rewriter.DexRewriter;
import org.jf.dexlib2.rewriter.Rewriter;
import org.jf.dexlib2.rewriter.RewriterModule;
import org.jf.dexlib2.rewriter.Rewriters;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Narrow PairIP client-side pattern, based on the reviewed Kimi 3.1.5 build.
 * This is not an entitlement, native protection, billing, server or integrity
 * patch. Never guess when the entry points differ or are already modified.
 */
public final class PairIpEditor {
    private static final String APPLICATION = "Lcom/pairip/application/Application;";
    private static final String CLIENT = "Lcom/pairip/licensecheck/LicenseClient;";
    private static final String RESPONSE = "Lcom/pairip/licensecheck/LicenseResponseHelper;";
    private static final String CONTEXT = "Landroid/content/Context;";
    private static final int PUBLIC = 0x1, STATIC = 0x8, NATIVE = 0x100, ABSTRACT = 0x400;
    private static final int MAX_DEX_COUNT = 32;

    private PairIpEditor() {}

    /** Neither of the reviewed PairIP classes was present in the input. */
    public static final class PairIpNotFoundException extends IOException {
        PairIpNotFoundException() { super("No reviewed PairIP entry point was found"); }
    }

    private static boolean methodSignature(Method m, String owner, String name, String parameter) {
        return m.getDefiningClass().equals(owner) && m.getName().equals(name) && m.getReturnType().equals("V")
                && m.getParameterTypes().size() == (parameter == null ? 0 : 1)
                && (parameter == null || m.getParameterTypes().get(0).toString().equals(parameter));
    }
    private static boolean check(Method m) { return methodSignature(m, CLIENT, "checkLicense", CONTEXT); }
    private static boolean initialize(Method m) { return methodSignature(m, CLIENT, "initializeLicenseCheck", null); }
    private static boolean attach(Method m) { return methodSignature(m, APPLICATION, "attachBaseContext", CONTEXT); }
    private static boolean references(List<Instruction> instructions, String owner, String name, String returnType, String parameter) {
        for (Instruction instruction : instructions) {
            if (!(instruction instanceof ReferenceInstruction)) continue;
            Object reference = ((ReferenceInstruction) instruction).getReference();
            if (!(reference instanceof MethodReference)) continue;
            MethodReference ref = (MethodReference) reference;
            if (ref.getDefiningClass().equals(owner) && ref.getName().equals(name)
                    && (returnType == null || ref.getReturnType().equals(returnType))
                    && (parameter == null || (ref.getParameterTypes().size() == 1
                        && ref.getParameterTypes().get(0).toString().equals(parameter)))) return true;
        }
        return false;
    }
    private static List<Instruction> instructions(Method method) throws IOException {
        if (method.getImplementation() == null) throw new IOException("PairIP method has no bytecode");
        List<Instruction> result = new ArrayList<>();
        for (Instruction instruction : method.getImplementation().getInstructions()) result.add(instruction);
        return result;
    }
    private static void validateApplication(ClassDef cls) throws IOException {
        int count = 0;
        for (Method method : cls.getMethods()) if (attach(method)) {
            count++;
            if ((method.getAccessFlags() & STATIC) != 0 || !references(instructions(method), CLIENT, "checkLicense", "V", CONTEXT))
                throw new IOException("PairIP Application entry point differs from the reviewed method");
        }
        if (count != 1) throw new IOException("PairIP Application entry point is missing or ambiguous");
    }
    private static void validateClient(ClassDef cls) throws IOException {
        int checks = 0, initializers = 0;
        for (Method method : cls.getMethods()) {
            if (check(method)) {
                checks++;
                int flags = method.getAccessFlags();
                List<Instruction> ops = instructions(method);
                if ((flags & (PUBLIC | STATIC)) != (PUBLIC | STATIC) || (flags & (NATIVE | ABSTRACT)) != 0
                        || method.getImplementation().getRegisterCount() != 3 || ops.size() != 16
                        || ops.get(0).getOpcode() != Opcode.CONST_STRING
                        || !references(ops, CLIENT, "isIsolatedProcess", "Z", null))
                    throw new IOException("PairIP checkLicense differs from the reviewed Kimi method or is already patched");
            } else if (initialize(method)) {
                initializers++;
                int flags = method.getAccessFlags();
                List<Instruction> ops = instructions(method);
                if ((flags & PUBLIC) == 0 || (flags & (STATIC | NATIVE | ABSTRACT)) != 0
                        || method.getImplementation().getRegisterCount() != 4 || ops.size() != 29
                        || ops.get(0).getOpcode() != Opcode.SGET_OBJECT
                        || !references(ops, RESPONSE, "validateResponse", null, null)
                        || !references(ops, CLIENT, "initiateFreshLicensingServiceConnection", null, null))
                    throw new IOException("PairIP initializeLicenseCheck differs from the reviewed Kimi method or is already patched");
            }
        }
        if (checks != 1 || initializers != 1) throw new IOException("PairIP methods are missing or ambiguous");
    }
    private static Method rewrite(Method method) {
        // One register is required for either the Context argument or the receiver.
        ImmutableMethodImplementation code = new ImmutableMethodImplementation(1,
                Collections.singletonList(new ImmutableInstruction10x(Opcode.RETURN_VOID)),
                Collections.emptyList(), Collections.emptyList());
        return new ImmutableMethod(method.getDefiningClass(), method.getName(), method.getParameters(),
                method.getReturnType(), method.getAccessFlags(), method.getAnnotations(), code);
    }
    private static boolean isReturnOnly(Method method) {
        if (method.getImplementation() == null || method.getImplementation().getRegisterCount() != 1) return false;
        java.util.Iterator<? extends Instruction> it = method.getImplementation().getInstructions().iterator();
        return it.hasNext() && it.next().getOpcode() == Opcode.RETURN_VOID && !it.hasNext();
    }

    /** Writes only the affected DEX to a new private file and returns its index. */
    public static int patch(List<File> files, File output) throws IOException {
        if (files == null || files.isEmpty() || files.size() > MAX_DEX_COUNT || output == null || output.exists())
            throw new IOException("Invalid PairIP inputs or existing output");
        int applications = 0, clients = 0, clientIndex = -1;
        DexFile clientDex = null;
        for (int i = 0; i < files.size(); i++) {
            File input = files.get(i);
            if (input == null || input.getCanonicalFile().equals(output.getCanonicalFile()))
                throw new IOException("PairIP output overlaps input");
            DexFile dex = LvlEditor.load(input);
            for (ClassDef cls : dex.getClasses()) {
                if (APPLICATION.equals(cls.getType())) { applications++; validateApplication(cls); }
                if (CLIENT.equals(cls.getType())) { clients++; clientIndex = i; clientDex = dex; validateClient(cls); }
            }
        }
        if (applications == 0 && clients == 0) throw new PairIpNotFoundException();
        if (applications != 1 || clients != 1 || clientDex == null)
            throw new IOException("PairIP classes are incomplete or duplicated; no changes made");
        final RewriterModule module = new RewriterModule() {
            @Override public Rewriter<Method> getMethodRewriter(Rewriters rewriters) {
                final Rewriter<Method> original = super.getMethodRewriter(rewriters);
                return new Rewriter<Method>() {
                    @Override public Method rewrite(Method method) {
                        return check(method) || initialize(method) ? PairIpEditor.rewrite(method) : original.rewrite(method);
                    }
                };
            }
        };
        if (!output.createNewFile()) throw new IOException("Cannot reserve PairIP DEX output");
        boolean success = false;
        try {
            DexFileFactory.writeDexFile(output.getAbsolutePath(), new DexRewriter(module).rewriteDexFile(clientDex));
            LvlEditor.sealDexHeader(output);
            DexFile verified = LvlEditor.load(output);
            int classes = 0, checks = 0, initializers = 0;
            for (ClassDef cls : verified.getClasses()) if (CLIENT.equals(cls.getType())) {
                classes++;
                for (Method method : cls.getMethods()) {
                    if (check(method) && isReturnOnly(method)) checks++;
                    if (initialize(method) && isReturnOnly(method)) initializers++;
                }
            }
            if (classes != 1 || checks != 1 || initializers != 1) throw new IOException("Rewritten PairIP DEX failed verification");
            success = true;
            return clientIndex;
        } finally {
            if (!success) output.delete();
        }
    }
}
