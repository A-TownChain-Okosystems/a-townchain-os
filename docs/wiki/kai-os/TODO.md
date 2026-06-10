# TODO — A-TownChain OS & KAI-OS

> Auto-Sync: 2026-06-10 05:42 UTC | 8 offen | 14 erledigt

---

## Priorität HIGH (1 Issues)

- [ ] **#8** 🌐 Multi-Node Testnet — P2P Netzwerk live schalten
  - [ ] `blockchain/nodes/discovery.py` — Node-Discovery via UDP Broadcast
  - [ ] Bekannte Bootstrap-Nodes in `config/settings.json` hinterlegen
  - [ ] Node-Handshake Protokoll (Versionsprüfung, Chain-Height Abgleich)
  - [ ] Persistente Peer-Liste (wird bei Neustart geladen)
  - [ ] `broadcast_block()` — neuer Block wird an alle Peers gesendet
  - [ ] `broadcast_tx()` — neue TX wird ins Netzwerk propagiert
  - [ ] Orphan-Block Handling (Fork-Auflösung)
  - [ ] Longest-Chain-Rule implementieren
  - [ ] Initial Sync: neuer Node lädt Chain von Peers
  - [ ] `sync_from_peer(peer_address)` — Chain-Download
  - [ ] Checkpoint-System (vertrauenswürdige Block-Hashes)
  - [ ] Docker Compose: 5 Nodes lokal starten
  - [ ] Monitoring-Dashboard im ShivaOS (Node-Status live)
  - [ ] Faucet-Endpoint: Test-ATC anfordern


---

## Priorität MEDIUM (6 Issues)

- [ ] **#19** 📊 [Testnet] Node-Monitoring Dashboard
  - [ ] Node-Monitor Seite in `frontend/index.html` (Sidebar: `🌐 Nodes`)
  - [ ] Node-Karten: ID · Typ · Online/Offline · Peers · Chain-Height · Mempool
  - [ ] Live-Refresh alle 5 Sekunden
  - [ ] Netzwerk-Graph: Nodes als Knoten, Verbindungen als Kanten (D3.js oder Canvas)
  - [ ] Mining-Rate: Blöcke pro Minute
  - [ ] Globale Netzwerk-Stats: Total Nodes · Total Stake · Avg Block Time
  - [ ] Node registrieren via UI-Formular
  - [ ] Alle Nodes live sichtbar mit Status
  - [ ] Offline-Nodes werden rot markiert
  - [ ] Netzwerk-Graph zeigt Verbindungen
  - [ ] Auto-Refresh ohne Flackern
- [ ] **#18** 🐳 [Testnet] Docker Compose — 5-Node lokales Netzwerk
  - [ ] `Dockerfile` für A-TownChain OS Backend
  - [ ] `docker-compose.testnet.yml` — 5 Service-Definitionen
  - [ ] Umgebungsvariablen pro Node (NODE_ID, NODE_TYPE, STAKE, BOOTSTRAP)
  - [ ] Shared Volume für Block-Daten (optional)
  - [ ] Healthcheck pro Service
  - [ ] `scripts/testnet-start.sh` — Convenience-Script
  - [ ] `scripts/testnet-stop.sh`
  - [ ] `scripts/testnet-faucet.sh <address>` — 100 Test-ATC senden
  - [ ] `docker-compose up` startet alle 5 Nodes fehlerfrei
  - [ ] Alle Nodes finden sich gegenseitig
  - [ ] Miner mint Blöcke, Validator bestätigt, alle synchronisieren
  - [ ] Faucet-Script sendet Test-ATC erfolgreich
- [ ] **#13** 🛒 ATC Marketplace — Shivamon kaufen & verkaufen
  - [ ] `blockchain/contracts/marketplace/marketplace_contract.py`
  - [ ] `list_for_sale(token_id, seller, price_atc)` — NFT listen
  - [ ] `buy(token_id, buyer)` — NFT kaufen (ATC-Transfer + NFT-Transfer)
  - [ ] `cancel_listing(token_id, seller)` — Listing entfernen
  - [ ] `make_offer(token_id, buyer, offer_price)` — Gegenangebot
  - [ ] Marktplatz-Fee: 2.5% pro Trade → ATC-Treasury
  - [ ] Auktions-Modus: zeitbasierte Höchstgebots-Auktion
  - [ ] `backend/api/routes/marketplace_routes.py`
  - [ ] `GET /api/marketplace/listings` — alle aktiven Listings
  - [ ] `GET /api/marketplace/listings?element=Neon&rarity=Rare` — Filter
  - [ ] `POST /api/marketplace/list` — NFT listen
  - [ ] `POST /api/marketplace/buy` — NFT kaufen
  - [ ] `GET /api/marketplace/stats` — Volumen, Floor Price, Top Sales
  - [ ] Marketplace-Seite im Dashboard (Sidebar: `🛒 Market`)
  - [ ] NFT-Grid mit Preis, Element, Rarity, Stats-Preview
  - [ ] Filter: Element · Rarity · Preis-Range · Level
  - [ ] Eigene Listings verwalten
  - [ ] Kauf-Flow: Bestätigung → ATC-Abzug → NFT-Transfer → Bestätigung
  - [ ] Floor Price pro Element
  - [ ] 24h Handelsvolumen in ATC
  - [ ] Top-10 teuerste Shivamon
