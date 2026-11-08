import app.morphe.extension.king.AxmlEditor;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;

/** Standalone tests: run on a JRE without the Android SDK or the user's APK. */
public final class AxmlEditorTestMain {
    private static int checks;
    private static void check(boolean condition, String message) {
        checks++; if (!condition) throw new AssertionError(message);
    }
    private static int u16(byte[] b, int p) { return (b[p] & 255) | ((b[p+1] & 255) << 8); }
    private static int i32(byte[] b, int p) { return (b[p] & 255) | ((b[p+1] & 255) << 8) | ((b[p+2] & 255) << 16) | (b[p+3] << 24); }
    private static void p16(byte[] b, int p, int v) { b[p]=(byte)v; b[p+1]=(byte)(v>>>8); }
    private static void p32(byte[] b, int p, int v) { b[p]=(byte)v; b[p+1]=(byte)(v>>>8); b[p+2]=(byte)(v>>>16); b[p+3]=(byte)(v>>>24); }
    private static byte[] chunk(int type, int header, int size) {
        byte[] b=new byte[size]; p16(b,0,type); p16(b,2,header); p32(b,4,size); return b;
    }
    private static byte[] pool(List<String> values, boolean utf8) {
        ByteArrayOutputStream payload = new ByteArrayOutputStream();
        int[] offsets = new int[values.size()];
        for (int i=0;i<values.size();i++) {
            offsets[i]=payload.size(); String s=values.get(i);
            byte[] data=s.getBytes(utf8 ? StandardCharsets.UTF_8 : StandardCharsets.UTF_16LE);
            if (utf8) { if (s.length()>=128 || data.length>=128) throw new AssertionError(); payload.write(s.length()); payload.write(data.length); }
            else { payload.write(s.length() & 255); payload.write(s.length() >>> 8); }
            payload.write(data,0,data.length); payload.write(0); if(!utf8) payload.write(0);
        }
        while ((payload.size() & 3)!=0) payload.write(0);
        int start=28+4*values.size(); byte[] b=chunk(1,28,start+payload.size());
        p32(b,8,values.size()); p32(b,16,(utf8?0x100:0)|1); p32(b,20,start);
        for(int i=0;i<offsets.length;i++) p32(b,28+4*i,offsets[i]);
        System.arraycopy(payload.toByteArray(),0,b,start,payload.size()); return b;
    }
    private static byte[] map(int count, boolean existingVisibility) {
        byte[] b=chunk(0x180,8,8+4*count); p32(b,8+3*4,0x010100d0); p32(b,8+4*4,0x0101014f);
        if (existingVisibility) p32(b,8+6*4,0x010100dc); return b;
    }
    private static void attr(byte[] b,int p,int name,int type,int value) {
        p32(b,p,0); p32(b,p+4,name); p32(b,p+8,-1); p16(b,p+12,8); b[p+15]=(byte)type; p32(b,p+16,value);
    }
    private static byte[] start(int name, boolean child, boolean existingVisibility) {
        int count=child?(existingVisibility?3:2):0; byte[] b=chunk(0x102,16,36+20*count);
        p32(b,12,-1); p32(b,16,-1); p32(b,20,name); p16(b,24,20); p16(b,26,20); p16(b,28,count);
        if(child) { p16(b,30,1); attr(b,36,3,1,0x7f0a0001); int p=56;
            if(existingVisibility) { attr(b,p,6,0x10,0); p+=20; }
            attr(b,p,4,3,5);
        }
        return b;
    }
    private static byte[] end(int name) { byte[] b=chunk(0x103,16,24); p32(b,12,-1);p32(b,16,-1);p32(b,20,name);return b; }
    static byte[] xml(boolean utf8,boolean existingVisibility) {
        List<String> values=existingVisibility
            ? Arrays.asList("http://schemas.android.com/apk/res/android","LinearLayout","Button","id","text","សួស្តី Hello","visibility")
            : Arrays.asList("http://schemas.android.com/apk/res/android","LinearLayout","Button","id","text","សួស្តី Hello");
        ByteArrayOutputStream out=new ByteArrayOutputStream();
        for(byte[] b: new byte[][] {chunk(3,8,8),pool(values,utf8),map(values.size(),existingVisibility),
                                    start(1,false,existingVisibility),start(2,true,existingVisibility),end(2),end(1)}) out.write(b,0,b.length);
        byte[] result=out.toByteArray();p32(result,4,result.length);return result;
    }
    static byte[] manifest(boolean split) {
        List<String> values=Arrays.asList("manifest", "split", "feature");
        byte[] root=chunk(0x102,16,split?56:36);
        p32(root,12,-1);p32(root,16,-1);p32(root,20,0);p16(root,24,20);p16(root,26,20);p16(root,28,split?1:0);
        if(split){attr(root,36,1,3,2);p32(root,36,-1);}
        ByteArrayOutputStream out=new ByteArrayOutputStream();
        for(byte[] b:new byte[][]{chunk(3,8,8),pool(values,true),root,end(0)})out.write(b,0,b.length);
        byte[] result=out.toByteArray();p32(result,4,result.length);return result;
    }
    private static int[] findVisibility(byte[] xml, int ordinal) {
        int cursor=8, seen=0; int[] ids=new int[0];
        while(cursor<xml.length) {
            int type=u16(xml,cursor),size=i32(xml,cursor+4);
            if(type==0x180) {ids=new int[(size-8)/4]; for(int i=0;i<ids.length;i++)ids[i]=i32(xml,cursor+8+4*i);}
            if(type==0x102 && seen++==ordinal) {
                int count=u16(xml,cursor+28), attr=cursor+16+u16(xml,cursor+24);
                for(int i=0;i<count;i++) {int p=attr+i*20, name=i32(xml,p+4);if(name>=0&&name<ids.length&&ids[name]==0x010100dc)
                    return new int[]{i,xml[p+15]&255,i32(xml,p+16),u16(xml,cursor+30)};}
            }
            cursor+=size;
        }
        return null;
    }
    private static void rejects(Runnable action, String reason) {
        try {action.run();throw new AssertionError("Should reject "+reason);}catch(IllegalArgumentException expected){checks++;}
    }
    public static void main(String[] args) {
        for(boolean utf8:new boolean[]{true,false}) for(boolean existing:new boolean[]{true,false}) {
            byte[] before=xml(utf8,existing); List<AxmlEditor.Node> nodes=AxmlEditor.list(before);
            check(nodes.size()==2 && nodes.get(0).depth==0 && nodes.get(1).depth==1,"node tree");
            check(nodes.get(1).tag.equals("Button") && nodes.get(1).text.equals("សួស្តី Hello"),"label");
            check(nodes.get(1).resourceId==0x7f0a0001,"id");
            byte[] after=AxmlEditor.hide(before,Collections.singleton(1));
            check(i32(after,4)==after.length && (after.length&3)==0,"file length");
            int[] attr=findVisibility(after,1); check(attr!=null && attr[1]==0x10 && attr[2]==2,"compiled GONE enum (not View.GONE=8)");
            check(attr[0]==1 && attr[3]==1,"sorted attribute and original idIndex");
            check(AxmlEditor.list(after).get(1).text.equals("សួស្តី Hello"),"text preserved");
            check(existing ? after.length==before.length : after.length>before.length,"append versus update");
            byte[] two=AxmlEditor.hide(before,new HashSet<>(Arrays.asList(0,1)));
            check(findVisibility(two,0)!=null && findVisibility(two,1)!=null,"multiple nodes");
            rejects(()->AxmlEditor.hide(before,Collections.emptySet()),"empty selection");
            rejects(()->AxmlEditor.hide(before,Collections.singleton(3)),"stale selection");
            byte[] truncated=Arrays.copyOf(before,before.length-1);
            rejects(()->AxmlEditor.list(truncated),"truncated XML");
            byte[] wrongRoot=before.clone();wrongRoot[0]=9;
            rejects(()->AxmlEditor.list(wrongRoot),"wrong root type");
            byte[] badEnd=before.clone();p32(badEnd,badEnd.length-4,2);
            rejects(()->AxmlEditor.list(badEnd),"mismatched closing tag");
        }
        check(!AxmlEditor.isSplitManifest(manifest(false)),"single APK manifest");
        check(AxmlEditor.isSplitManifest(manifest(true)),"split manifest detected");
        rejects(()->AxmlEditor.isSplitManifest(xml(true,false)),"non-manifest root");
        System.out.println("AxmlEditor: "+checks+" assertions passed");
    }
}
