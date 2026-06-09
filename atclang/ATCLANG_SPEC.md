# ATCLang — Vollständige Sprachspezifikation

> Version: 0.2.0 | Stand: 2026-06-09 | KAI-OS Wiki
> Status: Aktiv entwickelt (Sprint 2.5)

---

## 1. Übersicht

ATCLang ist die native Programmiersprache des A-TownChain Ökosystems. Sie ist speziell für Blockchain-Anwendungen, Smart Contracts und KI-Agenten-Interaktionen designed.

### Eigenschaften

| Eigenschaft | Beschreibung |
|-------------|-------------|
| Paradigma | Imperativ + Contract-Oriented |
| Typsystem | Statisch typisiert |
| Ausführung | Stack-basierte VM (ATCVM) |
| Ziel-Plattform | A-TownChain Blockchain + KAI-OS |
| Dateiendung | .atc |
| Version | 0.2.0-alpha |

---

## 2. Architektur der Toolchain

```
Quellcode (.atc)
     |
  [Lexer]          -> Token-Stream
     |
  [Parser]         -> AST (Abstract Syntax Tree)
     |
  [Compiler]       -> Bytecode (Instruction-Liste)
     |
  [ATCVM]          -> Ausführung
     |
  [Blockchain]     -> Events + State-Änderungen on-chain
```

### Dateien

| Datei | Beschreibung | Zeilen |
|-------|-------------|--------|
| atclang/lexer/lexer.py | Tokenizer | 272 |
| atclang/parser/ast_nodes.py | AST-Knoten-Definitionen | 130 |
| atclang/parser/parser.py | Recursive-Descent Parser | 376 |
| atclang/compiler/compiler.py | Bytecode-Compiler | 455 |
| atclang/vm/atcvm.py | Stack-VM + Opcodes | 330 |
| atclang/repl/repl.py | Interaktive Shell | 158 |

---

## 3. Lexer

### 3.1 Keywords (51 Schlüsselwörter)

```
wallet    contract   fn        state     emit      require
return    if         else      elif      for       while
in        import     from      as        let       const
pub       priv       self      caller    block     tx
deploy    call       event     error     true      false
null      break      continue  struct    enum      impl
trait     new        delete    async     await     node
consensus genesis    mint      burn      stake     unstake
vote
```

### 3.2 Typen (22 eingebaute Typen)

```
UInt8    UInt16    UInt32    UInt64    UInt256
Int8     Int16     Int32     Int64
Bool     String    Address   Hash256   Bytes
Map      List      Set       Option    Result
ATC8300  ATC9000   ATCContract ATCWallet
```

### 3.3 Operatoren

| Operator | Bedeutung |
|----------|-----------|
| + - * / % | Arithmetik |
| == != < > <= >= | Vergleich |
| && \|\| ! | Logik |
| = | Zuweisung |
| := | Deklaration + Zuweisung |
| -> | Rückgabetyp |
| :: | Namespace (ATC::Wallet::new) |
| . | Feldzugriff |
| @decorator | Decorator |

---

## 4. Parser & AST

### 4.1 AST-Knoten

```python
# Vollständige AST-Knoten-Liste

# Programme
Program             # Root-Knoten
ImportStmt          # import ATC::Wallet

# Deklarationen
FunctionDef         # fn transfer(to: Address) -> Bool { ... }
ContractDef         # contract ShivaToken : ATC-8300 { ... }
StructDef           # struct Player { name: String, hp: UInt16 }
EventDef            # event Transfer(from: Address, to: Address)
StateDef            # state balance: Map<Address, UInt256>

# Statements
LetStmt             # let x: UInt256 = 100
AssignStmt          # x = 200
IfStmt              # if x > 0 { ... } else { ... }
ForStmt             # for item in list { ... }
WhileStmt           # while condition { ... }
ReturnStmt          # return value
EmitStmt            # emit Transfer(caller, to, amount)
RequireStmt         # require(balance >= amount)
ExprStmt            # Ausdruck als Statement

# Expressions
BinaryOp            # a + b, x == y
UnaryOp             # !flag, -number
IntLiteral          # 42, 1_000_000
FloatLiteral        # 3.14
StringLiteral       # "hallo"
BoolLiteral         # true / false
Identifier          # variablenname
CallExpr            # fn_name(arg1, arg2)
MethodCallExpr      # obj.method(args)
IndexExpr           # map[key], list[0]
FieldAccessExpr     # obj.field
NamespacedExpr      # ATC::Wallet::new(...)
```