- [ ] **#12** ⛓ Solidity Smart Contracts — On-Chain ATC Token
  - [ ] `blockchain/contracts/solidity/ATCToken.sol` — ERC20 (ATC-8300)
  - [ ] `blockchain/contracts/solidity/Shivamon.sol` — ERC721 (ATC-9000)
  - [ ] `blockchain/contracts/solidity/ATCGovernance.sol` — Voting (ATC-9900)
  - [ ] `blockchain/contracts/solidity/GenesisToken.sol` — ATC-001
  - [ ] Hardhat / Foundry Setup in `blockchain/contracts/solidity/`
  - [ ] Deployment Scripts für Testnet
  - [ ] ABI-Export für Backend-Integration
  - [ ] Unit Tests (Coverage > 90%)
  - [ ] Backend liest Contract-State via Web3.py
  - [ ] `backend/api/routes/blockchain.py` — On-Chain Queries
  - [ ] ABI-Dateien in `config/abis/`
- [ ] **#11** 🥚 Shivamon Breeding — Gen 2 NFT Züchtung
  - [ ] `ShivamonContract.breed(parent1_id, parent2_id, owner)` implementieren
  - [ ] DNA-Mixing: Kind-DNA = SHA-256(parent1.dna + parent2.dna + timestamp)
  - [ ] Stat-Vererbung: 50/50 Mix beider Eltern-Stats + zufällige Mutation (±10%)
  - [ ] Element-Vererbung: dominant (70%) / rezessiv (30%) — oder neues Hybrid-Element
  - [ ] Rarity-Formel: Kind-Rarity basiert auf Eltern-Rarities
  - [ ] Cooldown: jedes Shivamon kann nur alle 24h züchten
  - [ ] Breeding-Kosten: 25 ATC
  - [ ] Gen 1: native gemintete Shivamon (aktuell)
  - [ ] Gen 2: erste Breeding-Generation
  - [ ] Gen N: Stats wachsen mit Generation (base + generation × 5)
  - [ ] Max Generation: 10 (danach kein weiteres Breeding)
  - [ ] `POST /api/game/shivamon/breed` — Breeding starten
  - [ ] `GET /api/game/shivamon/:id/breeding-status` — Cooldown prüfen
  - [ ] Breeding-Interface im Shivamon-Tab
  - [ ] Parent-Auswahl aus eigener Collection
  - [ ] Preview der möglichen Kind-Stats
  - [ ] Cooldown-Timer Anzeige
- [ ] **#7** 📦 Build System — EXE / AppImage Installer
  - [ ] `build/build.py` — PyInstaller Config ausbauen
  - [ ] Single-File EXE: Gateway + Backend + Frontend gebündelt
  - [ ] Auto-Start: Gateway bootet beim EXE-Start
  - [ ] Embedded Browser (CEF / Electron Alternative)
  - [ ] Windows Installer (NSIS oder Inno Setup)
  - [ ] Linux AppImage
  - [ ] GitHub Actions CI/CD — automatischer Build bei Tag


---

## Priorität LOW / Nicht klassifiziert

- [ ] **#10** 🌉 Cross-Chain Bridge — ATC ↔ EVM Interoperabilität
  - [ ] `blockchain/bridge/bridge_contract.py` — Lock/Mint Mechanismus
  - [ ] Lock-Contract auf A-TownChain: ATC einfrieren
  - [ ] Mint-Contract auf EVM: Wrapped ATC (wATC) ausgeben
  - [ ] Relayer-Service: überwacht beide Chains und löst Mint/Burn aus
  - [ ] `bridge/relayer.py` — Event-Listener + TX-Sender
  - [ ] Ethereum Sepolia Testnet
  - [ ] Polygon Mumbai Testnet
  - [ ] BSC Testnet
  - [ ] Multi-Sig Relayer (mind. 3/5 Signaturen)
  - [ ] Rate Limiting: max. 10.000 ATC pro Bridge-TX
  - [ ] Timelock: 24h Verzögerung bei großen Transfers (> 100.000 ATC)
  - [ ] Emergency Pause Funktion
  - [ ] `POST /api/bridge/lock` — ATC auf A-TownChain einfrieren
  - [ ] `GET /api/bridge/status/:tx_id` — Bridge-TX Status
  - [ ] `GET /api/bridge/stats` — Gesamt-TVL (Total Value Locked)
  - [ ] Bridge-Interface im Dashboard (Sidebar: `🌉 Bridge`)
  - [ ] Chain-Selector (ATC ↔ ETH / ATC ↔ MATIC)
  - [ ] Status-Tracker für laufende Bridge-Transaktionen


---

## Erledigt (letzte 8)

- [x] **#22** 🚀 KAI-OS v1.3.2-beta — Substrate-Integration + DevOps-Automatisierung
- [x] **#21** build(deps): Bump flask-cors from 4.0.1 to 6.0.0
- [x] **#20** 🧪 API-Gateway-Tests — Unit & Integrationstests für Port 4000
- [x] **#17** ⛓ [Testnet] Longest-Chain-Rule — Fork-Auflösung
- [x] **#16** 🔄 [Testnet] Initial Sync — Neue Nodes synchronisieren
- [x] **#15** 📡 [Testnet] Block Propagation — P2P Block Broadcasting
- [x] **#14** 🌐 [Testnet] Bootstrap Node — P2P Discovery Service
- [x] **#9** 🏛 Governance Contract (ATC-9900) — DAO Voting


---

*Auto-generiert von KAI-OS Sync Agent — 2026-06-10 05:42 UTC*
