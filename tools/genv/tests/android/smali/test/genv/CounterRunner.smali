.class public Ltest/genv/CounterRunner;
.super Ljava/lang/Object;
.implements Lcom/pairip/licensecheck/LicenseClient$ImmediateTaskExecutor;
.method public constructor <init>()V
    .registers 1
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    return-void
.end method
.method public run(Ljava/lang/Runnable;)V
    .registers 3
    sget v0, Lcom/pairip/licensecheck/LicenseClient;->checkRuns:I
    add-int/lit8 v0, v0, 0x1
    sput v0, Lcom/pairip/licensecheck/LicenseClient;->checkRuns:I
    return-void
.end method
