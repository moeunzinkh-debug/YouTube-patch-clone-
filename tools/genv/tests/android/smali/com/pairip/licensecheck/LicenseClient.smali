# Synthetic counter-only PairIP-shaped methods. The opcode and reference shape
# mirrors the reviewed GenV fingerprint; this is NOT GenV's production code.
.class public Lcom/pairip/licensecheck/LicenseClient;
.super Ljava/lang/Object;

.field public static checkRuns:I
.field public static initRuns:I
.field private static mainThreadRunner:Lcom/pairip/licensecheck/LicenseClient$ImmediateTaskExecutor;
.field private static backgroundRunner:Lcom/pairip/licensecheck/LicenseClient$ImmediateTaskExecutor;
.field private static licenseCheckState:Lcom/pairip/licensecheck/LicenseClient$LicenseCheckState;
.field private static responsePayload:Landroid/os/Bundle;
.field private static packageName:Ljava/lang/String;
.field private static localCheckEnabled:Z
.field private static customTrialEndTriggered:Z

.method static constructor <clinit>()V
    .registers 1
    new-instance v0, Ltest/genv/CounterRunner;
    invoke-direct {v0}, Ltest/genv/CounterRunner;-><init>()V
    sput-object v0, Lcom/pairip/licensecheck/LicenseClient;->mainThreadRunner:Lcom/pairip/licensecheck/LicenseClient$ImmediateTaskExecutor;
    sput-object v0, Lcom/pairip/licensecheck/LicenseClient;->backgroundRunner:Lcom/pairip/licensecheck/LicenseClient$ImmediateTaskExecutor;
    new-instance v0, Lcom/pairip/licensecheck/LicenseClient$LicenseCheckState;
    invoke-direct {v0}, Lcom/pairip/licensecheck/LicenseClient$LicenseCheckState;-><init>()V
    sput-object v0, Lcom/pairip/licensecheck/LicenseClient;->licenseCheckState:Lcom/pairip/licensecheck/LicenseClient$LicenseCheckState;
    return-void
.end method

.method public constructor <init>()V
    .registers 1
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    return-void
.end method

.method private static isIsolatedProcess()Z
    .registers 1
    const/4 v0, 0x0
    return v0
.end method

.method private initiateFreshLicensingServiceConnection(Z)V
    .registers 3
    sget v0, Lcom/pairip/licensecheck/LicenseClient;->initRuns:I
    add-int/lit8 v0, v0, 0x1
    sput v0, Lcom/pairip/licensecheck/LicenseClient;->initRuns:I
    return-void
.end method

.method private handleError(Lcom/pairip/licensecheck/LicenseCheckException;)V
    .registers 2
    return-void
.end method

.method public static checkLicense(Landroid/content/Context;)V
    .registers 3
    const-string v0, "synthetic"
    if-nez p0, :context_ok
    const-string v1, "missing context"
    invoke-static {v0, v1}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;)I
    return-void
  :context_ok
    invoke-static {}, Lcom/pairip/licensecheck/LicenseClient;->isIsolatedProcess()Z
    move-result v1
    if-eqz v1, :regular
    const-string v1, "isolated"
    invoke-static {v0, v1}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I
    return-void
  :regular
    sget-object v0, Lcom/pairip/licensecheck/LicenseClient;->mainThreadRunner:Lcom/pairip/licensecheck/LicenseClient$ImmediateTaskExecutor;
    new-instance v1, Lcom/pairip/licensecheck/LicenseClient$$ExternalSyntheticLambda7;
    invoke-direct {v1, p0}, Lcom/pairip/licensecheck/LicenseClient$$ExternalSyntheticLambda7;-><init>(Landroid/content/Context;)V
    invoke-interface {v0, v1}, Lcom/pairip/licensecheck/LicenseClient$ImmediateTaskExecutor;->run(Ljava/lang/Runnable;)V
    return-void
.end method

.method public initializeLicenseCheck()V
    .registers 4
    sget-object v0, Lcom/pairip/licensecheck/LicenseClient;->licenseCheckState:Lcom/pairip/licensecheck/LicenseClient$LicenseCheckState;
    invoke-virtual {v0}, Lcom/pairip/licensecheck/LicenseClient$LicenseCheckState;->ordinal()I
    move-result v0
    const/4 v1, 0x0
    if-eqz v0, :fresh_a
    const/4 v2, 0x1
    if-eq v0, v2, :validate
    const/4 v2, 0x2
    if-eq v0, v2, :local
    return-void
  :fresh_a
    invoke-direct {p0, v1}, Lcom/pairip/licensecheck/LicenseClient;->initiateFreshLicensingServiceConnection(Z)V
    return-void
  :validate
    sget-object v0, Lcom/pairip/licensecheck/LicenseClient;->responsePayload:Landroid/os/Bundle;
    sget-object v1, Lcom/pairip/licensecheck/LicenseClient;->packageName:Ljava/lang/String;
  :try_start
    invoke-static {v0, v1}, Lcom/pairip/licensecheck/LicenseResponseHelper;->validateResponse(Landroid/os/Bundle;Ljava/lang/String;)V
  :try_end
    return-void
  :caught
    move-exception v0
    invoke-direct {p0, v0}, Lcom/pairip/licensecheck/LicenseClient;->handleError(Lcom/pairip/licensecheck/LicenseCheckException;)V
    return-void
  :local
    sget-boolean v0, Lcom/pairip/licensecheck/LicenseClient;->localCheckEnabled:Z
    if-eqz v0, :fresh_b
    sget-boolean v0, Lcom/pairip/licensecheck/LicenseClient;->customTrialEndTriggered:Z
    if-nez v0, :fresh_b
    sget-object v0, Lcom/pairip/licensecheck/LicenseClient;->backgroundRunner:Lcom/pairip/licensecheck/LicenseClient$ImmediateTaskExecutor;
    new-instance v1, Lcom/pairip/licensecheck/LicenseClient$$ExternalSyntheticLambda8;
    invoke-direct {v1, p0}, Lcom/pairip/licensecheck/LicenseClient$$ExternalSyntheticLambda8;-><init>(Lcom/pairip/licensecheck/LicenseClient;)V
    invoke-interface {v0, v1}, Lcom/pairip/licensecheck/LicenseClient$ImmediateTaskExecutor;->run(Ljava/lang/Runnable;)V
    return-void
  :fresh_b
    invoke-direct {p0, v1}, Lcom/pairip/licensecheck/LicenseClient;->initiateFreshLicensingServiceConnection(Z)V
    return-void
    .catch Lcom/pairip/licensecheck/LicenseCheckException; {:try_start .. :try_end} :caught
.end method
