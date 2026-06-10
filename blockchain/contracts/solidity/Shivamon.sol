// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/**
 * @title Shivamon
 * @dev ATC-9000 NFT Standard — Battle-RPG NFTs für A-TownChain
 * Max Supply: 9.900
 * Elemente: Fire, Water, Earth, Air, Shadow, Neon, Quantum
 * Seltenheit: Common, Uncommon, Rare, Epic, Legendary, Genesis
 */
contract Shivamon is ERC721, ERC721Enumerable, ERC721URIStorage, Ownable {

    // ── Konstanten ────────────────────────────────────────
    uint256 public constant MAX_SUPPLY    = 9_900;
    uint256 public constant MINT_FEE_ATC  = 0.1 ether;   // 0.1 ATC (18 Dez.)
    uint256 public constant BREED_COOLDOWN = 48 hours;

    // ── State ─────────────────────────────────────────────
    uint256 private _nextTokenId;
    IERC20  public  atcToken;

    // Token-Metadaten
    struct ShivamonData {
        string  element;      // Fire|Water|Earth|Air|Shadow|Neon|Quantum
        string  rarity;       // Common|Uncommon|Rare|Epic|Legendary|Genesis
        uint8   generation;   // 1 = Gen 1, 2 = Gen 2 (Breeding), ...
        uint32  hp;
        uint32  attack;
        uint32  defense;
        uint32  speed;
        uint32  special;
        uint32  level;        // 1 – 100
        uint256 xp;
        uint256 lastBreed;    // Timestamp letzter Breed
        bytes32 dnaHash;      // Einzigartiger Fingerabdruck
    }

    mapping(uint256 => ShivamonData) public shivamonData;

    // ── Events ────────────────────────────────────────────
    event ShivamonMinted(uint256 indexed tokenId, address indexed owner,
                         string element, string rarity, uint8 generation);
    event BattleResult(uint256 indexed attackerId, uint256 indexed defenderId,
                       uint256 winner, uint32 xpGained);
    event Bred(uint256 indexed parent1, uint256 indexed parent2,
               uint256 indexed childId, address owner);

    // ── Konstruktor ───────────────────────────────────────
    constructor(address _atcToken)
        ERC721("Shivamon", "SHIV")
        Ownable(msg.sender)
    {
        atcToken = IERC20(_atcToken);
    }

    // ── Mint ──────────────────────────────────────────────
    function mint(
        address to,
        string  memory element,
        string  memory rarity,
        uint8   generation
    ) external returns (uint256) {
        require(_nextTokenId < MAX_SUPPLY, "Max supply reached");

        // Mint-Fee abziehen (0.1 ATC → Treasury/Owner)
        require(
            atcToken.transferFrom(msg.sender, owner(), MINT_FEE_ATC),
            "ATC fee transfer failed"
        );

        uint256 tokenId = _nextTokenId++;
        _safeMint(to, tokenId);

        // Stats berechnen (Rarity-basiert)
        uint256 mult = _rarityMultiplier(rarity);
        bytes32 dna  = keccak256(abi.encodePacked(to, element, generation, block.timestamp, tokenId));

        shivamonData[tokenId] = ShivamonData({
            element:    element,
            rarity:     rarity,
            generation: generation,
            hp:         uint32(100 * mult / 100),
            attack:     uint32(_pseudoRandom(tokenId, 1, 20, 40) * mult / 100),
            defense:    uint32(_pseudoRandom(tokenId, 2, 15, 35) * mult / 100),
            speed:      uint32(_pseudoRandom(tokenId, 3, 10, 30) * mult / 100),
            special:    uint32(_pseudoRandom(tokenId, 4, 25, 50) * mult / 100),
            level:      1,
            xp:         0,
            lastBreed:  0,
            dnaHash:    dna
        });

        emit ShivamonMinted(tokenId, to, element, rarity, generation);
        return tokenId;
    }

    // ── Owner-Mint (ohne Fee, für System) ─────────────────
    function ownerMint(address to, string memory element,
                       string memory rarity, uint8 generation)
        external onlyOwner returns (uint256)
    {
        require(_nextTokenId < MAX_SUPPLY, "Max supply reached");
        uint256 tokenId = _nextTokenId++;
        _safeMint(to, tokenId);
        uint256 mult = _rarityMultiplier(rarity);
        bytes32 dna  = keccak256(abi.encodePacked(to, element, generation, block.timestamp, tokenId));
        shivamonData[tokenId] = ShivamonData({
            element: element, rarity: rarity, generation: generation,
            hp: uint32(100 * mult / 100),
            attack:  uint32(_pseudoRandom(tokenId, 1, 20, 40) * mult / 100),
            defense: uint32(_pseudoRandom(tokenId, 2, 15, 35) * mult / 100),
            speed:   uint32(_pseudoRandom(tokenId, 3, 10, 30) * mult / 100),
            special: uint32(_pseudoRandom(tokenId, 4, 25, 50) * mult / 100),
            level: 1, xp: 0, lastBreed: 0, dnaHash: dna
        });
        emit ShivamonMinted(tokenId, to, element, rarity, generation);
        return tokenId;
    }

    // ── Battle ────────────────────────────────────────────
    function battle(uint256 attackerId, uint256 defenderId)
        external returns (uint256 winner, uint32 xpGained)
    {
        require(ownerOf(attackerId) == msg.sender, "Not attacker owner");
        require(_exists(attackerId) && _exists(defenderId), "Token does not exist");

        ShivamonData storage att = shivamonData[attackerId];
        ShivamonData storage def = shivamonData[defenderId];

        // Einfache Battle-Formel mit Pseudo-Zufälligkeit
        uint256 attScore = att.attack + att.speed / 2 + att.special / 2;
        uint256 defScore = def.defense + def.hp / 10 + def.speed / 2;
        uint256 rand     = uint256(keccak256(abi.encodePacked(
            block.timestamp, attackerId, defenderId, block.prevrandao
        ))) % 100;

        if (attScore + rand / 10 > defScore) {
            winner   = attackerId;
            xpGained = 50 + uint32(def.level * 5);
            att.xp  += xpGained;
            if (att.xp >= att.level * 100 && att.level < 100) {
                att.level++;
            }
        } else {
            winner   = defenderId;
            xpGained = 30 + uint32(att.level * 3);
            def.xp  += xpGained;
            if (def.xp >= def.level * 100 && def.level < 100) {
                def.level++;
            }
        }
        emit BattleResult(attackerId, defenderId, winner, xpGained);
    }

    // ── Breeding ──────────────────────────────────────────
    function breed(uint256 parent1Id, uint256 parent2Id, address childOwner)
        external returns (uint256 childId)
    {
        require(ownerOf(parent1Id) == msg.sender, "Not parent1 owner");
        require(_exists(parent1Id) && _exists(parent2Id), "Token does not exist");
        require(_nextTokenId < MAX_SUPPLY, "Max supply reached");

        ShivamonData storage p1 = shivamonData[parent1Id];
        ShivamonData storage p2 = shivamonData[parent2Id];

        require(block.timestamp >= p1.lastBreed + BREED_COOLDOWN, "P1 cooldown");
        require(block.timestamp >= p2.lastBreed + BREED_COOLDOWN, "P2 cooldown");

        p1.lastBreed = block.timestamp;
        p2.lastBreed = block.timestamp;

        childId = _nextTokenId++;
        _safeMint(childOwner, childId);

        // Element: zufällig von einem Elternteil
        string memory element = (block.timestamp % 2 == 0) ? p1.element : p2.element;
        uint8  gen            = uint8(
            (p1.generation > p2.generation ? p1.generation : p2.generation) + 1
        );
        bytes32 dna = keccak256(abi.encodePacked(parent1Id, parent2Id, childId, block.timestamp));

        // Stats = Durchschnitt × 1.1
        shivamonData[childId] = ShivamonData({
            element:    element,
            rarity:     "Uncommon",
            generation: gen,
            hp:         (p1.hp + p2.hp) * 110 / 200,
            attack:     (p1.attack + p2.attack) * 110 / 200,
            defense:    (p1.defense + p2.defense) * 110 / 200,
            speed:      (p1.speed + p2.speed) * 110 / 200,
            special:    (p1.special + p2.special) * 110 / 200,
            level: 1, xp: 0, lastBreed: 0, dnaHash: dna
        });
        emit Bred(parent1Id, parent2Id, childId, childOwner);
    }

    // ── Hilfsfunktionen ───────────────────────────────────
    function _rarityMultiplier(string memory rarity) internal pure returns (uint256) {
        bytes32 h = keccak256(bytes(rarity));
        if (h == keccak256("Genesis"))   return 500;
        if (h == keccak256("Legendary")) return 300;
        if (h == keccak256("Epic"))      return 200;
        if (h == keccak256("Rare"))      return 150;
        if (h == keccak256("Uncommon"))  return 120;
        return 100; // Common
    }

    function _pseudoRandom(uint256 seed, uint256 salt,
                            uint256 min, uint256 max) internal view returns (uint256) {
        uint256 r = uint256(keccak256(abi.encodePacked(seed, salt, block.timestamp))) % (max - min);
        return min + r;
    }

    function _exists(uint256 tokenId) internal view returns (bool) {
        return tokenId < _nextTokenId;
    }

    function totalMinted() external view returns (uint256) { return _nextTokenId; }

    // ── ERC721 Override-Boilerplate ───────────────────────
    function _update(address to, uint256 tokenId, address auth)
        internal override(ERC721, ERC721Enumerable) returns (address)
    { return super._update(to, tokenId, auth); }

    function _increaseBalance(address account, uint128 value)
        internal override(ERC721, ERC721Enumerable)
    { super._increaseBalance(account, value); }

    function tokenURI(uint256 tokenId)
        public view override(ERC721, ERC721URIStorage) returns (string memory)
    { return super.tokenURI(tokenId); }

    function supportsInterface(bytes4 interfaceId)
        public view override(ERC721, ERC721Enumerable, ERC721URIStorage) returns (bool)
    { return super.supportsInterface(interfaceId); }
}