### 4.2 Beispiel: AST für Transfer-Funktion

```
FunctionDef(
  name="transfer",
  params=[("to", "Address"), ("amount", "UInt256")],
  return_type="Bool",
  body=[
    RequireStmt(
      BinaryOp(">=", IndexExpr(Identifier("balance"), Identifier("caller")), Identifier("amount"))
    ),
    AssignStmt(
      IndexExpr(Identifier("balance"), Identifier("caller")),
      BinaryOp("-", IndexExpr(...), Identifier("amount"))
    ),
    EmitStmt("Transfer", [Identifier("caller"), Identifier("to"), Identifier("amount")]),
    ReturnStmt(BoolLiteral(true))
  ]
)
```

---

## 5. VM: Opcodes

### 5.1 Alle 43 Opcodes

| Gruppe | Opcode | Beschreibung |
|--------|--------|-------------|
| **Stack** | PUSH val | Wert auf Stack legen |
| | POP | Oberstes Element entfernen |
| | DUP | Stack-Top duplizieren |
| | SWAP | Obere zwei tauschen |
| **Arithmetik** | ADD / SUB / MUL / DIV / MOD | Grundrechenarten |
| | NEG | Negation (-x) |
| **Vergleich** | EQ / NEQ / LT / GT / LTE / GTE | Vergleiche (Bool-Ergebnis) |
| **Logik** | AND / OR / NOT | Boolsche Operationen |
| **Variablen** | LOAD name | Variable auf Stack laden |
| | STORE name | Stack-Top in Variable speichern |
| | LOAD_IDX | Map/List[key] laden |
| | STORE_IDX | Map/List[key] = val setzen |
| **Sprünge** | JUMP offset | Unbedingter Sprung |
| | JUMP_IF offset | Sprung wenn Top == True |
| | JUMP_NOT offset | Sprung wenn Top == False |
| **Funktionen** | CALL name argc | Funktion aufrufen |
| | RETURN | Rückkehr mit Stack-Top |
| | CALL_EXT name | Externe ATC-Funktion |
| **ATC-Spezifisch** | EMIT event argc | Blockchain-Event auslösen |
| | REQUIRE msg | Assertion (wirft Fehler wenn false) |
| | TRANSFER | ATC-Token transferieren |
| | MINT | Token minten |
| | BURN | Token burnen |
| **Objekte** | NEW_MAP | Leere Map {} erstellen |
| | NEW_LIST | Leere Liste [] erstellen |
| | GET_FIELD name | obj.field laden |
| | SET_FIELD name | obj.field = val setzen |
| **System** | HALT | Ausführung stoppen |
| | NOP | Keine Operation |
| | PRINT | Debug-Ausgabe |

### 5.2 Gas-Kosten

| Opcode-Gruppe | Gas pro Aufruf |
|---------------|----------------|
| PUSH, POP, DUP, SWAP | 1 |
| ADD, SUB, MUL | 3 |
| DIV, MOD | 5 |
| EQ, NEQ, LT, GT, LTE, GTE | 3 |
| LOAD, STORE | 3 |
| LOAD_IDX, STORE_IDX | 5 |
| CALL | 50 |
| EMIT | 100 |
| REQUIRE | 5 |
| MINT, BURN | 500 |
| TRANSFER | 200 |

**Gas-Limit Standard:** 1.000.000 Gas pro Transaktion

---

## 6. Vollständige Syntax-Referenz

### 6.1 Variablen

