# A synthetic implementation with the instruction counts and references used
# by the reviewed Kimi fingerprint. Only counters are changed; no network calls.
.class public Lcom/pairip/licensecheck/LicenseClient;
.super Ljava/lang/Object;

.field public static checkRuns:I
.field public static initRuns:I
.field private static tag:Ljava/lang/String;

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

.method private initiateFreshLicensingServiceConnection()V
    .registers 1
    return-void
.end method

.method public static checkLicense(Landroid/content/Context;)V
    .registers 3
    const-string v0, "synthetic PairIP"
    invoke-static {}, Lcom/pairip/licensecheck/LicenseClient;->isIsolatedProcess()Z
    move-result v0
    const/4 v0, 0x1
    sput v0, Lcom/pairip/licensecheck/LicenseClient;->checkRuns:I
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    return-void
.end method

.method public initializeLicenseCheck()V
    .registers 4
    sget-object v0, Lcom/pairip/licensecheck/LicenseClient;->tag:Ljava/lang/String;
    invoke-static {}, Lcom/pairip/licensecheck/LicenseResponseHelper;->validateResponse()V
    invoke-direct {p0}, Lcom/pairip/licensecheck/LicenseClient;->initiateFreshLicensingServiceConnection()V
    const/4 v0, 0x1
    sput v0, Lcom/pairip/licensecheck/LicenseClient;->initRuns:I
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    return-void
.end method
