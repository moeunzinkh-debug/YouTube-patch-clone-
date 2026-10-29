package org.telegram.tgnet;
public class TLRPC {
  public static class TL_error extends TLObject { public String text; }
  public static class TL_auth_resendCode extends TLObject { public String phone_number,phone_code_hash; }
  public static abstract class auth_SentCode extends TLObject {
    public int flags,timeout; public Object type,next_type; public String phone_code_hash; public auth_Authorization authorization;
  }
  public static class TL_auth_sentCode extends auth_SentCode {}
  public static class TL_auth_sentCodePaymentRequired extends auth_SentCode {}
  public static class TL_auth_sentCodeSuccess extends auth_SentCode {}
  public static class TL_auth_sentCodeTypeSetUpEmailRequired {}
  public static class TL_auth_sentCodeTypeEmailCode {}
  public static class TL_auth_codeTypeSms {}
  public static class TL_auth_codeTypeFlashCall {}
  public static class TL_auth_codeTypeCall {}
  public static class TL_auth_codeTypeMissedCall {}
  public static class TL_auth_codeTypeFragmentSms {}
  public static abstract class auth_Authorization extends TLObject {}
  public static class TL_auth_authorization extends auth_Authorization {}
  public static class TL_auth_authorizationSignUpRequired extends auth_Authorization { public TL_help_termsOfService terms_of_service; }
  public static class TL_help_termsOfService extends TLObject {}
}