```atclang
// Unveränderlich
const MAX_SUPPLY: UInt256 = 1_000_000_000

// Veränderlich
let counter: UInt32 = 0

// Typen können inferiert werden
let name = "ShivaCore"   // Typ: String
let amount = 100         // Typ: UInt64 (default Int)
```

### 6.2 Funktionen

```atclang
// Einfache Funktion
fn add(a: UInt256, b: UInt256) -> UInt256 {
    return a + b
}

// Öffentliche Funktion (callable von extern)
pub fn get_balance(addr: Address) -> UInt256 {
    return state.balance[addr]
}

// Interne Funktion
priv fn _validate(amount: UInt256) -> Bool {
    require(amount > 0)
    return true
}

// Async-Funktion (für off-chain Calls)
async fn fetch_price(token: String) -> UInt256 {
    // Ruft Oracle-Vertrag auf
    return await ATC::Oracle::get_price(token)
}
```

### 6.3 Contracts

```atclang
// Contract erbt von ATC-8300 (Fungible Token Standard)
contract ATCToken : ATC-8300 {

    // State-Variablen (persistiert on-chain)
    state balance: Map<Address, UInt256>
    state allowance: Map<Address, Map<Address, UInt256>>
    state total_supply: UInt256 = 0

    // Events
    event Transfer(from: Address, to: Address, amount: UInt256)
    event Approval(owner: Address, spender: Address, amount: UInt256)

    // Konstruktor
    fn init(initial_supply: UInt256) {
        balance[caller] = initial_supply
        total_supply = initial_supply
        emit Transfer("0x0", caller, initial_supply)
    }

    pub fn transfer(to: Address, amount: UInt256) -> Bool {
        require(balance[caller] >= amount, "Nicht genug Balance")
        require(to != "0x0", "Ungültige Adresse")
        balance[caller] -= amount
        balance[to] += amount
        emit Transfer(caller, to, amount)
        return true
    }

    pub fn approve(spender: Address, amount: UInt256) -> Bool {
        allowance[caller][spender] = amount
        emit Approval(caller, spender, amount)
        return true
    }

    pub fn transfer_from(from: Address, to: Address, amount: UInt256) -> Bool {
        require(allowance[from][caller] >= amount, "Nicht genehmigt")
        require(balance[from] >= amount, "Nicht genug Balance")
        allowance[from][caller] -= amount
        balance[from] -= amount
        balance[to] += amount
        emit Transfer(from, to, amount)
        return true
    }
}
```

### 6.4 Shivamon NFT Contract

```atclang
contract ShivamonNFT : ATC-9000 {

    state owners: Map<UInt256, Address>
    state token_count: UInt256 = 0
    state metadata: Map<UInt256, String>   // IPFS-CID

    // Shivamon-spezifische Attribute
    state stats: Map<UInt256, ShivamonStats>

    struct ShivamonStats {
        name: String
        element: String
        level: UInt8
        hp: UInt16
        attack: UInt16
        defense: UInt16
        speed: UInt16
        rarity: String
        generation: UInt8
        dna: Hash256
    }

    event Mint(to: Address, token_id: UInt256, name: String)
    event Transfer(from: Address, to: Address, token_id: UInt256)
    event LevelUp(token_id: UInt256, new_level: UInt8)

    pub fn mint(to: Address, name: String, element: String, ipfs_cid: String) -> UInt256 {
        let token_id = token_count
        token_count += 1
        owners[token_id] = to
        metadata[token_id] = ipfs_cid

        // Basis-Stats generieren (deterministisch aus token_id)
        stats[token_id] = ShivamonStats {
            name: name,
            element: element,
            level: 1,
            hp: 50 + (token_id % 50),
            attack: 10 + (token_id % 30),
            defense: 10 + (token_id % 25),
            speed: 10 + (token_id % 20),
            rarity: "Common",
            generation: 1,
            dna: ATC::Hash::blake2b(token_id)
        }

        emit Mint(to, token_id, name)
        return token_id
    }

    pub fn transfer(to: Address, token_id: UInt256) -> Bool {
        require(owners[token_id] == caller, "Nicht der Besitzer")
        require(to != "0x0", "Ungültige Adresse")
        owners[token_id] = to
        emit Transfer(caller, to, token_id)
        return true
    }
}
```

