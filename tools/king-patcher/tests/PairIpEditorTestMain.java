import app.morphe.extension.king.PairIpEditor;
import org.jf.dexlib2.DexFileFactory;
import org.jf.dexlib2.Opcode;
import org.jf.dexlib2.Opcodes;
import org.jf.dexlib2.iface.ClassDef;
import org.jf.dexlib2.iface.Method;
import org.jf.dexlib2.iface.instruction.Instruction;
import org.jf.dexlib2.immutable.ImmutableClassDef;
import org.jf.dexlib2.immutable.ImmutableMethod;
import org.jf.dexlib2.immutable.ImmutableMethodImplementation;
import org.jf.dexlib2.immutable.ImmutableMethodParameter;
import org.jf.dexlib2.immutable.instruction.ImmutableInstruction10x;
import org.jf.dexlib2.immutable.instruction.ImmutableInstruction21c;
import org.jf.dexlib2.immutable.instruction.ImmutableInstruction35c;
import org.jf.dexlib2.immutable.reference.ImmutableFieldReference;
import org.jf.dexlib2.immutable.reference.ImmutableMethodReference;
import org.jf.dexlib2.immutable.reference.ImmutableStringReference;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.zip.Adler32;

/** Synthetic Kimi-shaped PairIP bytecode, not an app or live license check. */
public final class PairIpEditorTestMain {
    private static final String CLIENT="Lcom/pairip/licensecheck/LicenseClient;";
    private static final String APPLICATION="Lcom/pairip/application/Application;";
    private static final String RESPONSE="Lcom/pairip/licensecheck/LicenseResponseHelper;";
    private static final String CONTEXT="Landroid/content/Context;";
    private static int checks;
    private static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
    private static ImmutableMethodReference ref(String owner,String name,List<String> params,String result){
        return new ImmutableMethodReference(owner,name,params,result);
    }
    private static ImmutableMethod method(String owner,String name,List<String> types,int flags,int registers,List<Instruction> ops){
        List<ImmutableMethodParameter> params=new ArrayList<>();
        for(String type:types)params.add(new ImmutableMethodParameter(type,Collections.emptySet(),null));
        return new ImmutableMethod(owner,name,params,"V",flags,Collections.emptySet(),
            new ImmutableMethodImplementation(registers,ops,Collections.emptyList(),Collections.emptyList()));
    }
    static ClassDef app(boolean callsCheck){
        List<Instruction> ops=new ArrayList<>();
        if(callsCheck)ops.add(new ImmutableInstruction35c(Opcode.INVOKE_STATIC,1,1,0,0,0,0,
            ref(CLIENT,"checkLicense",Collections.singletonList(CONTEXT),"V")));
        ops.add(new ImmutableInstruction10x(Opcode.RETURN_VOID));
        return new ImmutableClassDef(APPLICATION,1,"Landroid/app/Application;",Collections.emptyList(),null,
            Collections.emptySet(),Collections.emptyList(),Collections.singletonList(method(APPLICATION,"attachBaseContext",
            Collections.singletonList(CONTEXT),4,2,ops)));
    }
    static ClassDef client(boolean validCheck,boolean validInit){
        List<Instruction> check=new ArrayList<>();
        check.add(new ImmutableInstruction21c(Opcode.CONST_STRING,0,new ImmutableStringReference("synthetic")));
        check.add(new ImmutableInstruction35c(Opcode.INVOKE_STATIC,0,0,0,0,0,0,
            ref(CLIENT,validCheck?"isIsolatedProcess":"different",Collections.emptyList(),"Z")));
        for(int i=0;i<13;i++)check.add(new ImmutableInstruction10x(Opcode.NOP));
        check.add(new ImmutableInstruction10x(Opcode.RETURN_VOID));
        List<Instruction> init=new ArrayList<>();
        init.add(new ImmutableInstruction21c(Opcode.SGET_OBJECT,0,new ImmutableFieldReference(CLIENT,"tag","Ljava/lang/String;")));
        init.add(new ImmutableInstruction35c(Opcode.INVOKE_STATIC,0,0,0,0,0,0,
            ref(RESPONSE,validInit?"validateResponse":"different",Collections.emptyList(),"V")));
        init.add(new ImmutableInstruction35c(Opcode.INVOKE_DIRECT,1,3,0,0,0,0,
            ref(CLIENT,"initiateFreshLicensingServiceConnection",Collections.emptyList(),"V")));
        for(int i=0;i<25;i++)init.add(new ImmutableInstruction10x(Opcode.NOP));
        init.add(new ImmutableInstruction10x(Opcode.RETURN_VOID));
        List<Method> methods=Arrays.asList(
            method(CLIENT,"checkLicense",Collections.singletonList(CONTEXT),9,3,check),
            method(CLIENT,"initializeLicenseCheck",Collections.emptyList(),1,4,init),
            method(CLIENT,"unchanged",Collections.emptyList(),1,1,Collections.singletonList(new ImmutableInstruction10x(Opcode.RETURN_VOID))));
        return new ImmutableClassDef(CLIENT,1,"Ljava/lang/Object;",Collections.emptyList(),null,
            Collections.emptySet(),Collections.emptyList(),methods);
    }
    static List<ClassDef> fixtureClasses(){return Arrays.asList(app(true),client(true,true));}
    static void makeFixture(Path path)throws Exception{LvlEditorTestMain.makeDex(path,fixtureClasses());}
    private static byte[] sha(Path path)throws Exception{return MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path));}
    private static void header(Path path)throws Exception{
        byte[] bytes=Files.readAllBytes(path);
        check(Arrays.equals(Arrays.copyOfRange(bytes,12,32),MessageDigest.getInstance("SHA-1").digest(Arrays.copyOfRange(bytes,32,bytes.length))),"DEX SHA-1");
        Adler32 crc=new Adler32();crc.update(bytes,12,bytes.length-12);long stored=0;
        for(int i=0;i<4;i++)stored|=((long)bytes[8+i]&255)<<(8*i);
        check(stored==crc.getValue(),"DEX Adler-32");
    }
    private static void rejects(List<File> inputs,Path output,String reason)throws Exception{
        try{PairIpEditor.patch(inputs,output.toFile());throw new AssertionError("Should reject "+reason);}
        catch(IOException expected){checks++;check(!Files.exists(output),"no output for "+reason);}
    }
    public static void main(String[] args)throws Exception{
        Path temp=Files.createTempDirectory("pairip-fixture-");
        try{
            Path input=temp.resolve("input.dex"),output=temp.resolve("output.dex");makeFixture(input);byte[] before=sha(input);
            check(PairIpEditor.patch(Collections.singletonList(input.toFile()),output.toFile())==0,"matched index");
            check(Arrays.equals(before,sha(input)),"input unchanged");header(output);
            int patched=0,unchanged=0,app=0;
            for(ClassDef cls:DexFileFactory.loadDexFile(output.toFile(),Opcodes.forDexVersion(35)).getClasses())for(Method m:cls.getMethods()){
                if(cls.getType().equals(CLIENT)&&(m.getName().equals("checkLicense")||m.getName().equals("initializeLicenseCheck"))){
                    List<Instruction> ops=new ArrayList<>();for(Instruction i:m.getImplementation().getInstructions())ops.add(i);
                    check(ops.size()==1&&ops.get(0).getOpcode()==Opcode.RETURN_VOID&&m.getImplementation().getRegisterCount()==1,"client entry point returned");patched++;
                }else if(cls.getType().equals(CLIENT)&&m.getName().equals("unchanged"))unchanged++;
                else if(cls.getType().equals(APPLICATION)&&m.getName().equals("attachBaseContext")){
                    check(m.getImplementation().getInstructions().iterator().next().getOpcode()==Opcode.INVOKE_STATIC,"application call retained");app++;
                }
            }
            check(patched==2&&unchanged==1&&app==1,"only two client entry points modified");
            Path a=temp.resolve("app.dex"),c=temp.resolve("client.dex");
            LvlEditorTestMain.makeDex(a,Collections.singletonList(app(true)));LvlEditorTestMain.makeDex(c,Collections.singletonList(client(true,true)));
            check(PairIpEditor.patch(Arrays.asList(a.toFile(),c.toFile()),temp.resolve("multi.dex").toFile())==1,"multi DEX client index");
            rejects(Collections.singletonList(output.toFile()),temp.resolve("again.dex"),"already patched");
            rejects(Arrays.asList(input.toFile(),input.toFile()),temp.resolve("duplicate.dex"),"duplicate classes");
            Path noApp=temp.resolve("no-app.dex");LvlEditorTestMain.makeDex(noApp,Collections.singletonList(client(true,true)));
            rejects(Collections.singletonList(noApp.toFile()),temp.resolve("no-app-out.dex"),"missing application");
            Path wrongApp=temp.resolve("wrong-app.dex");LvlEditorTestMain.makeDex(wrongApp,Arrays.asList(app(false),client(true,true)));
            rejects(Collections.singletonList(wrongApp.toFile()),temp.resolve("wrong-app-out.dex"),"missing entry call");
            Path wrongCheck=temp.resolve("wrong-check.dex");LvlEditorTestMain.makeDex(wrongCheck,Arrays.asList(app(true),client(false,true)));
            rejects(Collections.singletonList(wrongCheck.toFile()),temp.resolve("wrong-check-out.dex"),"unreviewed check");
            Path wrongInit=temp.resolve("wrong-init.dex");LvlEditorTestMain.makeDex(wrongInit,Arrays.asList(app(true),client(true,false)));
            rejects(Collections.singletonList(wrongInit.toFile()),temp.resolve("wrong-init-out.dex"),"unreviewed init");
            Path corrupt=temp.resolve("corrupt.dex");byte[] bad=Files.readAllBytes(input);bad[8]^=1;Files.write(corrupt,bad);
            rejects(Collections.singletonList(corrupt.toFile()),temp.resolve("corrupt-out.dex"),"invalid DEX checksum");
            Path existing=temp.resolve("existing.dex");Files.write(existing,new byte[]{1,2});
            try{PairIpEditor.patch(Collections.singletonList(input.toFile()),existing.toFile());throw new AssertionError("overwrite");}
            catch(IOException expected){checks++;check(Arrays.equals(Files.readAllBytes(existing),new byte[]{1,2}),"existing output preserved");}
            System.out.println("PairIpEditor: "+checks+" assertions passed");
        }finally{try(java.util.stream.Stream<Path> paths=Files.walk(temp)){paths.sorted(java.util.Comparator.reverseOrder()).forEach(p->{try{Files.deleteIfExists(p);}catch(IOException ignored){}});}}
    }
}
