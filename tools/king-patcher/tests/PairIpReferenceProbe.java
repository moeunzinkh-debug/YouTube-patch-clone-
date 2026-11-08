import app.morphe.extension.king.PairIpEditor;
import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.List;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

/** Read-only reference probe; no APK or extracted DEX is uploaded or installed. */
public final class PairIpReferenceProbe {
    private static byte[] digest(Path path)throws Exception {
        MessageDigest md=MessageDigest.getInstance("SHA-256");
        try(java.io.InputStream in=Files.newInputStream(path)){byte[] b=new byte[32768];int n;while((n=in.read(b))!=-1)if(n>0)md.update(b,0,n);}
        return md.digest();
    }
    public static void main(String[] args)throws Exception {
        Path apk=Path.of(args[0]),temp=Files.createTempDirectory("pairip-reference-");byte[] before=digest(apk);
        try {
            List<File> dex=new ArrayList<>();
            try(ZipFile zip=new ZipFile(apk.toFile())){
                for(int n=1;n<=32;n++){
                    String name=n==1?"classes.dex":"classes"+n+".dex";ZipEntry entry=zip.getEntry(name);
                    if(entry==null)break;
                    if(entry.getSize()<0||entry.getSize()>128L*1024*1024)throw new IOException("Reference DEX size unsupported");
                    Path file=temp.resolve(name);
                    try(java.io.InputStream in=zip.getInputStream(entry)){Files.copy(in,file);}
                    dex.add(file.toFile());
                }
            }
            try {
                int index=PairIpEditor.patch(dex,temp.resolve("modified.dex").toFile());
                System.out.println("REFERENCE_MATCH: reviewed PairIP shape matched in DEX index "+index+"; temporary DEX verified");
            } catch(IOException unrecognized) {
                System.out.println("REFERENCE_NOT_MATCHED: "+unrecognized.getMessage());
                // Emit only structural metadata for the two known method names.
                // No strings, method bodies, account data or APK is published.
                for(File file:dex){
                    byte[] magic=new byte[8];try(java.io.FileInputStream in=new java.io.FileInputStream(file)){if(in.read(magic)!=8)throw new IOException("short DEX");}
                    int version=Integer.parseInt(new String(magic,4,3,java.nio.charset.StandardCharsets.US_ASCII));
                    org.jf.dexlib2.iface.DexFile loaded=org.jf.dexlib2.DexFileFactory.loadDexFile(file,org.jf.dexlib2.Opcodes.forDexVersion(version));
                    for(org.jf.dexlib2.iface.ClassDef cls:loaded.getClasses())if(cls.getType().equals("Lcom/pairip/licensecheck/LicenseClient;"))
                        for(org.jf.dexlib2.iface.Method method:cls.getMethods())if(method.getName().equals("checkLicense")||method.getName().equals("initializeLicenseCheck")){
                            org.jf.dexlib2.iface.MethodImplementation impl=method.getImplementation();int count=0;String first="none";
                            if(impl!=null)for(org.jf.dexlib2.iface.instruction.Instruction instruction:impl.getInstructions()){
                                if(count++==0)first=instruction.getOpcode().name();
                            }
                            System.out.println("REFERENCE_SHAPE: "+method.getName()+" registers="+(impl==null?-1:impl.getRegisterCount())+" instructions="+count+" first="+first);
                        }
                }
            }
            if(!java.util.Arrays.equals(before,digest(apk)))throw new AssertionError("Reference APK changed");
            System.out.println("REFERENCE_UNCHANGED: no APK was written, installed, or published");
        }finally{try(java.util.stream.Stream<Path> paths=Files.walk(temp)){paths.sorted(java.util.Comparator.reverseOrder()).forEach(p->{try{Files.deleteIfExists(p);}catch(IOException ignored){}});}}
    }
}
