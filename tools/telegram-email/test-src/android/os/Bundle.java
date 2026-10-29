package android.os;
import java.util.HashMap;
public class Bundle {
  private final HashMap<String, Object> values = new HashMap<>();
  public void putString(String k, String v) { values.put(k,v); }
  public String getString(String k) { Object v=values.get(k); return v instanceof String ? (String)v : null; }
  public void putInt(String k,int v) { values.put(k,v); }
  public int getInt(String k) { return getInt(k,0); }
  public int getInt(String k,int d) { Object v=values.get(k); return v instanceof Integer ? (Integer)v : d; }
  public void putLong(String k,long v) { values.put(k,v); }
  public long getLong(String k,long d) { Object v=values.get(k); return v instanceof Long ? (Long)v : d; }
  public void putBoolean(String k,boolean v) { values.put(k,v); }
  public boolean getBoolean(String k,boolean d) { Object v=values.get(k); return v instanceof Boolean ? (Boolean)v : d; }
  public void remove(String k) { values.remove(k); }
  public boolean containsKey(String k) { return values.containsKey(k); }
}
