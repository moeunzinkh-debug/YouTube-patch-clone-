"""Use the baseline toolchain but replace the old process strategy entirely."""
from pathlib import Path
import subprocess
import sys
root = Path(sys.argv[1])
subprocess.run([sys.executable, 'tools/gemini-apk/prepare_build.py', str(root)], check=True)
src = root / 'src/main/kotlin/app/morphe/patches/google/workprofile/ProcessNameSanitizePatch.kt'
src.write_text(Path('tools/gemini-experimental/ProcessIdentityPatch.kt').read_text())
# Only the process strategy changes in this first experiment. This is not yet
# a wholesale port of the external GmsCore engine.
for path in [root / 'patches-bundle.json', root / 'scripts/package-mpp.py']:
    path.write_text(path.read_text().replace('0.1.4', '0.2.0'))
