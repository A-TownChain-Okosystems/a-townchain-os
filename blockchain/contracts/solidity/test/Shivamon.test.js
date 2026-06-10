const { expect } = require("chai");
const { ethers }  = require("hardhat");

/**
 * Shivamon.test.js — ATC-9000 NFT Contract
 * Tests: Mint, Battle, Breeding, Stats, Ownership
 */
describe("Shivamon (ATC-9000 NFT)", function () {

  let shivamon, atcToken;
  let owner, minter, player1, player2, treasury;

  const ELEMENTS  = ["Fire", "Water", "Earth", "Air", "Shadow", "Neon", "Quantum"];
  const RARITIES  = ["Common", "Uncommon", "Rare", "Epic", "Legendary", "Genesis"];
  const MINT_FEE  = ethers.parseEther("0.1");    // 0.1 ATC
  const INITIAL_ATC = ethers.parseEther("1000000");

  beforeEach(async function () {
    [owner, minter, player1, player2, treasury] = await ethers.getSigners();

    // ATCToken deployen
    const ATCToken = await ethers.getContractFactory("ATCToken");
    atcToken = await ATCToken.deploy();
    await atcToken.waitForDeployment();

    // Miner registrieren + Initial-Supply
    await atcToken.registerMiner(owner.address);
    await atcToken.connect(owner).mint(owner.address, INITIAL_ATC);

    // ATC an Spieler verteilen
    await atcToken.transfer(player1.address, ethers.parseEther("1000"));
    await atcToken.transfer(player2.address, ethers.parseEther("1000"));

    // Shivamon deployen
    const Shivamon = await ethers.getContractFactory("Shivamon");
    shivamon = await Shivamon.deploy(await atcToken.getAddress());
    await shivamon.waitForDeployment();

    // Approve für Mint-Fee
    await atcToken.connect(player1).approve(
      await shivamon.getAddress(), ethers.parseEther("100")
    );
    await atcToken.connect(player2).approve(
      await shivamon.getAddress(), ethers.parseEther("100")
    );
  });

  // ── 1. Deployment ─────────────────────────────────────
  describe("Deployment", function () {
    it("sollte korrekte Token-Metadaten haben", async function () {
      expect(await shivamon.name()).to.equal("Shivamon");
      expect(await shivamon.symbol()).to.equal("SHIV");
      expect(await shivamon.MAX_SUPPLY()).to.equal(9900n);
      expect(await shivamon.totalMinted()).to.equal(0n);
    });

    it("sollte ATC-Token-Adresse korrekt gespeichert haben", async function () {
      expect(await shivamon.atcToken()).to.equal(await atcToken.getAddress());
    });
  });

  // ── 2. Minting ────────────────────────────────────────
  describe("Mint", function () {
    it("sollte Shivamon mit Mint-Fee minten", async function () {
      const balBefore = await atcToken.balanceOf(player1.address);

      const tx = await shivamon.connect(player1).mint(
        player1.address, "Fire", "Common", 1
      );
      const receipt = await tx.wait();

      expect(await shivamon.totalMinted()).to.equal(1n);
      expect(await shivamon.ownerOf(0)).to.equal(player1.address);

      // Fee abgezogen?
      const balAfter = await atcToken.balanceOf(player1.address);
      expect(balBefore - balAfter).to.equal(MINT_FEE);
    });

    it("sollte ShivamonMinted-Event emittieren", async function () {
      await expect(
        shivamon.connect(player1).mint(player1.address, "Neon", "Rare", 1)
      ).to.emit(shivamon, "ShivamonMinted")
        .withArgs(0n, player1.address, "Neon", "Rare", 1);
    });

    it("sollte Stats nach Rarity korrekt berechnen", async function () {
      await shivamon.connect(player1).mint(player1.address, "Fire", "Common",    1);
      await shivamon.connect(player1).mint(player1.address, "Fire", "Legendary", 1);

      const common    = await shivamon.shivamonData(0);
      const legendary = await shivamon.shivamonData(1);

      expect(legendary.hp).to.be.gt(common.hp);
      expect(legendary.attack).to.be.gt(common.attack);
    });

    it("sollte ohne Fee für Owner (ownerMint) funktionieren", async function () {
      await shivamon.connect(owner).ownerMint(
        player1.address, "Quantum", "Genesis", 1
      );
      expect(await shivamon.totalMinted()).to.equal(1n);
      expect(await shivamon.ownerOf(0)).to.equal(player1.address);
      const data = await shivamon.shivamonData(0);
      expect(data.element).to.equal("Quantum");
      expect(data.rarity).to.equal("Genesis");
    });

    it("sollte bei unzureichendem Allowance revertieren", async function () {
      // Kein Approve → Transfer fehlschlägt
      const Shivamon2 = await ethers.getContractFactory("Shivamon");
      const s2 = await Shivamon2.deploy(await atcToken.getAddress());
      await s2.waitForDeployment();
      await expect(
        s2.connect(player1).mint(player1.address, "Fire", "Common", 1)
      ).to.be.reverted;
    });

    it("sollte DNA-Hash eindeutig generieren", async function () {
      await shivamon.connect(player1).mint(player1.address, "Fire", "Common", 1);
      await shivamon.connect(player1).mint(player1.address, "Fire", "Common", 1);
      const d0 = await shivamon.shivamonData(0);
      const d1 = await shivamon.shivamonData(1);
      expect(d0.dnaHash).to.not.equal(d1.dnaHash);
    });
  });

  // ── 3. Battle ─────────────────────────────────────────
  describe("Battle", function () {
    beforeEach(async function () {
      await shivamon.connect(owner).ownerMint(player1.address, "Fire",  "Rare", 1);
      await shivamon.connect(owner).ownerMint(player2.address, "Water", "Rare", 1);
    });

    it("sollte Battle korrekt ausführen und Winner zurückgeben", async function () {
      const tx = await shivamon.connect(player1).battle(0, 1);
      const receipt = await tx.wait();

      // BattleResult Event prüfen
      const event = receipt.logs.find(l => {
        try { return shivamon.interface.parseLog(l).name === "BattleResult"; }
        catch { return false; }
      });
      expect(event).to.not.be.undefined;

      const parsed = shivamon.interface.parseLog(event);
      const winner = parsed.args.winner;
      expect(winner === 0n || winner === 1n).to.be.true;
      expect(parsed.args.xpGained).to.be.gt(0n);
    });

    it("sollte XP an Gewinner vergeben", async function () {
      const before = (await shivamon.shivamonData(0)).xp;
      await shivamon.connect(player1).battle(0, 1);
      const after = (await shivamon.shivamonData(0)).xp;
      // Winner bekommt XP (entweder Token 0 oder 1)
      const after1 = (await shivamon.shivamonData(1)).xp;
      expect(after + after1).to.be.gt(before);
    });

    it("sollte revertieren wenn nicht Attacker-Owner", async function () {
      await expect(
        shivamon.connect(player2).battle(0, 1)
      ).to.be.revertedWith("Not attacker owner");
    });
  });

  // ── 4. Breeding ───────────────────────────────────────
  describe("Breeding", function () {
    beforeEach(async function () {
      await shivamon.connect(owner).ownerMint(player1.address, "Fire",  "Rare", 1);
      await shivamon.connect(owner).ownerMint(player1.address, "Water", "Rare", 1);
    });

    it("sollte Gen-2 Shivamon züchten", async function () {
      await shivamon.connect(player1).breed(0, 1, player1.address);
      expect(await shivamon.totalMinted()).to.equal(3n);
      const child = await shivamon.shivamonData(2);
      expect(child.generation).to.equal(2);
      expect(child.level).to.equal(1);
    });

    it("sollte Bred-Event emittieren", async function () {
      await expect(
        shivamon.connect(player1).breed(0, 1, player1.address)
      ).to.emit(shivamon, "Bred")
        .withArgs(0n, 1n, 2n, player1.address);
    });

    it("sollte Cooldown erzwingen", async function () {
      await shivamon.connect(player1).breed(0, 1, player1.address);
      await expect(
        shivamon.connect(player1).breed(0, 1, player1.address)
      ).to.be.revertedWith("P1 cooldown");
    });

    it("sollte revertieren wenn nicht Parent1-Owner", async function () {
      await expect(
        shivamon.connect(player2).breed(0, 1, player2.address)
      ).to.be.revertedWith("Not parent1 owner");
    });

    it("Kind-Stats sollten Durchschnitt der Eltern × 1.1 sein", async function () {
      const p1 = await shivamon.shivamonData(0);
      const p2 = await shivamon.shivamonData(1);
      await shivamon.connect(player1).breed(0, 1, player1.address);
      const child = await shivamon.shivamonData(2);
      const expectedHp = (p1.hp + p2.hp) * 110n / 200n;
      expect(child.hp).to.equal(expectedHp);
    });
  });

  // ── 5. Transfers ──────────────────────────────────────
  describe("Transfers", function () {
    beforeEach(async function () {
      await shivamon.connect(owner).ownerMint(player1.address, "Shadow", "Epic", 1);
    });

    it("sollte NFT transferieren", async function () {
      await shivamon.connect(player1).transferFrom(
        player1.address, player2.address, 0
      );
      expect(await shivamon.ownerOf(0)).to.equal(player2.address);
    });

    it("sollte totalMinted korrekt zählen", async function () {
      await shivamon.connect(owner).ownerMint(player2.address, "Air", "Common", 1);
      expect(await shivamon.totalMinted()).to.equal(2n);
      expect(await shivamon.totalSupply()).to.equal(2n);
    });
  });
});
