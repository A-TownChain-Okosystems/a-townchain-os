# Copyright (c) 2026 Michael Wroblewski / ShivaCore / A-TownChain-Okosystems. All Rights Reserved.
"""
ATC-95 — ATCLang Test Framework
ATC-98 — Testing Standard

Gemeinsames Test-Harness fuer .atc-Contracts: kompiliert Quelltext,
fuehrt ihn in der ATCVM aus und stellt Assertion-Helfer bereit, damit
jeder neue ATC-Standard sofort einen Unit-Test bekommt (ATC-98 Pflicht).
"""
from atclang.compiler.compiler import compile_source
from atclang.vm.atcvm import ATCVM, ATCFunction


class ATCTestCase:
    """Basis-Klasse fuer ATCLang-Contract-Tests (ATC-95/ATC-98 Standard)."""

    def compile_and_run(self, source: str, entry: str = None):
        module = compile_source(source)
        vm = ATCVM()
        for fname, instrs in module.functions.items():
            params = module.function_params.get(fname, [])
            vm.register_function(ATCFunction(name=fname, params=params, instructions=instrs))
        if entry and entry in module.functions:
            return vm.execute(module.functions[entry]), vm
        main_instrs = module.instructions if len(module.instructions) > 1 else (
            list(module.functions.values())[0] if module.functions else module.instructions
        )
        return vm.execute(main_instrs), vm

    def assert_atc_result(self, source: str, expected, entry: str = None):
        result, _ = self.compile_and_run(source, entry)
        assert result == expected, f"ATC-Test fehlgeschlagen: erwartet {expected}, erhalten {result}"
        return True

    def assert_compiles(self, source: str) -> bool:
        """ATC-98 Minimal-Pflichttest: Quelltext muss fehlerfrei kompilieren."""
        compile_source(source)
        return True


def run_standard_test(standard_id: str, source: str, expected=None) -> dict:
    """Fuehrt den ATC-98-Pflichttest fuer einen Standard aus und gibt ein Report-Dict zurueck."""
    tc = ATCTestCase()
    report = {"standard": standard_id, "compiled": False, "result_ok": None}
    try:
        result, _ = tc.compile_and_run(source)
        report["compiled"] = True
        if expected is not None:
            report["result_ok"] = (result == expected)
    except Exception as e:
        report["error"] = str(e)
    return report
