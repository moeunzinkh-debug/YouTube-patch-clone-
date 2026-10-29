#!/usr/bin/env python3
"""Compare real original/patched Telegram DEX hooks; never inspect account data."""
from __future__ import annotations

import gc
import json
import re
import sys
import zipfile
from pathlib import Path

from androguard.core.dex import DEX
from loguru import logger

logger.remove()
LOGIN = 'Lorg/telegram/ui/LoginActivity;'
SETUP = 'Lorg/telegram/ui/LoginActivity$LoginActivitySetupEmail;'
AUTH = 'Lorg/telegram/tgnet/TLRPC$auth_SentCode;'
RESEND = 'Lorg/telegram/tgnet/TLRPC$TL_auth_resendCode;'
SIGNUP = 'Lorg/telegram/tgnet/TLRPC$TL_auth_authorizationSignUpRequired;'
EXTENSION = 'Lapp/template/extension/telegram/EmailAlternative;'
TARGETS = {
    (LOGIN, 'fillNextCodeParams', '(Landroid/os/Bundle;Lorg/telegram/tgnet/TLRPC$auth_SentCode;Z)V'): 'observe',
    (SETUP, 'setParams', '(Landroid/os/Bundle;Z)V'): 'install',
}
REQUIRED = {
    LOGIN, SETUP, AUTH, RESEND, SIGNUP,
    'Lorg/telegram/tgnet/TLRPC$TL_auth_sentCode;',
    'Lorg/telegram/tgnet/TLRPC$TL_auth_sentCodePaymentRequired;',
    'Lorg/telegram/tgnet/TLRPC$TL_auth_sentCodeSuccess;',
    'Lorg/telegram/tgnet/TLRPC$TL_auth_sentCodeTypeSetUpEmailRequired;',
    'Lorg/telegram/tgnet/TLRPC$TL_auth_codeTypeSms;',
    'Lorg/telegram/tgnet/TLRPC$TL_auth_codeTypeFlashCall;',
    'Lorg/telegram/tgnet/TLRPC$TL_auth_codeTypeCall;',
    'Lorg/telegram/tgnet/TLRPC$TL_auth_codeTypeMissedCall;',
    'Lorg/telegram/tgnet/TLRPC$TL_auth_authorization;',
    'Lorg/telegram/tgnet/RequestDelegate;',
    'Lorg/telegram/tgnet/ConnectionsManager;',
}
EXPECTED_FIELDS = {
    LOGIN: {('activityMode', 'I'), ('currentViewNum', 'I'),
            ('currentTermsOfService', 'Lorg/telegram/tgnet/TLRPC$TL_help_termsOfService;')},
    SETUP: {('this$0', LOGIN), ('currentParams', 'Landroid/os/Bundle;'), ('nextPressed', 'Z')},
    AUTH: {('flags', 'I'), ('type', 'Lorg/telegram/tgnet/TLRPC$auth_SentCodeType;'),
           ('next_type', 'Lorg/telegram/tgnet/TLRPC$auth_CodeType;'), ('timeout', 'I'),
           ('phone_code_hash', 'Ljava/lang/String;'),
           ('authorization', 'Lorg/telegram/tgnet/TLRPC$auth_Authorization;')},
    RESEND: {('phone_number', 'Ljava/lang/String;'), ('phone_code_hash', 'Ljava/lang/String;')},
    SIGNUP: {('terms_of_service', 'Lorg/telegram/tgnet/TLRPC$TL_help_termsOfService;')},
}


def inspect(path: Path, patched: bool) -> dict:
    wanted = REQUIRED | ({EXTENSION} if patched else set())
    seen, fields, methods = set(), {}, {}
    with zipfile.ZipFile(path) as archive:
        names = sorted(n for n in archive.namelist() if re.fullmatch(r'classes\d*\.dex', n))
        if not names:
            raise ValueError('No DEX in APK')
        for name in names:
            dex = DEX(archive.read(name))
            for cls in dex.get_classes():
                owner = cls.get_name()
                if owner not in wanted:
                    continue
                if owner in seen:
                    raise ValueError('Duplicate required class: ' + owner)
                seen.add(owner)
                if owner in EXPECTED_FIELDS:
                    fields[owner] = {(f.get_name(), f.get_descriptor()) for f in cls.get_fields()}
                if owner in (LOGIN, SETUP):
                    for method in cls.get_methods():
                        key = (owner, method.get_name(), method.get_descriptor().replace(' ', ''))
                        if key in TARGETS:
                            if method.get_code() is None:
                                raise ValueError('Hook target has no implementation: ' + str(key))
                            methods[key] = {
                                'registers': method.get_code().get_registers_size(),
                                'insns': [(ins.get_name(), ins.get_output()) for ins in method.get_instructions()],
                            }
            del dex
            gc.collect()
            if wanted.issubset(seen):
                break
    missing = wanted - seen
    if missing:
        raise ValueError('Required runtime class absent: ' + ', '.join(sorted(missing)))
    for owner, expected in EXPECTED_FIELDS.items():
        if not expected.issubset(fields.get(owner, set())):
            raise ValueError('Missing runtime fields in ' + owner + ': ' + str(expected - fields.get(owner, set())))
    if set(methods) != set(TARGETS):
        raise ValueError('Could not resolve both exact login methods')
    return methods


def compare(original: dict, patched: dict) -> None:
    for key, hook in TARGETS.items():
        before, after = original[key], patched[key]
        if before['registers'] != after['registers']:
            raise ValueError('Changed register count for ' + str(key))
        insns = after['insns']
        if not insns or not insns[0][0].startswith('invoke-static') or EXTENSION + '->' + hook + '(' not in insns[0][1]:
            raise ValueError('Missing first-instruction runtime hook ' + hook)
        if [x[0] for x in before['insns']] != [x[0] for x in insns[1:]]:
            raise ValueError('Original login control-flow opcodes changed beyond hook: ' + str(key))


def main() -> None:
    if len(sys.argv) != 5:
        raise SystemExit('usage: verify_apk.py original.apk experiment-only.apk defaults-plus-experiment.apk report.json')
    original, single, combined, output = map(Path, sys.argv[1:])
    stock = inspect(original, False)
    compare(stock, inspect(single, True))
    compare(stock, inspect(combined, True))
    report = {
        'exact_login_reflection_fields': 'passed_static_dex_check',
        'server_response_and_add_email_hooks': 'passed_single_and_default_plus_experiment',
        'original_login_method_opcodes_after_hook': 'unchanged',
        'server_login_and_real_device': 'not_tested',
        'sample': 'Telegram Web 12.10.1, original Telegram signature verified separately',
    }
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
