package android.content;
import java.util.*;
public class Context {
 public static final int MODE_PRIVATE=0;
 private final Memory prefs=new Memory();
 public SharedPreferences getSharedPreferences(String n,int m){return prefs;}
 static class Memory implements SharedPreferences, SharedPreferences.Editor {
  Map<String,Object> data=new HashMap<>();
  public boolean getBoolean(String k,boolean d){return (boolean)data.getOrDefault(k,d);}
  public int getInt(String k,int d){return (int)data.getOrDefault(k,d);}
  public Editor edit(){return this;} public Editor putBoolean(String k,boolean v){data.put(k,v);return this;}
  public Editor putInt(String k,int v){data.put(k,v);return this;}
  public Editor clear(){data.clear();return this;} public void apply(){}
 }
}
