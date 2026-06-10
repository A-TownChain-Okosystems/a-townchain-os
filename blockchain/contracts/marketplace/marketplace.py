"""
ATC Marketplace — Issue #13 (Shivamon kaufen & verkaufen)
On-Chain NFT Marketplace für Shivamon-Trading.
"""
import hashlib, time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

class ListingStatus(Enum):
    ACTIVE    = "active"
    SOLD      = "sold"
    CANCELLED = "cancelled"
    EXPIRED   = "expired"

class AuctionStatus(Enum):
    ACTIVE    = "active"
    ENDED     = "ended"
    CANCELLED = "cancelled"

@dataclass
class Listing:
    id:           str
    seller:       str
    nft_id:       str
    price:        float     # ATC
    token:        str = "ATC"
    status:       ListingStatus = ListingStatus.ACTIVE
    created:      float = field(default_factory=time.time)
    expires:      Optional[float] = None
    buyer:        Optional[str] = None
    sold_at:      Optional[float] = None
    sale_price:   Optional[float] = None
    tx_hash:      Optional[str] = None

@dataclass
class Auction:
    id:           str
    seller:       str
    nft_id:       str
    start_price:  float
    reserve:      float    # Mindestpreis
    ends_at:      float
    status:       AuctionStatus = AuctionStatus.ACTIVE
    bids:         Dict[str, float] = field(default_factory=dict)  # bidder → amount
    created:      float = field(default_factory=time.time)

    @property
    def highest_bid(self) -> float:
        return max(self.bids.values()) if self.bids else 0.0

    @property
    def highest_bidder(self) -> Optional[str]:
        if not self.bids: return None
        return max(self.bids.items(), key=lambda x: x[1])[0]

