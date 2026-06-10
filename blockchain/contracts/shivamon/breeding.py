"""
Shivamon Breeding — Issue #11 (Gen 2 NFT Züchtung)
DNA-basiertes Vererbungssystem für Shivamon NFTs.
Gen 2 Shivamon erben Traits von 2 Eltern-Shivamon.
"""
import hashlib, random, time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

class ElementType(Enum):
    FIRE    = "fire"
    WATER   = "water"
    EARTH   = "earth"
    AIR     = "air"
    SHADOW  = "shadow"
    NEON    = "neon"
    QUANTUM = "quantum"
    FUSION  = "fusion"   # Gen 2 spezifisch: 2 Eltern-Elemente kombiniert

@dataclass
class ShivamonDNA:
    """DNA-Sequenz eines Shivamon — bestimmt alle Traits."""
    sequence: str        # 64-Zeichen Hex (256-bit)
    element:  ElementType
    rarity:   int        # 1–100 (1=legendär, 100=common)
    stats:    Dict[str, int] = field(default_factory=dict)
    traits:   List[str]  = field(default_factory=list)
    gen:      int = 1

    @classmethod
    def generate(cls, seed: str, element: ElementType, gen: int = 1):
        seq = hashlib.sha256(seed.encode()).hexdigest()
        r   = random.Random(seed)
        rarity = max(1, min(100, int(seq[:4], 16) % 100 + 1))
        stats  = {
            "hp":  r.randint(50,100) + (100 - rarity) // 5,
            "atk": r.randint(40,90)  + (100 - rarity) // 6,
            "def": r.randint(30,80)  + (100 - rarity) // 7,
            "spd": r.randint(40,95)  + (100 - rarity) // 5,
            "spc": r.randint(35,85)  + (100 - rarity) // 6,
        }
        traits = []
        trait_pool = ["Sturdy","Swift","Brave","Calm","Jolly","Timid",
                       "Adamant","Modest","Bold","Impish","Careful","Quirky"]
        for i in range(3): traits.append(trait_pool[int(seq[i*2:i*2+2],16) % len(trait_pool)])
        return cls(sequence=seq, element=element, rarity=rarity,
                    stats=stats, traits=list(set(traits)), gen=gen)


@dataclass
class BreedingResult:
    offspring_dna: ShivamonDNA
    parent_a_id:   str
    parent_b_id:   str
    inherited_from_a: List[str]
    inherited_from_b: List[str]
    mutation:        bool
    mutation_trait:  Optional[str]
    timestamp:       float = field(default_factory=time.time)
    egg_hash:        str = ""

    def __post_init__(self):
        if not self.egg_hash:
            self.egg_hash = hashlib.sha256(
                f"{self.parent_a_id}{self.parent_b_id}{self.timestamp}".encode()
            ).hexdigest()[:16]


