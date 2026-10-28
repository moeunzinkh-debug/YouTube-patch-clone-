"""Verify the small SimSimi-only package; never apply YouTube bundle assumptions."""
import hashlib
import json
import sys
import zipfile
from pathlib import Path

bundle = Path(sys.argv[1])
checksum = bundle.with_name(bundle.name + '.sha256')
digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
assert checksum.read_text().split()[0] == digest, 'Bundle checksum mismatch'
with zipfile.ZipFile(bundle) as archive:
    assert archive.testzip() is None, 'Corrupt archive'
    names = archive.namelist()
    manifest = archive.read('META-INF/MANIFEST.MF').decode().replace('\r', '')
    assert 'Version: 0.3.0-dev.1\n' in manifest, manifest
    assert 'Patcher-Version: 2.0.0\n' in manifest, manifest
    assert 'app/morphe/patches/simsimi/AdGatePatchKt.class' in names
    assert 'app/morphe/patches/simsimi/AdGateTransform.class' in names
    assert not any(n.startswith(('app/morphe/patches/youtube/', 'app/morphe/patches/gemini/', 'app/morphe/patches/google/')) for n in names)
    assert 'app/morphe/patches/simsimi/PullRefreshPatchKt.class' in names
    assert 'app/morphe/patches/simsimi/MicroGServicePatchKt.class' in names
    extension = archive.read('extensions/simsimi.mpe')
    assert extension.startswith(b'dex\n') and b'PullRefresh' in extension and b'PullGesture' in extension
    assert b'ConversationScreen' in extension, 'Missing Conversation-only screen guard'
    assert any(b'Daily bonus without video (client path, experimental)' in archive.read(name) for name in names if name.endswith('.class')), 'Missing daily bonus selector'
    feature_class = archive.read('app/morphe/patches/simsimi/MembershipFeaturePatchesKt.class')
    for label in (
        'Conversation level controls', 'Profile photo controls',
        'Custom group cover controls', 'Photo sending controls',
        'Read receipt display', 'Membership item controls',
    ):
        assert (label + ' (client only, experimental)').encode() in feature_class, f'Missing selector: {label}'
    assert not any(n.endswith('Test.class') for n in names)
print(json.dumps({'bundle': str(bundle), 'sha256': digest, 'size': bundle.stat().st_size,
                  'status': 'Experimental standalone SimSimi package structure verified; device behavior not tested.'}, indent=2))
