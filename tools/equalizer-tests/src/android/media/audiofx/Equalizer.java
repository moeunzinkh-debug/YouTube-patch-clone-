package android.media.audiofx;
public class Equalizer {
 public static Equalizer last; public static int created; public static boolean failCreate;
 public boolean released, control=true; private short[] levels={0,0};
 public Equalizer(int priority,int session){if(session<=0||failCreate)throw new IllegalStateException(); last=this;created++;}
 public boolean hasControl(){return control;} public short[] getBandLevelRange(){return new short[]{-1500,1500};}
 public short getNumberOfBands(){return 2;} public int getCenterFreq(short b){return b==0?60000:1000000;}
 public void setBandLevel(short b,short l){levels[b]=l;} public short getBandLevel(short b){return levels[b];}
 public int setEnabled(boolean e){return 0;} public void release(){released=true;}
 public short getNumberOfPresets(){return 2;} public String getPresetName(short p){return "Preset "+p;}
 public void usePreset(short p){levels[0]=(short)(p*500);levels[1]=(short)(p*-500);}
}