class ShivamonBreedingEngine:
    """
    Gen-2 NFT Breeding Engine.
    Regeln:
    - Zwei Shivamon derselben Ära können brüten
    - DNA wird 50/50 geteilt (mit Mutationschance)
    - Eltern-Elemente können zu FUSION kombinieren
    - Rarity = Durchschnitt beider Eltern (+-10% Zufall)
    - SoulBound Gen-2-NFT: 10% Mutationswahrscheinlichkeit
    """
    COOLDOWN       = 86400  # 24h zwischen Zuchten
    MUTATION_RATE  = 0.10   # 10%
    MAX_GEN        = 3      # Max Generation

    FUSION_TABLE = {
        frozenset({"fire","water"}):   ElementType.NEON,
        frozenset({"fire","earth"}):   ElementType.FIRE,
        frozenset({"water","earth"}):  ElementType.EARTH,
        frozenset({"air","fire"}):     ElementType.QUANTUM,
        frozenset({"shadow","neon"}):  ElementType.QUANTUM,
        frozenset({"shadow","water"}): ElementType.SHADOW,
        frozenset({"air","water"}):    ElementType.AIR,
        frozenset({"earth","shadow"}): ElementType.FUSION,
        frozenset({"neon","quantum"}): ElementType.FUSION,
    }

    def __init__(self):
        self._registry: Dict[str, ShivamonDNA] = {}
        self._cooldowns: Dict[str, float] = {}
        self._bred_count = 0

    def register(self, shivamon_id: str, dna: ShivamonDNA):
        self._registry[shivamon_id] = dna

    def _check_cooldown(self, sid: str) -> bool:
        last = self._cooldowns.get(sid, 0)
        return (time.time() - last) >= self.COOLDOWN

    def _resolve_element(self, ea: ElementType, eb: ElementType) -> ElementType:
        key = frozenset({ea.value, eb.value})
        return self.FUSION_TABLE.get(key, ea if random.random() < 0.5 else eb)

    def breed(self, parent_a_id: str, parent_b_id: str,
               owner: str) -> BreedingResult:
        dna_a = self._registry.get(parent_a_id)
        dna_b = self._registry.get(parent_b_id)
        if not dna_a: raise ValueError(f"Shivamon {parent_a_id} nicht gefunden")
        if not dna_b: raise ValueError(f"Shivamon {parent_b_id} nicht gefunden")
        if parent_a_id == parent_b_id:
            raise ValueError("Selbst-Zucht nicht möglich")
        if dna_a.gen >= self.MAX_GEN or dna_b.gen >= self.MAX_GEN:
            raise ValueError(f"Max Generation ({self.MAX_GEN}) erreicht")
        if not self._check_cooldown(parent_a_id):
            raise ValueError(f"{parent_a_id} hat noch Cooldown")
        if not self._check_cooldown(parent_b_id):
            raise ValueError(f"{parent_b_id} hat noch Cooldown")

        r = random.Random(f"{parent_a_id}{parent_b_id}{time.time()}")

        # Element bestimmen
        new_element = self._resolve_element(dna_a.element, dna_b.element)

        # Stats vererben (50/50 + +-10%)
        inherited_a, inherited_b = [], []
        new_stats = {}
        for stat in ["hp","atk","def","spd","spc"]:
            if r.random() < 0.5:
                new_stats[stat] = int(dna_a.stats.get(stat,50) * r.uniform(0.9,1.1))
                inherited_a.append(stat)
            else:
                new_stats[stat] = int(dna_b.stats.get(stat,50) * r.uniform(0.9,1.1))
                inherited_b.append(stat)

        # Traits vererben
        all_traits = list(set(dna_a.traits + dna_b.traits))
        new_traits  = r.sample(all_traits, min(3, len(all_traits)))

        # Rarity
        avg_rarity  = (dna_a.rarity + dna_b.rarity) / 2
        new_rarity  = max(1, min(100, int(avg_rarity + r.uniform(-10, 10))))

        # Mutation?
        mutated = r.random() < self.MUTATION_RATE
        mut_trait = None
        if mutated:
            bonus_traits = ["Mega","Ultra","Divine","Cosmic","Ethereal",
                             "Ancient","Prism","Void","Echo","Storm"]
            mut_trait = r.choice(bonus_traits)
            new_traits.append(mut_trait)
            new_rarity = max(1, new_rarity - 15)   # Mutanten sind seltener

        seed = f"{dna_a.sequence}{dna_b.sequence}{time.time()}"
        offspring_dna = ShivamonDNA(
            sequence = hashlib.sha256(seed.encode()).hexdigest(),
            element  = new_element,
            rarity   = new_rarity,
            stats    = new_stats,
            traits   = new_traits,
            gen      = max(dna_a.gen, dna_b.gen) + 1,
        )

        self._cooldowns[parent_a_id] = time.time()
        self._cooldowns[parent_b_id] = time.time()
        self._bred_count += 1

        return BreedingResult(
            offspring_dna    = offspring_dna,
            parent_a_id      = parent_a_id,
            parent_b_id      = parent_b_id,
            inherited_from_a = inherited_a,
            inherited_from_b = inherited_b,
            mutation         = mutated,
            mutation_trait   = mut_trait,
        )

    def stats(self) -> dict:
        return {
            "registered": len(self._registry),
            "bred_total": self._bred_count,
            "max_gen":    self.MAX_GEN,
            "mutation_rate": f"{self.MUTATION_RATE*100:.0f}%",
        }