### 6.5 Kontrollfluss

```atclang
// If-Else
if balance[caller] > 1000 {
    emit Premium(caller)
} elif balance[caller] > 100 {
    emit Standard(caller)
} else {
    emit Basic(caller)
}

// For-Schleife
for token_id in token_list {
    let owner = owners[token_id]
    emit TokenInfo(token_id, owner)
}

// While-Schleife
let i: UInt32 = 0
while i < 10 {
    counter += 1
    i += 1
}

// Break / Continue
for item in items {
    if item == null { continue }
    if item == target { break }
    process(item)
}
```

### 6.6 Structs

```atclang
struct Player {
    address: Address
    name: String
    level: UInt8
    xp: UInt64
    wins: UInt32
    losses: UInt32
}

fn create_player(name: String) -> Player {
    return Player {
        address: caller,
        name: name,
        level: 1,
        xp: 0,
        wins: 0,
        losses: 0
    }
}
```

### 6.7 Imports & Namespaces

```atclang
// Eingebaute ATC-Bibliotheken
import ATC::Wallet
import ATC::Math
import ATC::Hash
import ATC::Time
import ATC::Oracle

// Andere Contracts
import contracts::ATCToken
import contracts::ShivamonNFT

// Verwendung
let hash = ATC::Hash::blake2b("input")
let timestamp = ATC::Time::now()
let price = ATC::Oracle::get_price("ATC/USDT")
```

---

## 7. Standard-Bibliothek (ATC:: Namespace)

### ATC::Wallet

```atclang
ATC::Wallet::new(name: String)          -> Wallet
ATC::Wallet::balance(addr: Address)     -> UInt256
ATC::Wallet::transfer(to: Address, amount: UInt256) -> Bool
ATC::Wallet::sign(data: Hash256)        -> Bytes
ATC::Wallet::verify(sig: Bytes, data: Hash256, addr: Address) -> Bool
```

### ATC::Math

```atclang
ATC::Math::min(a: UInt256, b: UInt256) -> UInt256
ATC::Math::max(a: UInt256, b: UInt256) -> UInt256
ATC::Math::sqrt(x: UInt256)            -> UInt256
ATC::Math::pow(base: UInt256, exp: UInt256) -> UInt256
ATC::Math::abs(x: Int256)              -> UInt256
```

### ATC::Hash

```atclang
ATC::Hash::blake2b(data: String)  -> Hash256
ATC::Hash::sha256(data: String)   -> Hash256
ATC::Hash::keccak256(data: String) -> Hash256  // EVM-kompatibel
```

### ATC::Time

```atclang
ATC::Time::now()          -> UInt64   // Unix-Timestamp
ATC::Time::block_time()   -> UInt64   // Block-Timestamp
ATC::Time::block_num()    -> UInt64   // Aktuelle Block-Höhe
```

### ATC::Oracle

```atclang
ATC::Oracle::get_price(pair: String) -> UInt256   // z.B. "ATC/USDT"
ATC::Oracle::get_random(seed: Hash256) -> UInt256 // VRF-basiert
```

---

## 8. Fehlerbehandlung

```atclang
// require() — wirft Fehler wenn Bedingung false
require(amount > 0, "Betrag muss positiv sein")
require(balance[caller] >= amount, "Nicht genug Balance")
require(caller == owner, "Nur Owner erlaubt")

// error — benannte Fehlertypen
error InsufficientBalance(address: Address, required: UInt256)
error Unauthorized(caller: Address)
error InvalidAmount(amount: UInt256)

// Fehler auslösen
fn transfer(to: Address, amount: UInt256) -> Bool {
    if balance[caller] < amount {
        emit InsufficientBalance(caller, amount)
        return false
    }
    // ...
}
```

