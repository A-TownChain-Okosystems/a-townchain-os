"""
ATCLang v0.4.0 — Type Checker
Static type analysis for ATCLang programs.
Issue: #48 | Wiki: Kap. 36
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger("atclang.typechecker")


class ATCType(Enum):
    VOID    = "void"
    BOOL    = "bool"
    U8      = "u8"
    U32     = "u32"
    U64     = "u64"
    I32     = "i32"
    I64     = "i64"
    F64     = "f64"
    STRING  = "string"
    ADDRESS = "Address"
    BYTES   = "bytes"
    MAP     = "Map"
    VEC     = "Vec"
    ANY     = "any"
    UNKNOWN = "unknown"


@dataclass
class TypeInfo:
    base: ATCType
    generic_args: List["TypeInfo"] = field(default_factory=list)
    nullable: bool = False

    def __str__(self) -> str:
        if self.generic_args:
            args = ", ".join(str(a) for a in self.generic_args)
            return f"{self.base.value}<{args}>"
        return self.base.value


@dataclass
class TypeError:
    line: int
    col: int
    message: str
    severity: str = "error"  # error | warning

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] line {self.line}:{self.col} — {self.message}"


class TypeEnvironment:
    """Scope-aware type environment for variable and function types."""

    def __init__(self, parent: Optional["TypeEnvironment"] = None):
        self.parent = parent
        self._vars: Dict[str, TypeInfo] = {}
        self._funcs: Dict[str, tuple] = {}  # name -> (return_type, [param_types])

    def declare_var(self, name: str, type_info: TypeInfo):
        self._vars[name] = type_info

    def lookup_var(self, name: str) -> Optional[TypeInfo]:
        if name in self._vars:
            return self._vars[name]
        return self.parent.lookup_var(name) if self.parent else None

    def declare_func(self, name: str, return_type: TypeInfo, param_types: List[TypeInfo]):
        self._funcs[name] = (return_type, param_types)

    def lookup_func(self, name: str) -> Optional[tuple]:
        if name in self._funcs:
            return self._funcs[name]
        return self.parent.lookup_func(name) if self.parent else None

    def child(self) -> "TypeEnvironment":
        return TypeEnvironment(parent=self)


# Built-in types
BUILTINS = {
    "msg.sender":   TypeInfo(ATCType.ADDRESS),
    "msg.value":    TypeInfo(ATCType.U64),
    "block.number": TypeInfo(ATCType.U64),
    "block.hash":   TypeInfo(ATCType.BYTES),
    "tx.origin":    TypeInfo(ATCType.ADDRESS),
}

TYPE_MAP = {
    "void": ATCType.VOID, "bool": ATCType.BOOL,
    "u8": ATCType.U8, "u32": ATCType.U32, "u64": ATCType.U64,
    "i32": ATCType.I32, "i64": ATCType.I64, "f64": ATCType.F64,
    "string": ATCType.STRING, "Address": ATCType.ADDRESS,
    "bytes": ATCType.BYTES, "any": ATCType.ANY,
}


class TypeChecker:
    """
    ATCLang Static Type Checker.
    Walks the AST and validates types, returning a list of TypeErrors.
    """

    def __init__(self):
        self.errors: List[TypeError] = []
        self.warnings: List[TypeError] = []
        self._env = TypeEnvironment()
        self._current_contract: Optional[str] = None
        self._current_func_return: Optional[TypeInfo] = None
        # Seed built-ins
        for name, t in BUILTINS.items():
            self._env.declare_var(name, t)

    def check(self, ast: dict) -> List[TypeError]:
        """Type-check an AST. Returns list of errors."""
        self.errors = []
        self.warnings = []
        if isinstance(ast, dict):
            self._check_node(ast, self._env)
        return self.errors

    def _parse_type(self, type_str: str) -> TypeInfo:
        if not type_str:
            return TypeInfo(ATCType.UNKNOWN)
        base = TYPE_MAP.get(type_str.split("<")[0].strip(), ATCType.UNKNOWN)
        return TypeInfo(base=base)

    def _error(self, line: int, col: int, msg: str):
        self.errors.append(TypeError(line=line, col=col, message=msg))

    def _warn(self, line: int, col: int, msg: str):
        self.warnings.append(TypeError(line=line, col=col, message=msg, severity="warning"))

    def _check_node(self, node: dict, env: TypeEnvironment) -> Optional[TypeInfo]:
        ntype = node.get("type", "")

        if ntype == "Contract":
            self._current_contract = node.get("name")
            child_env = env.child()
            for field_node in node.get("fields", []):
                self._check_node(field_node, child_env)
            for func_node in node.get("functions", []):
                self._check_node(func_node, child_env)

        elif ntype == "StateField":
            field_type = self._parse_type(node.get("field_type", ""))
            env.declare_var(node.get("name", ""), field_type)

        elif ntype == "Function":
            ret_type = self._parse_type(node.get("return_type", "void"))
            param_types = [self._parse_type(p.get("type","")) for p in node.get("params",[])]
            fname = node.get("name","")
            env.declare_func(fname, ret_type, param_types)
            func_env = env.child()
            for p in node.get("params",[]):
                func_env.declare_var(p.get("name",""), self._parse_type(p.get("type","")))
            self._current_func_return = ret_type
            for stmt in node.get("body",[]):
                self._check_node(stmt, func_env)
            self._current_func_return = None

        elif ntype == "VarDecl":
            decl_type = self._parse_type(node.get("var_type",""))
            env.declare_var(node.get("name",""), decl_type)
            if "value" in node:
                val_type = self._check_node(node["value"], env)
                if val_type and decl_type.base != ATCType.ANY:
                    if val_type.base != decl_type.base and val_type.base != ATCType.UNKNOWN:
                        self._error(node.get("line",0), node.get("col",0),
                                    f"Type mismatch: expected {decl_type}, got {val_type}")

        elif ntype == "Assignment":
            var_type = env.lookup_var(node.get("name",""))
            val_type = self._check_node(node.get("value",{}), env)
            if var_type is None:
                self._error(node.get("line",0), node.get("col",0),
                            f"Undefined variable: {node.get('name')}")
            elif val_type and var_type.base != ATCType.ANY:
                if val_type.base != var_type.base and val_type.base != ATCType.UNKNOWN:
                    self._error(node.get("line",0), node.get("col",0),
                                f"Type mismatch in assignment to '{node.get('name')}': "
                                f"expected {var_type}, got {val_type}")

        elif ntype == "Return":
            val_type = self._check_node(node.get("value",{}), env)
            if self._current_func_return and val_type:
                if (self._current_func_return.base != ATCType.ANY and
                        val_type.base != self._current_func_return.base and
                        val_type.base != ATCType.UNKNOWN):
                    self._warn(node.get("line",0), node.get("col",0),
                               f"Return type mismatch: expected {self._current_func_return}, got {val_type}")

        elif ntype == "Identifier":
            resolved = env.lookup_var(node.get("name",""))
            if resolved is None:
                self._error(node.get("line",0), node.get("col",0),
                            f"Undefined identifier: {node.get('name')}")
            return resolved

        elif ntype == "IntLiteral":
            return TypeInfo(ATCType.U64)

        elif ntype == "StringLiteral":
            return TypeInfo(ATCType.STRING)

        elif ntype == "BoolLiteral":
            return TypeInfo(ATCType.BOOL)

        elif ntype == "FunctionCall":
            func_info = env.lookup_func(node.get("name",""))
            if func_info is None and node.get("name") not in ("require", "emit", "revert"):
                self._error(node.get("line",0), node.get("col",0),
                            f"Undefined function: {node.get('name')}")
                return TypeInfo(ATCType.UNKNOWN)
            for arg in node.get("args",[]):
                self._check_node(arg, env)
            return func_info[0] if func_info else TypeInfo(ATCType.VOID)

        return None

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def report(self) -> str:
        lines = []
        for e in self.errors:
            lines.append(str(e))
        for w in self.warnings:
            lines.append(str(w))
        if not lines:
            return "Type check passed: no errors."
        return "\n".join(lines)
