const { expect } = require("chai");
const { ethers }  = require("hardhat");

/**
 * GenesisToken.test.js — ATC-001 Ursprungs-Token
 * Tests: Deployment, Provenance, Lock, Verify, Metadaten
 */
describe("GenesisToken (ATC-001)", function () {

  let genesis;
  let owner, addr1, addr2;

  beforeEach(async function () {
    [owner, addr1, addr2] = await ethers.getSigners();

    const GenesisToken = await ethers.getContractFactory("GenesisToken");
    genesis = await GenesisToken.deploy();
    await genesis.waitForDeployment();
  });

  // ── 1. Deployment ─────────────────────────────────────
  describe("Deployment & Konstanten", function () {
    it("sollte korrekte Token-Konstanten haben", async function () {
      expect(await genesis.TOKEN_ID()).to.equal("ATC-001-GENESIS");
      expect(await genesis.NAME()).to.equal("A-TownChain Genesis Token");
      expect(await genesis.SYMBOL()).to.equal("ATC-001");
      expect(await genesis.TOTAL_SUPPLY()).to.equal(1n);
    });

    it("sollte Deployer als initialen Holder setzen", async function () {
      expect(await genesis.holder()).to.equal(owner.address);
    });

    it("sollte nicht gesperrt sein beim Deploy", async function () {
      expect(await genesis.locked()).to.be.false;
    });

    it("sollte mintedAt korrekt setzen", async function () {
      const mintedAt = await genesis.mintedAt();
      expect(mintedAt).to.be.gt(0n);
    });

    it("sollte GenesisMinted-Event beim Deploy emittieren", async function () {
      const GenesisToken = await ethers.getContractFactory("GenesisToken");
      const g2 = await GenesisToken.deploy();
      const receipt = await g2.deploymentTransaction().wait();
      const [dep] = await ethers.getSigners();
      const iface = g2.interface;
      const event = receipt.logs.find(l => {
        try { return iface.parseLog(l).name === "GenesisMinted"; }
        catch { return false; }
      });
      expect(event).to.not.be.undefined;
    });
  });

  // ── 2. Provenance ─────────────────────────────────────
  describe("Provenance", function () {
    it("sollte initialen Provenance-Eintrag haben", async function () {
      const len = await genesis.provenanceLength();
      expect(len).to.equal(1n);

      const entry = await genesis.getProvenance(0);
      expect(entry.from).to.equal(ethers.ZeroAddress);
      expect(entry.to).to.equal(owner.address);
      expect(entry.note).to.equal("ATC-001 Genesis Mint — A-TownChain Origin");
    });

    it("sollte Provenance-Eintrag hinzufügen und Holder aktualisieren", async function () {
      await genesis.connect(owner).recordProvenance(
        addr1.address, "Übergabe an A-TownChain Foundation"
      );
      expect(await genesis.holder()).to.equal(addr1.address);
      expect(await genesis.provenanceLength()).to.equal(2n);
    });

    it("sollte ProvenanceRecorded-Event emittieren", async function () {
      await expect(
        genesis.connect(owner).recordProvenance(addr1.address, "Transfer")
      ).to.emit(genesis, "ProvenanceRecorded")
        .withArgs(owner.address, addr1.address, "Transfer");
    });

    it("sollte Nicht-Owner bei recordProvenance ablehnen", async function () {
      await expect(
        genesis.connect(addr1).recordProvenance(addr2.address, "Hack")
      ).to.be.reverted;
    });

    it("sollte Provenance-Kette korrekt aufbauen", async function () {
      await genesis.recordProvenance(addr1.address, "Schritt 1");
      await genesis.recordProvenance(addr2.address, "Schritt 2");

      const e1 = await genesis.getProvenance(1);
      const e2 = await genesis.getProvenance(2);

      expect(e1.from).to.equal(owner.address);
      expect(e1.to).to.equal(addr1.address);
      expect(e2.from).to.equal(addr1.address);
      expect(e2.to).to.equal(addr2.address);
    });
  });

  // ── 3. Lock-Mechanismus ───────────────────────────────
  describe("Lock", function () {
    it("sollte Token sperren", async function () {
      await genesis.connect(owner).lock();
      expect(await genesis.locked()).to.be.true;
    });

    it("sollte GenesisLocked-Event emittieren", async function () {
      await expect(
        genesis.connect(owner).lock()
      ).to.emit(genesis, "GenesisLocked");
    });

    it("sollte doppeltes Sperren ablehnen", async function () {
      await genesis.connect(owner).lock();
      await expect(
        genesis.connect(owner).lock()
      ).to.be.revertedWith("Already locked");
    });

    it("sollte Provenance nach Lock blockieren", async function () {
      await genesis.connect(owner).lock();
      await expect(
        genesis.connect(owner).recordProvenance(addr1.address, "zu spät")
      ).to.be.revertedWith("Token is locked");
    });

    it("sollte Nicht-Owner bei lock() ablehnen", async function () {
      await expect(
        genesis.connect(addr1).lock()
      ).to.be.reverted;
    });
  });

  // ── 4. Verify & Metadaten ─────────────────────────────
  describe("Verify & Metadaten", function () {
    it("sollte verify() korrekt zurückgeben", async function () {
      const [isValid, currentHolder, age, provLen] = await genesis.verify();
      expect(isValid).to.be.true;
      expect(currentHolder).to.equal(owner.address);
      expect(age).to.be.gte(0n);
      expect(provLen).to.equal(1n);
    });

    it("sollte getMetadata alle Felder zurückgeben", async function () {
      const [
        tokenId, name_, supply, holdr, created, isLocked, provCount
      ] = await genesis.getMetadata();

      expect(tokenId).to.equal("ATC-001-GENESIS");
      expect(name_).to.equal("A-TownChain Genesis Token");
      expect(supply).to.equal(1n);
      expect(holdr).to.equal(owner.address);
      expect(created).to.be.gt(0n);
      expect(isLocked).to.be.false;
      expect(provCount).to.equal(1n);
    });

    it("sollte nach Lock den Status in Metadaten zeigen", async function () {
      await genesis.lock();
      const [, , , , , isLocked,] = await genesis.getMetadata();
      expect(isLocked).to.be.true;
    });

    it("sollte nach Provenance-Eintrag korrekte Holder-Anzahl zeigen", async function () {
      await genesis.recordProvenance(addr1.address, "Test");
      const [, , , , , , provCount] = await genesis.getMetadata();
      expect(provCount).to.equal(2n);
    });
  });
});
