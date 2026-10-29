"""Exercise the static APK comparison policy without needing an APK or Android."""
import ast
import copy
import unittest
from pathlib import Path

source = Path('tools/simsimi/verify_quick_apk.py')
module = ast.parse(source.read_text(), filename=str(source))
function = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == 'check_navigation')
BAR = 'Lcom/aurelhubert/ahbottomnavigation/i;'
CONTROLLER = 'Lcom/reactnativenavigation/viewcontrollers/bottomtabs/BottomTabsController;'
HANDLERS = ('lambda$createClassicItems$5', 'lambda$createSmallItems$6')
namespace = {'BAR': BAR, 'CONTROLLER': CONTROLLER, 'HANDLERS': HANDLERS}
exec(compile(ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[])), str(source), 'exec'), namespace)
check_navigation = namespace['check_navigation']


def stock():
    def method(*instructions):
        return {'registers': 3, 'instructions': list(instructions)}
    methods = {(BAR, name, '(ILandroid/view/View;)V'): method(('return-void', '')) for name in HANDLERS}
    methods[(BAR, 'setCurrentItem', '(I)V')] = method(('return-void', ''))
    methods[(BAR, 'setCurrentItem', '(IZ)V')] = method(('return-void', ''))
    methods[(CONTROLLER, 'onTabSelected', '(IZ)Z')] = method(('invoke-virtual', 'emitBottomTabPressed'))
    return {'methods': methods, 'quick_class': False, 'tap_class': False}


def hooked(original):
    result = copy.deepcopy(original)
    result.update(quick_class=True, tap_class=True)
    for key in result['methods']:
        if key[0] == BAR and key[1] in HANDLERS:
            result['methods'][key]['instructions'].insert(0, ('invoke-static', 'QuickReturn;->onTabClicked('))
    return result


class VerifyQuickApkTest(unittest.TestCase):
    def setUp(self):
        self.original = stock()
        self.patched = hooked(self.original)

    def test_selected_and_disabled(self):
        check_navigation(self.original, self.patched, True)
        check_navigation(self.original, self.original, False)

    def test_disabled_patch_must_not_hook(self):
        with self.assertRaises(AssertionError):
            check_navigation(self.original, self.patched, False)

    def test_programmatic_navigation_must_not_change(self):
        self.patched['methods'][(BAR, 'setCurrentItem', '(IZ)V')]['instructions'].insert(
            0, ('invoke-static', 'QuickReturn;->onTabClicked('))
        with self.assertRaises(AssertionError):
            check_navigation(self.original, self.patched, True)

    def test_original_click_instructions_must_survive(self):
        self.patched['methods'][(BAR, HANDLERS[0], '(ILandroid/view/View;)V')]['instructions'].pop()
        with self.assertRaises(AssertionError):
            check_navigation(self.original, self.patched, True)

    def test_hook_must_be_first_and_static(self):
        instructions = self.patched['methods'][(BAR, HANDLERS[0], '(ILandroid/view/View;)V')]['instructions']
        instructions.insert(0, instructions.pop())
        with self.assertRaises(AssertionError):
            check_navigation(self.original, self.patched, True)

    def test_extension_must_be_present(self):
        self.patched['quick_class'] = False
        with self.assertRaises(AssertionError):
            check_navigation(self.original, self.patched, True)

    def test_original_register_layout_must_survive(self):
        self.patched['methods'][(BAR, HANDLERS[1], '(ILandroid/view/View;)V')]['registers'] += 1
        with self.assertRaises(AssertionError):
            check_navigation(self.original, self.patched, True)


if __name__ == '__main__':
    unittest.main()
