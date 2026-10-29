package android.app;
import android.content.Context; import android.content.DialogInterface;
public class AlertDialog implements DialogInterface {
  public static AlertDialog last; private DialogInterface.OnClickListener yes,no;
  public void accept(){ if(yes!=null) yes.onClick(this,-1); }
  public void cancel(){ if(no!=null) no.onClick(this,-2); }
  public static class Builder {
    private final AlertDialog dialog=new AlertDialog();
    public Builder(Context c){}
    public Builder setTitle(CharSequence s){return this;}
    public Builder setMessage(CharSequence s){return this;}
    public Builder setNegativeButton(CharSequence s,DialogInterface.OnClickListener c){dialog.no=c;return this;}
    public Builder setPositiveButton(CharSequence s,DialogInterface.OnClickListener c){dialog.yes=c;return this;}
    public AlertDialog show(){last=dialog;return dialog;}
  }
}