---

## 9. Was noch fehlt / Roadmap

### 9.1 Implementiert (v0.1.0)

| Feature | Status |
|---------|--------|
| Lexer: alle Token-Typen | ✅ |
| Parser: Expressions, Statements | ✅ |
| Parser: Contract, Function | ✅ |
| Compiler: Expressions -> Bytecode | ✅ |
| Compiler: if/else/while/for | ✅ |
| Compiler: Funktionen | ✅ |
| VM: alle 43 Opcodes | ✅ |
| VM: Gas-Metering | ✅ |
| VM: Events (EMIT) | ✅ |
| REPL: Interaktive Shell | ✅ |

### 9.2 Fehlt / Geplant (v0.2.0 — Sprint 2.5)

| Feature | Priorität | Sprint |
|---------|-----------|--------|
| Unit-Tests (test_atclang.py) | HOCH | 2.5 |
| Type-Checker (statische Typen prüfen) | HOCH | 2.5 |
| Structs im Compiler | HOCH | 2.5 |
| Standard-Bibliothek ATC:: (Implementierung) | HOCH | 2.5 |
| Imports zwischen Contracts | MITTEL | 2.6 |
| Async/Await (off-chain calls) | MITTEL | 3.1 |
| Generics (Map<K,V> zur Laufzeit) | MITTEL | 3.1 |
| Enums mit Daten | MITTEL | 3.2 |
| Pattern Matching (match/case) | NIEDRIG | 3.3 |
| Closures / Lambda | NIEDRIG | 3.4 |
| Substrate-Ink! Transpiler | HOCH | 3.5 |
| VS Code Extension (Syntax-Highlighting) | NIEDRIG | 4.1 |
| Language Server Protocol (LSP) | NIEDRIG | 4.2 |

---

## 10. REPL-Verwendung

```bash
# ATCLang REPL starten
python3 -m atclang.repl

ATCLang REPL v0.1.0 — Typ 'help' fuer Hilfe

>>> let x: UInt256 = 100
>>> let y: UInt256 = 200
>>> x + y
300

>>> fn double(n: UInt256) -> UInt256 { return n * 2 }
Funktion 'double' definiert

>>> double(21)
42

>>> :load my_contract.atc
Geladen: my_contract.atc

>>> :compile
Kompiliert: 42 Instruktionen

>>> :run
Ausfuehren...
```

### REPL-Befehle

| Befehl | Beschreibung |
|--------|-------------|
| :load <datei> | ATCLang-Datei laden |
| :compile | Aktuellen Code kompilieren |
| :run | Kompilierten Code ausführen |
| :disasm | Bytecode anzeigen |
| :reset | VM zurücksetzen |
| :history | Eingabe-History anzeigen |
| :help | Hilfe anzeigen |
| :quit / :q | Beenden |

---

## 11. Compiler-Pipeline Beispiel

```python
from atclang.lexer.lexer import ATCLexer
from atclang.parser.parser import ATCParser
from atclang.compiler.compiler import ATCCompiler
from atclang.vm.atcvm import ATCVM

source = """
fn fib(n: UInt256) -> UInt256 {
    if n <= 1 { return n }
    return fib(n - 1) + fib(n - 2)
}
"""

# 1. Lexen
lexer = ATCLexer(source)
tokens = lexer.tokenize()

# 2. Parsen
parser = ATCParser(tokens)
ast = parser.parse()

# 3. Kompilieren
compiler = ATCCompiler()
module = compiler.compile_program(ast)

# 4. Ausführen
vm = ATCVM()
for func in module.functions.values():
    vm.register_function(func)
vm.globals['fib'] = lambda n: None  # placeholder
result = vm.execute(module.main_instructions)

# 5. Ergebnis
print(f"fib(10) = {result}")  # 55
print(f"Gas verbraucht: {vm.gas_used}")
```

---

*ATCLang Sprachspezifikation v0.2.0 | KAI-OS Wiki | 2026-06-09*
