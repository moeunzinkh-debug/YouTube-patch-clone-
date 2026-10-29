package org.telegram.tgnet;
public class ConnectionsManager {
  public int sends,flags,cancels; public TLObject lastRequest; public RequestDelegate callback;
  public int sendRequest(TLObject request,RequestDelegate callback,int flags){sends++;this.flags=flags;this.lastRequest=request;this.callback=callback;return 123;}
  public void cancelRequest(int id,boolean notify){if(id!=123 || !notify)throw new AssertionError(); cancels++;}
  public void respond(TLObject result,TLRPC.TL_error error){callback.run(result,error);}
}
