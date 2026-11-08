import app.morphe.extension.king.ApkArchive;
import app.morphe.extension.king.AxmlEditor;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import java.util.zip.CRC32;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;
import java.util.zip.ZipOutputStream;

/** Archive tests use only generated fixtures; no app APK is read or distributed. */
public final class ApkArchiveTestMain {
    private static int checks;
    private static void check(boolean ok,String message){checks++;if(!ok)throw new AssertionError(message);}
    private static void entry(ZipOutputStream out,String name,byte[] bytes,boolean stored) throws Exception {
        ZipEntry entry=new ZipEntry(name);
        if(stored){CRC32 crc=new CRC32();crc.update(bytes);entry.setMethod(ZipEntry.STORED);entry.setSize(bytes.length);entry.setCompressedSize(bytes.length);entry.setCrc(crc.getValue());}
        out.putNextEntry(entry);out.write(bytes);out.closeEntry();
    }
    private static byte[] content(ZipFile zip,String path) throws Exception {
        try(java.io.InputStream in=zip.getInputStream(zip.getEntry(path));ByteArrayOutputStream out=new ByteArrayOutputStream()){
            byte[] buffer=new byte[2048];int count;while((count=in.read(buffer))!=-1)out.write(buffer,0,count);return out.toByteArray();
        }
    }
    private static byte[] sha(Path path)throws Exception{return MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path));}
    private static int u16(byte[] b,int p){return (b[p]&255)|((b[p+1]&255)<<8);}
    private static int i32(byte[] b,int p){return u16(b,p)|(u16(b,p+2)<<16);}
    private static int entryOffset(byte[] zip,String name){
        // Read central-directory local offsets, then local name and extra lengths.
        int eocd=-1;for(int i=zip.length-22;i>=0&&i>=zip.length-65557;i--)if(i32(zip,i)==0x06054b50){eocd=i;break;}
        if(eocd<0)throw new AssertionError("no end of central directory");
        int pos=i32(zip,eocd+16),count=u16(zip,eocd+10);
        for(int i=0;i<count;i++){
            if(i32(zip,pos)!=0x02014b50)throw new AssertionError("bad central record");
            int n=u16(zip,pos+28),x=u16(zip,pos+30),c=u16(zip,pos+32),local=i32(zip,pos+42);
            String found=new String(zip,pos+46,n,java.nio.charset.StandardCharsets.UTF_8);
            if(found.equals(name))return local+30+u16(zip,local+26)+u16(zip,local+28);
            pos+=46+n+x+c;
        }
        throw new AssertionError("entry not found: "+name);
    }
    private static void fixture(Path path,byte[] dex,boolean unsafe) throws Exception {
        try(ZipOutputStream out=new ZipOutputStream(Files.newOutputStream(path))){
            entry(out,"AndroidManifest.xml",new byte[]{1,2,3},true);
            entry(out,"classes.dex",dex,true);
            entry(out,"res/ab/layout.xml",AxmlEditorTestMain.xml(true,false),false);
            entry(out,"resources.arsc",new byte[]{7,8,9},true);
            entry(out,"lib/arm64-v8a/libtest.so",new byte[]{10,11,12},true);
            entry(out,"META-INF/CERT.RSA",new byte[]{13},false);
            entry(out,"META-INF/MANIFEST.MF",new byte[]{14},false);
            entry(out,"assets/unchanged.txt",new byte[]{15,16},false);
            if(unsafe)entry(out,"../escape",new byte[]{17},false);
        }
    }
    private interface Action {void run()throws Exception;}
    private static void rejects(Action action,Path output,String reason)throws Exception{
        try{action.run();throw new AssertionError("Should reject "+reason);}catch(IOException expected){checks++;check(!Files.exists(output),"no output on "+reason);}
    }
    public static void main(String[] args)throws Exception{
        Path temp=Files.createTempDirectory("archive-fixture-");
        try{
            Path dex=temp.resolve("fixture.dex");LvlEditorTestMain.makeFixture(dex);
            Path input=temp.resolve("input.apk");fixture(input,Files.readAllBytes(dex),false);byte[] digest=sha(input);
            ApkArchive.Layouts layouts=ApkArchive.listLayouts(input.toFile());
            check(!layouts.truncated&&layouts.layouts.size()==1,"one supported layout");
            check(layouts.layouts.get(0).nodes.size()==2&&layouts.layouts.get(0).nodes.get(1).tag.equals("Button"),"manual node listing");
            Map<String,Set<Integer>> select=new HashMap<>();select.put("res/ab/layout.xml",Collections.singleton(1));
            Path ui=temp.resolve("ui.apk");ApkArchive.buildUi(input.toFile(),ui.toFile(),select);
            check(Arrays.equals(digest,sha(input)),"original UI APK unchanged");
            byte[] output=Files.readAllBytes(ui);
            try(ZipFile zip=new ZipFile(ui.toFile());ZipFile original=new ZipFile(input.toFile())){
                byte[] before=content(original,"res/ab/layout.xml"),after=content(zip,"res/ab/layout.xml");
                check(!Arrays.equals(before,after)&&Arrays.equals(after,AxmlEditor.hide(before,Collections.singleton(1))),"selected node hidden");
                check(Arrays.equals(content(zip,"assets/unchanged.txt"),content(original,"assets/unchanged.txt")),"unselected data retained");
                check(Arrays.equals(content(zip,"classes.dex"),content(original,"classes.dex")),"UI does not alter dex");
                check(zip.getEntry("META-INF/CERT.RSA")==null&&zip.getEntry("META-INF/MANIFEST.MF")==null,"old signatures removed");
            }
            check(entryOffset(output,"resources.arsc")%4==0,"stored resources aligned");
            check(entryOffset(output,"classes.dex")%4==0,"stored DEX aligned");
            check(entryOffset(output,"lib/arm64-v8a/libtest.so")%16384==0,"native library 16 KiB aligned");
            Path missing=temp.resolve("missing.apk");Map<String,Set<Integer>> stale=new HashMap<>();stale.put("res/missing.xml",Collections.singleton(1));
            rejects(()->ApkArchive.buildUi(input.toFile(),missing.toFile(),stale),missing,"missing layout");
            Path wrong=temp.resolve("wrong.apk");select.put("res/ab/layout.xml",Collections.singleton(99));
            rejects(()->ApkArchive.buildUi(input.toFile(),wrong.toFile(),select),wrong,"stale node");
            Path unsafe=temp.resolve("unsafe.apk");fixture(unsafe,Files.readAllBytes(dex),true);
            Path rejected=temp.resolve("rejected.apk");select.put("res/ab/layout.xml",Collections.singleton(1));
            rejects(()->ApkArchive.buildUi(unsafe.toFile(),rejected.toFile(),select),rejected,"unsafe ZIP path");
            Path existing=temp.resolve("existing.apk");Files.write(existing,new byte[]{1,2});
            try{ApkArchive.buildUi(input.toFile(),existing.toFile(),select);throw new AssertionError("overwrite");}catch(IOException expected){checks++;check(Arrays.equals(Files.readAllBytes(existing),new byte[]{1,2}),"existing output preserved");}
            Path work=temp.resolve("work");Files.createDirectory(work);Path lvl=temp.resolve("lvl.apk");
            ApkArchive.buildLvl(input.toFile(),work.toFile(),lvl.toFile());
            check(Arrays.equals(digest,sha(input)),"original LVL APK unchanged");
            try(java.util.stream.Stream<Path> children=Files.list(work)){check(children.count()==0,"working DEX files cleaned");}
            try(ZipFile zip=new ZipFile(lvl.toFile());ZipFile original=new ZipFile(input.toFile())){
                check(!Arrays.equals(content(zip,"classes.dex"),content(original,"classes.dex")),"LVL dex changed");
                check(Arrays.equals(content(zip,"res/ab/layout.xml"),content(original,"res/ab/layout.xml")),"LVL does not alter layout");
                check(zip.getEntry("META-INF/CERT.RSA")==null,"LVL signature removed");
            }
            System.out.println("ApkArchive: "+checks+" assertions passed");
        }finally{
            try(java.util.stream.Stream<Path> paths=Files.walk(temp)){paths.sorted(java.util.Comparator.reverseOrder()).forEach(p->{try{Files.deleteIfExists(p);}catch(IOException ignored){}});}
        }
    }
}
