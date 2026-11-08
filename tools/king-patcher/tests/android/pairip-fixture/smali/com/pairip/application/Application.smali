.class public Lcom/pairip/application/Application;
.super Landroid/app/Application;

.method public constructor <init>()V
    .registers 1
    invoke-direct {p0}, Landroid/app/Application;-><init>()V
    return-void
.end method

.method protected attachBaseContext(Landroid/content/Context;)V
    .registers 2
    invoke-super {p0, p1}, Landroid/app/Application;->attachBaseContext(Landroid/content/Context;)V
    invoke-static {p1}, Lcom/pairip/licensecheck/LicenseClient;->checkLicense(Landroid/content/Context;)V
    return-void
.end method
