// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title ATCMarketplace
 * @dev NFT-Marktplatz für Shivamon — ATC-Zahlungen
 * Royalty: 2.5% an Creator
 * Platform-Fee: 1.0% an Treasury
 * Escrow: NFTs werden bis zum Kauf/Cancel gesperrt
 */
contract ATCMarketplace is Ownable, ReentrancyGuard {

    // ── Konstanten ────────────────────────────────────────
    uint256 public constant ROYALTY_BPS  = 250;   // 2.5%
    uint256 public constant PLATFORM_BPS = 100;   // 1.0%
    uint256 public constant BPS_BASE     = 10_000;
    uint256 public constant MIN_PRICE    = 1 ether; // 1 ATC minimum

    // ── State ─────────────────────────────────────────────
    IERC20  public atcToken;
    IERC721 public nftContract;
    address public treasury;
    uint256 private _listingCount;
    uint256 public  totalVolume;
    uint256 public  totalFees;

    enum ListingStatus { Active, Sold, Cancelled, Expired }

    struct Listing {
        uint256       listingId;
        uint256       tokenId;
        address       seller;
        address       creator;    // Original-Minter (Royalty-Empfänger)
        uint256       priceATC;
        uint256       listedAt;
        uint256       expiresAt;  // 30 Tage
        ListingStatus status;
    }

    struct Offer {
        uint256 offerId;
        uint256 tokenId;
        address buyer;
        uint256 offerATC;
        uint256 expiresAt;
        bool    accepted;
    }

    mapping(uint256 => Listing)             public listings;
    mapping(uint256 => uint256)             public tokenToListing;   // tokenId → listingId
    mapping(uint256 => Offer[])             public tokenOffers;
    mapping(uint256 => address)             public tokenCreator;     // tokenId → creator

    // ── Events ────────────────────────────────────────────
    event Listed(uint256 indexed listingId, uint256 indexed tokenId,
                 address indexed seller, uint256 priceATC);
    event Sold(uint256 indexed listingId, uint256 indexed tokenId,
               address indexed buyer, uint256 priceATC);
    event ListingCancelled(uint256 indexed listingId, uint256 indexed tokenId);
    event OfferMade(uint256 indexed tokenId, address indexed buyer, uint256 offerATC);
    event OfferAccepted(uint256 indexed tokenId, address indexed buyer, uint256 offerATC);

    // ── Konstruktor ───────────────────────────────────────
    constructor(address _atcToken, address _nftContract, address _treasury)
        Ownable(msg.sender)
    {
        atcToken    = IERC20(_atcToken);
        nftContract = IERC721(_nftContract);
        treasury    = _treasury;
    }

    // ── NFT listen ────────────────────────────────────────
    function listForSale(uint256 tokenId, uint256 priceATC)
        external nonReentrant returns (uint256)
    {
        require(nftContract.ownerOf(tokenId) == msg.sender, "Not owner");
        require(priceATC >= MIN_PRICE, "Price too low");
        require(listings[tokenToListing[tokenId]].status != ListingStatus.Active,
                "Already listed");

        // NFT in Escrow transferieren
        nftContract.transferFrom(msg.sender, address(this), tokenId);

        uint256 listingId = _listingCount++;
        if (tokenCreator[tokenId] == address(0)) {
            tokenCreator[tokenId] = msg.sender; // erster Seller = Creator
        }

        listings[listingId] = Listing({
            listingId:  listingId,
            tokenId:    tokenId,
            seller:     msg.sender,
            creator:    tokenCreator[tokenId],
            priceATC:   priceATC,
            listedAt:   block.timestamp,
            expiresAt:  block.timestamp + 30 days,
            status:     ListingStatus.Active
        });
        tokenToListing[tokenId] = listingId;

        emit Listed(listingId, tokenId, msg.sender, priceATC);
        return listingId;
    }

    // ── Kaufen ────────────────────────────────────────────
    function buy(uint256 listingId) external nonReentrant {
        Listing storage l = listings[listingId];
        require(l.status == ListingStatus.Active, "Not active");
        require(block.timestamp < l.expiresAt, "Listing expired");
        require(msg.sender != l.seller, "Cannot buy own listing");

        uint256 price    = l.priceATC;
        uint256 royalty  = (price * ROYALTY_BPS)  / BPS_BASE;
        uint256 platFee  = (price * PLATFORM_BPS) / BPS_BASE;
        uint256 sellerGet= price - royalty - platFee;

        // ATC-Zahlungen
        require(atcToken.transferFrom(msg.sender, l.seller,   sellerGet), "Seller transfer failed");
        require(atcToken.transferFrom(msg.sender, l.creator,  royalty),   "Royalty transfer failed");
        require(atcToken.transferFrom(msg.sender, treasury,   platFee),   "Fee transfer failed");

        // NFT aus Escrow an Käufer
        nftContract.transferFrom(address(this), msg.sender, l.tokenId);

        l.status = ListingStatus.Sold;
        totalVolume += price;
        totalFees   += platFee + royalty;

        emit Sold(listingId, l.tokenId, msg.sender, price);
    }

    // ── Listing abbrechen ─────────────────────────────────
    function cancelListing(uint256 listingId) external nonReentrant {
        Listing storage l = listings[listingId];
        require(l.status == ListingStatus.Active, "Not active");
        require(l.seller == msg.sender || msg.sender == owner(), "Not authorized");

        l.status = ListingStatus.Cancelled;
        nftContract.transferFrom(address(this), l.seller, l.tokenId);

        emit ListingCancelled(listingId, l.tokenId);
    }

    // ── Angebot machen ────────────────────────────────────
    function makeOffer(uint256 tokenId, uint256 offerATC) external {
        require(offerATC >= MIN_PRICE, "Offer too low");
        tokenOffers[tokenId].push(Offer({
            offerId:  tokenOffers[tokenId].length,
            tokenId:  tokenId,
            buyer:    msg.sender,
            offerATC: offerATC,
            expiresAt: block.timestamp + 7 days,
            accepted: false
        }));
        emit OfferMade(tokenId, msg.sender, offerATC);
    }

    // ── Views ─────────────────────────────────────────────
    function getListing(uint256 listingId) external view returns (Listing memory) {
        return listings[listingId];
    }

    function getActiveListings(uint256 offset, uint256 limit)
        external view returns (Listing[] memory result)
    {
        result = new Listing[](limit);
        uint256 count = 0;
        for (uint256 i = offset; i < _listingCount && count < limit; i++) {
            if (listings[i].status == ListingStatus.Active) {
                result[count++] = listings[i];
            }
        }
    }

    function getStats() external view returns (
        uint256 total, uint256 active, uint256 volume, uint256 fees
    ) {
        total  = _listingCount;
        volume = totalVolume;
        fees   = totalFees;
        for (uint256 i = 0; i < _listingCount; i++) {
            if (listings[i].status == ListingStatus.Active) active++;
        }
    }

    // ── Admin ─────────────────────────────────────────────
    function setTreasury(address _treasury) external onlyOwner {
        treasury = _treasury;
    }
}
