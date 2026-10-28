"""Prepare a completely isolated Morphe project; never change the YouTube build."""
import shutil
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
dest = Path(sys.argv[1]).resolve()
assert not dest.exists(), 'Use a new temporary build directory'
shutil.copytree(root / 'tools/simsimi/project', dest)
for filename in ('gradlew', 'gradlew.bat', 'build.gradle.kts'):
    shutil.copy2(root / filename, dest / filename)
shutil.copytree(root / 'gradle', dest / 'gradle')
settings = (root / 'settings.gradle.kts').read_text()
settings = settings[:settings.index('// Include morphe-patcher as composite builds')]
settings = settings.replace('rootProject.name = "youtube-patch-clone"', 'rootProject.name = "simsimi-patches"')
settings = settings.replace('include(":patches:stub")', '')
(dest / 'settings.gradle.kts').write_text(settings)
(dest / 'extensions').mkdir(exist_ok=True)
shutil.copy2(root / 'extensions/proguard-rules.pro', dest / 'extensions/proguard-rules.pro')
(dest / 'gradle.properties').write_text('org.gradle.jvmargs=-Xmx2048M\nversion=0.3.0-dev.1\nandroid.useAndroidX=true\n')
print('Isolated project:', dest)