class ATCMarketplace:
    """
    A-TownChain NFT Marketplace (ATC-MARKET-1000).
    Features:
    - Direktkauf zu Festpreis
    - Auktionen mit Mindestgebot
    - 2.5% Marktplatz-Gebühr
    - Offer-System (Counter-Offers)
    - Royalties: 5% an Original-Creator
    """
    MARKETPLACE_FEE = 0.025   # 2.5%
    ROYALTY_FEE     = 0.05    # 5% an Creator
    MIN_PRICE       = 1.0     # 1 ATC Minimum

    def __init__(self):
        self._listings:  Dict[str, Listing] = {}
        self._auctions:  Dict[str, Auction] = {}
        self._balances:  Dict[str, float]   = {}
        self._creators:  Dict[str, str]     = {}  # nft_id → creator_address
        self._volume:    float = 0.0
        self._fees_collected: float = 0.0

    def register_creator(self, nft_id: str, creator: str):
        self._creators[nft_id] = creator

    def deposit(self, user: str, amount: float):
        self._balances[user] = self._balances.get(user, 0.0) + amount

    def balance(self, user: str) -> float:
        return self._balances.get(user, 0.0)

    def _listing_id(self, seller, nft_id) -> str:
        return hashlib.sha256(f"{seller}{nft_id}{time.time()}".encode()).hexdigest()[:12]

    # ── Direktkauf ──────────────────────────────────────────────────
    def list_nft(self, seller: str, nft_id: str, price: float,
                  duration_days: int = 30) -> Listing:
        if price < self.MIN_PRICE: raise ValueError(f"Min Preis: {self.MIN_PRICE} ATC")
        lid = self._listing_id(seller, nft_id)
        listing = Listing(
            id=lid, seller=seller, nft_id=nft_id, price=price,
            expires=time.time() + duration_days*86400,
        )
        self._listings[lid] = listing
        return listing

    def buy(self, listing_id: str, buyer: str) -> dict:
        lst = self._listings.get(listing_id)
        if not lst: raise ValueError("Listing nicht gefunden")
        if lst.status != ListingStatus.ACTIVE: raise ValueError(f"Listing {lst.status.value}")
        if lst.expires and time.time() > lst.expires:
            lst.status = ListingStatus.EXPIRED; raise ValueError("Listing abgelaufen")
        if buyer == lst.seller: raise ValueError("Seller kann nicht selbst kaufen")

        bal = self._balances.get(buyer, 0.0)
        if bal < lst.price: raise ValueError(f"Nicht genug ATC (Guthaben: {bal}, Preis: {lst.price})")

        marketplace_cut = round(lst.price * self.MARKETPLACE_FEE, 6)
        royalty         = round(lst.price * self.ROYALTY_FEE, 6)
        seller_receives = round(lst.price - marketplace_cut - royalty, 6)

        # Zahlung
        self._balances[buyer]     -= lst.price
        self._balances[lst.seller] = self._balances.get(lst.seller,0) + seller_receives
        creator = self._creators.get(lst.nft_id)
        if creator:
            self._balances[creator] = self._balances.get(creator,0) + royalty
        self._fees_collected += marketplace_cut
        self._volume         += lst.price

        lst.status    = ListingStatus.SOLD
        lst.buyer     = buyer
        lst.sold_at   = time.time()
        lst.sale_price= lst.price
        lst.tx_hash   = hashlib.sha256(f"{listing_id}{buyer}{time.time()}".encode()).hexdigest()

        return {"tx_hash": lst.tx_hash, "nft_id": lst.nft_id,
                "price": lst.price, "seller_receives": seller_receives,
                "royalty": royalty, "fee": marketplace_cut}

    # ── Auktionen ───────────────────────────────────────────────────
    def start_auction(self, seller: str, nft_id: str,
                       start_price: float, reserve: float,
                       duration_hours: int = 48) -> Auction:
        aid = self._listing_id(seller, nft_id) + "a"
        auction = Auction(
            id=aid, seller=seller, nft_id=nft_id,
            start_price=start_price, reserve=reserve,
            ends_at=time.time() + duration_hours*3600,
        )
        self._auctions[aid] = auction
        return auction

    def place_bid(self, auction_id: str, bidder: str, amount: float) -> bool:
        auc = self._auctions.get(auction_id)
        if not auc: raise ValueError("Auktion nicht gefunden")
        if auc.status != AuctionStatus.ACTIVE: raise ValueError("Auktion nicht aktiv")
        if time.time() > auc.ends_at: auc.status = AuctionStatus.ENDED; raise ValueError("Auktion beendet")
        if amount <= auc.highest_bid: raise ValueError(f"Gebot muss > {auc.highest_bid} ATC sein")
        if amount < auc.start_price:  raise ValueError(f"Mindestgebot: {auc.start_price} ATC")
        bal = self._balances.get(bidder, 0.0)
        if bal < amount: raise ValueError(f"Nicht genug Guthaben ({bal} ATC)")
        # Vorheriges Gebot zurückgeben
        if auc.highest_bidder:
            prev_bidder = auc.highest_bidder
            prev_bid    = auc.bids[prev_bidder]
            self._balances[prev_bidder] = self._balances.get(prev_bidder,0) + prev_bid
            self._balances[bidder] -= amount
        else:
            self._balances[bidder] -= amount
        auc.bids[bidder] = amount
        return True

    def settle_auction(self, auction_id: str) -> Optional[dict]:
        auc = self._auctions.get(auction_id)
        if not auc: raise ValueError("Auktion nicht gefunden")
        if time.time() < auc.ends_at and auc.status == AuctionStatus.ACTIVE:
            raise ValueError("Auktion läuft noch")
        auc.status = AuctionStatus.ENDED
        if not auc.bids or auc.highest_bid < auc.reserve:
            # Kein gültiges Gebot → Erstattung
            if auc.highest_bidder:
                self._balances[auc.highest_bidder] =                     self._balances.get(auc.highest_bidder,0) + auc.highest_bid
            return None
        winner = auc.highest_bidder
        price  = auc.highest_bid
        fee    = round(price * self.MARKETPLACE_FEE, 6)
        royalty= round(price * self.ROYALTY_FEE, 6)
        self._balances[auc.seller] = self._balances.get(auc.seller,0) + price - fee - royalty
        self._fees_collected += fee
        self._volume         += price
        return {"winner": winner, "price": price, "nft_id": auc.nft_id}

    def active_listings(self) -> List[Listing]:
        return [l for l in self._listings.values()
                if l.status == ListingStatus.ACTIVE]

    def stats(self) -> dict:
        return {
            "listings":       len(self._listings),
            "active":         len(self.active_listings()),
            "auctions":       len(self._auctions),
            "total_volume":   round(self._volume,2),
            "fees_collected": round(self._fees_collected,6),
            "marketplace_fee": f"{self.MARKETPLACE_FEE*100:.1f}%",
            "royalty_fee":    f"{self.ROYALTY_FEE*100:.1f}%",
        }
