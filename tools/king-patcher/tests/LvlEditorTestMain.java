import app.morphe.extension.king.LvlEditor;
import org.jf.dexlib2.DexFileFactory;
import org.jf.dexlib2.Opcode;
import org.jf.dexlib2.Opcodes;
import org.jf.dexlib2.iface.ClassDef;
import org.jf.dexlib2.iface.DexFile;
import org.jf.dexlib2.iface.Method;
import org.jf.dexlib2.iface.instruction.Instruction;
import org.jf.dexlib2.iface.instruction.NarrowLiteralInstruction;
import org.jf.dexlib2.iface.instruction.ReferenceInstruction;
import org.jf.dexlib2.iface.reference.MethodReference;
import org.jf.dexlib2.immutable.ImmutableClassDef;
import org.jf.dexlib2.immutable.ImmutableDexFile;
import org.jf.dexlib2.immutable.ImmutableMethod;
import org.jf.dexlib2.immutable.ImmutableMethodImplementation;
import org.jf.dexlib2.immutable.ImmutableMethodParameter;
import org.jf.dexlib2.immutable.instruction.ImmutableInstruction10x;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

/** Creates synthetic DEX files; never reads or publishes a user's app. */
public final class LvlEditorTestMain {
    private static final String CHECKER="Lcom/android/vending/licensing/LicenseChecker;";
    private static final String CALLBACK="Lcom/android/vending/licensing/LicenseCheckerCallback;";
    private static int checks;
    private static void check(boolean ok,String message) { checks++; if(!ok)throw new AssertionError(message); }
    private static ImmutableMethod method(String owner,String name,String parameter,int flags,boolean hasCode) {
        List<ImmutableMethodParameter> params=Collections.singletonList(new ImmutableMethodParameter(parameter,Collections.emptySet(),"p"));
        ImmutableMethodImplementation code=hasCode ? new ImmutableMethodImplementation(2,
                Collections.singletonList(new ImmutableInstruction10x(Opcode.RETURN_VOID)),Collections.emptyList(),Collections.emptyList()) : null;
        return new ImmutableMethod(owner,name,params,"V",flags,Collections.emptySet(),code);
    }
    private static ClassDef callback(boolean full) {
        List<Method> methods=new ArrayList<>();
        methods.add(method(CALLBACK,"allow","I",0x401,false));
        methods.add(method(CALLBACK,"dontAllow","I",0x401,false));
        if(full)methods.add(method(CALLBACK,"applicationError","I",0x401,false));
        return new ImmutableClassDef(CALLBACK,0x601,"Ljava/lang/Object;",Collections.emptyList(),null,
                Collections.emptySet(),Collections.emptyList(),methods);
    }
    private static ClassDef checker(String name,int flags) {
        List<Method> methods=new ArrayList<>();
        methods.add(method(name,"checkAccess",CALLBACK,flags,true));
        methods.add(method(name,"unchanged","I",0x1,true));
        return new ImmutableClassDef(name,0x1,"Ljava/lang/Object;",Collections.emptyList(),null,
                Collections.emptySet(),Collections.emptyList(),methods);
    }
    private static void makeDex(Path path,List<? extends ClassDef> classes) throws Exception {
        DexFileFactory.writeDexFile(path.toString(),new ImmutableDexFile(Opcodes.forDexVersion(35),classes));
    }
    private static byte[] sha(Path p) throws Exception { return MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(p)); }
    private static void rejects(List<File> inputs,Path output,String reason) throws Exception {
        try { LvlEditor.patch(inputs,output.toFile()); throw new AssertionError("Should reject "+reason); }
        catch (IOException expected) { checks++; check(!Files.exists(output),"no output on "+reason); }
    }
    public static void main(String[] args) throws Exception {
        Path temp=Files.createTempDirectory("lvl-fixture-");
        try {
            Path input=temp.resolve("classes.dex"), out=temp.resolve("out.dex");
            makeDex(input,Arrays.asList(checker(CHECKER,1),callback(true)));
            byte[] digest=sha(input);
            DexFile inputDex=DexFileFactory.loadDexFile(input.toFile(),Opcodes.forDexVersion(35));
            for(ClassDef cls:inputDex.getClasses()) for(Method method:cls.getMethods()) if(method.getImplementation()!=null) {
                try { for(org.jf.dexlib2.iface.debug.DebugItem ignored:method.getImplementation().getDebugItems()) {} }
                catch(RuntimeException error) { throw new AssertionError("Invalid fixture debug info: "+cls.getType()+"->"+method.getName()+" registers="+method.getImplementation().getRegisterCount(),error); }
            }
            check(LvlEditor.patch(Collections.singletonList(input.toFile()),out.toFile())==0,"checker index");
            check(Arrays.equals(digest,sha(input)),"original input unchanged");
            DexFile after=DexFileFactory.loadDexFile(out.toFile(),Opcodes.forDexVersion(35));
            int seen=0, other=0;
            for(ClassDef cls:after.getClasses()) for(Method method:cls.getMethods()) {
                if(CHECKER.equals(cls.getType()) && "checkAccess".equals(method.getName())) {
                    seen++; List<Instruction> ins=new ArrayList<>();
                    for(Instruction item:method.getImplementation().getInstructions())ins.add(item);
                    check(ins.size()==3 && ins.get(0).getOpcode()==Opcode.CONST_16 && ins.get(1).getOpcode()==Opcode.INVOKE_INTERFACE && ins.get(2).getOpcode()==Opcode.RETURN_VOID,"replacement opcodes");
                    check(((NarrowLiteralInstruction)ins.get(0)).getNarrowLiteral()==256,"LVL LICENSED reason");
                    MethodReference ref=(MethodReference)((ReferenceInstruction)ins.get(1)).getReference();
                    check(ref.getDefiningClass().equals(CALLBACK) && ref.getName().equals("allow"),"allow callback");
                } else if(CHECKER.equals(cls.getType()) && "unchanged".equals(method.getName())) {
                    other++;check(method.getImplementation().getInstructions().iterator().next().getOpcode()==Opcode.RETURN_VOID,"unrelated method retained");
                }
            }
            check(seen==1 && other==1,"exact checker edited");
            rejects(Collections.singletonList(out.toFile()),temp.resolve("already.dex"),"already patched checker");
            rejects(Arrays.asList(input.toFile(),input.toFile()),temp.resolve("duplicate.dex"),"duplicate classes");
            Path incomplete=temp.resolve("incomplete.dex");makeDex(incomplete,Arrays.asList(checker(CHECKER,1),callback(false)));
            rejects(Collections.singletonList(incomplete.toFile()),temp.resolve("incomplete-out.dex"),"incomplete callback");
            Path obfuscated=temp.resolve("obfuscated.dex");makeDex(obfuscated,Arrays.asList(checker("La;",1),callback(true)));
            rejects(Collections.singletonList(obfuscated.toFile()),temp.resolve("obfuscated-out.dex"),"unrecognized checker");
            Path staticMethod=temp.resolve("static.dex");makeDex(staticMethod,Arrays.asList(checker(CHECKER,9),callback(true)));
            rejects(Collections.singletonList(staticMethod.toFile()),temp.resolve("static-out.dex"),"static checker");
            Path wrong=temp.resolve("wrong.dex");Files.write(wrong,new byte[]{'d','e','x','\n','0','4','0',0});
            rejects(Collections.singletonList(wrong.toFile()),temp.resolve("wrong-out.dex"),"unsupported DEX version");
            Path existing=temp.resolve("existing.dex");Files.write(existing,new byte[]{1,2,3});
            try {LvlEditor.patch(Collections.singletonList(input.toFile()),existing.toFile());throw new AssertionError("existing output");}
            catch(IOException expected){checks++;check(Arrays.equals(Files.readAllBytes(existing),new byte[]{1,2,3}),"existing output retained");}
            System.out.println("LvlEditor: "+checks+" assertions passed");
        } finally {
            try (java.util.stream.Stream<Path> paths=Files.walk(temp)) {
                paths.sorted(java.util.Comparator.reverseOrder()).forEach(path -> {try {Files.deleteIfExists(path);}catch(IOException ignored){}});
            }
        }
    }
}
