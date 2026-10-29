package org.telegram.ui;
import android.app.Activity; import android.os.Bundle; import android.widget.LinearLayout;
import app.template.extension.telegram.EmailAlternative; import org.telegram.tgnet.ConnectionsManager; import org.telegram.tgnet.TLRPC;
public class LoginActivity {
  private int activityMode=0,currentViewNum=12; private TLRPC.TL_help_termsOfService currentTermsOfService;
  public final Activity parent=new Activity(); public final ConnectionsManager manager=new ConnectionsManager();
  public int fills,successes; public Bundle lastParams; public TLRPC.auth_SentCode lastResponse;
  public ConnectionsManager getConnectionsManager(){return manager;} public Activity getParentActivity(){return parent;}
  public void setPage(int page,boolean animated,Bundle params,boolean back){currentViewNum=page;lastParams=params;}
  private void fillNextCodeParams(Bundle params,TLRPC.auth_SentCode response){EmailAlternative.observe(params,response);fills++;lastParams=params;lastResponse=response;}
  private void onAuthSuccess(TLRPC.TL_auth_authorization auth){successes++;}
  public void changeMode(int n){activityMode=n;} public void page(int n){currentViewNum=n;} public int page(){return currentViewNum;}
  public TLRPC.TL_help_termsOfService terms(){return currentTermsOfService;}
  public class LoginActivitySetupEmail extends LinearLayout {
    private Bundle currentParams; private boolean nextPressed;
    public LoginActivitySetupEmail(){super(parent);}
    public void setParams(Bundle params){EmailAlternative.install(this,params);if(params!=null)currentParams=params;}
    public boolean busy(){return nextPressed;} public void busy(boolean value){nextPressed=value;}
  }
}
