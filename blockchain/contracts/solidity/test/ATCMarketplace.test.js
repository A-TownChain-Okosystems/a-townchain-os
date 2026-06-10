const { expect } = require("chai");
const { ethers }  = require("hardhat");
const { time }    = require("@nomicfoundation/hardhat-network-helpers");

/**
 * ATCMarketplace.test.js — NFT-Marktplatz
 * Tests: Listing, Kauf, Cancel, Gebühren, Escrow
 */
describe("ATCMarketplace", function () {

  let marketplace, atcToken, shivamon;
  let owner, seller, buyer, treasury, relayer;

  const INITIAL_ATC = ethers.parseEther("1000000");
  const LIST_PRICE  = ethers.parseEther("500");      // 500 ATC
  const MIN_PRICE   = ethers.parseEther("1");

  beforeEach(async function () {
    [owner, seller, buyer, treasury, relayer] = await ethers.getSigners();

    // ATCToken deployen + Supply
    const ATCToken = await ethers.getContractFactory("ATCToken");
    atcToken = await ATCToken.deploy();
    await atcToken.waitForDeployment();
    await atcToken.registerMiner(owner.address);
    await atcToken.connect(owner).mint(owner.address, INITIAL_ATC);
    await atcToken.transfer(seller.address, ethers.parseEther("10000"));
    await atcToken.transfer(buyer.address,  ethers.parseEther("10000"));

    // Shivamon deployen + Approve
    const Shivamon = await ethers.getContractFactory("Shivamon");
    shivamon = await Shivamon.deploy(await atcToken.getAddress());
    await shivamon.waitForDeployment();

    // Marketplace deployen
    const MP = await ethers.getContractFactory("ATCMarketplace");
    marketplace = await MP.deploy(
      await atcToken.getAddress(),
      await shivamon.getAddress(),
      treasury.address
    );
    await marketplace.waitForDeployment();

    // Seller: ownerMint NFT (ohne Fee)
    await shivamon.connect(owner).ownerMint(seller.address, "Fire", "Rare", 1);
    // Token ID 0 gehört Seller

    // Seller gibt Marketplace Erlaubnis für NFT
    await shivamon.connect(seller).setApprovalForAll(
      await marketplace.getAddress(), true
    );

    // Buyer gibt Marketplace Erlaubnis für ATC
    await atcToken.connect(buyer).approve(
      await marketplace.getAddress(), ethers.parseEther("10000")
    );
  });

  // ── 1. Listing ────────────────────────────────────────
  describe("Listing", function () {
    it("sollte NFT korrekt listen", async function () {
      const tx = await marketplace.connect(seller).listForSale(0, LIST_PRICE);
      await tx.wait();

      const listing = await marketplace.getListing(0);
      expect(listing.tokenId).to.equal(0n);
      expect(listing.seller).to.equal(seller.address);
      expect(listing.priceATC).to.equal(LIST_PRICE);
      expect(listing.status).to.equal(0n); // Active
    });

    it("sollte Listed-Event emittieren", async function () {
      await expect(
        marketplace.connect(seller).listForSale(0, LIST_PRICE)
      ).to.emit(marketplace, "Listed")
        .withArgs(0n, 0n, seller.address, LIST_PRICE);
    });

    it("sollte NFT in Escrow sperren", async function () {
      await marketplace.connect(seller).listForSale(0, LIST_PRICE);
      // NFT ist jetzt im Marketplace-Contract
      expect(await shivamon.ownerOf(0)).to.equal(await marketplace.getAddress());
    });

    it("sollte bei Preis unter Minimum revertieren", async function () {
      await expect(
        marketplace.connect(seller).listForSale(0, ethers.parseEther("0.5"))
      ).to.be.revertedWith("Price too low");
    });

    it("sollte bei Nicht-Owner revertieren", async function () {
      await expect(
        marketplace.connect(buyer).listForSale(0, LIST_PRICE)
      ).to.be.reverted;
    });
  });

  // ── 2. Kauf ───────────────────────────────────────────
  describe("Kauf (buy)", function () {
    beforeEach(async function () {
      await marketplace.connect(seller).listForSale(0, LIST_PRICE);
    });

    it("sollte NFT korrekt kaufen und transferieren", async function () {
      await marketplace.connect(buyer).buy(0);
      expect(await shivamon.ownerOf(0)).to.equal(buyer.address);
    });

    it("sollte Sold-Event emittieren", async function () {
      await expect(
        marketplace.connect(buyer).buy(0)
      ).to.emit(marketplace, "Sold")
        .withArgs(0n, 0n, buyer.address, LIST_PRICE);
    });

    it("sollte Gebühren korrekt verteilen (2.5% Royalty + 1% Fee)", async function () {
      const royalty  = LIST_PRICE * 250n  / 10000n;  // 12.5 ATC
      const platFee  = LIST_PRICE * 100n  / 10000n;  // 5.0 ATC
      const sellerGet= LIST_PRICE - royalty - platFee; // 482.5 ATC

      const sellerBefore   = await atcToken.balanceOf(seller.address);
      const treasuryBefore = await atcToken.balanceOf(treasury.address);

      await marketplace.connect(buyer).buy(0);

      const sellerAfter    = await atcToken.balanceOf(seller.address);
      const treasuryAfter  = await atcToken.balanceOf(treasury.address);

      expect(sellerAfter - sellerBefore).to.equal(sellerGet);
      expect(treasuryAfter - treasuryBefore).to.equal(platFee);
    });

    it("sollte Listing als Sold markieren", async function () {
      await marketplace.connect(buyer).buy(0);
      const listing = await marketplace.getListing(0);
      expect(listing.status).to.equal(1n); // Sold
    });

    it("sollte Volume korrekt tracken", async function () {
      await marketplace.connect(buyer).buy(0);
      expect(await marketplace.totalVolume()).to.equal(LIST_PRICE);
    });

    it("sollte nicht von eigenem Listing kaufen können", async function () {
      await expect(
        marketplace.connect(seller).buy(0)
      ).to.be.revertedWith("Cannot buy own listing");
    });

    it("sollte bei inaktivem Listing revertieren", async function () {
      await marketplace.connect(buyer).buy(0);
      await expect(
        marketplace.connect(buyer).buy(0)
      ).to.be.revertedWith("Not active");
    });
  });

  // ── 3. Cancel ─────────────────────────────────────────
  describe("Cancel Listing", function () {
    beforeEach(async function () {
      await marketplace.connect(seller).listForSale(0, LIST_PRICE);
    });

    it("sollte Listing abbrechen und NFT zurückgeben", async function () {
      await marketplace.connect(seller).cancelListing(0);
      expect(await shivamon.ownerOf(0)).to.equal(seller.address);
    });

    it("sollte ListingCancelled-Event emittieren", async function () {
      await expect(
        marketplace.connect(seller).cancelListing(0)
      ).to.emit(marketplace, "ListingCancelled")
        .withArgs(0n, 0n);
    });

    it("sollte als Cancelled markiert werden", async function () {
      await marketplace.connect(seller).cancelListing(0);
      const listing = await marketplace.getListing(0);
      expect(listing.status).to.equal(2n); // Cancelled
    });

    it("sollte Owner auch canceln dürfen", async function () {
      await marketplace.connect(owner).cancelListing(0);
      expect(await shivamon.ownerOf(0)).to.equal(seller.address);
    });

    it("sollte Nicht-Berechtigte abweisen", async function () {
      await expect(
        marketplace.connect(buyer).cancelListing(0)
      ).to.be.revertedWith("Not authorized");
    });
  });

  // ── 4. Stats & Views ──────────────────────────────────
  describe("Stats & Views", function () {
    it("sollte getStats korrekt zurückgeben", async function () {
      await marketplace.connect(seller).listForSale(0, LIST_PRICE);
      const stats = await marketplace.getStats();
      expect(stats.total).to.equal(1n);
      expect(stats.active).to.equal(1n);
    });

    it("sollte getActiveListings paginiert zurückgeben", async function () {
      await marketplace.connect(seller).listForSale(0, LIST_PRICE);
      const listings = await marketplace.getActiveListings(0, 10);
      expect(listings[0].tokenId).to.equal(0n);
    });

    it("sollte makeOffer Event emittieren", async function () {
      await expect(
        marketplace.connect(buyer).makeOffer(0, ethers.parseEther("450"))
      ).to.emit(marketplace, "OfferMade")
        .withArgs(0n, buyer.address, ethers.parseEther("450"));
    });
  });
});
