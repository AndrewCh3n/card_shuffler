"""Single-pass Linear Slotted Elevator sort planner and deck integrity checker.

Coordinate & ordering conventions (match docs/architecture.md & docs/cad_spec.md):
  - `target_order[0]` is the TOP card of the finished face-down deck.
  - `target_order[N - 1]` is the BOTTOM card of the finished face-down deck.
  - Physical slot 0 is the LOWEST comb slot (drops onto the output tray floor first).
  - Physical slot N - 1 is the HIGHEST used comb slot (drops onto the top of the deck last).
  - Mapping: `physical_slot = (N - 1) - target_index`
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from .cards import MAX_SLOTS, missing_cards_from, normalize_card, validate_deck_order


class SortFaultError(Exception):
    """Raised when deck integrity fails during a sort run (triggers PAUSED_ALERT)."""

    def __init__(self, code: str, message: str, card: Optional[str] = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.card = card


@dataclass
class SlotAssignment:
    card: str
    target_index: int
    physical_slot: int


@dataclass
class SinglePassSortPlan:
    """Tracks real-time state of a 1-pass 52-card or 54-card elevator sort."""

    target_order: List[str]
    slot_occupancy: Dict[int, str] = field(default_factory=dict)
    seen_cards: Dict[str, int] = field(default_factory=dict)  # card -> physical_slot
    _target_index_map: Dict[str, int] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.target_order = validate_deck_order(self.target_order)
        if len(self.target_order) > MAX_SLOTS:
            raise ValueError(f"Target deck exceeds {MAX_SLOTS} physical slots.")
        self._target_index_map = {card: idx for idx, card in enumerate(self.target_order)}

    @property
    def expected_count(self) -> int:
        return len(self.target_order)

    @property
    def placed_count(self) -> int:
        return len(self.seen_cards)

    @property
    def is_complete(self) -> bool:
        return self.placed_count == self.expected_count

    def physical_slot_for(self, card: str) -> int:
        """Compute physical elevator slot (0 = bottom of output deck, N-1 = top)."""
        norm = normalize_card(card)
        if norm not in self._target_index_map:
            raise SortFaultError(
                code="UNEXPECTED_CARD",
                message=f"Card {norm} is not part of the selected {self.expected_count}-card deck (e.g., Joker in 52-card mode).",
                card=norm,
            )
        target_idx = self._target_index_map[norm]
        return (self.expected_count - 1) - target_idx

    def assign_scanned_card(self, card: str) -> SlotAssignment:
        """Validate a newly scanned card and reserve its physical elevator slot."""
        norm = normalize_card(card)

        if norm in self.seen_cards:
            existing_slot = self.seen_cards[norm]
            raise SortFaultError(
                code="DUPLICATE_CARD",
                message=f"Duplicate card {norm} detected (already placed in slot {existing_slot}).",
                card=norm,
            )

        slot = self.physical_slot_for(norm)
        target_idx = self._target_index_map[norm]
        self.seen_cards[norm] = slot
        self.slot_occupancy[slot] = norm
        return SlotAssignment(card=norm, target_index=target_idx, physical_slot=slot)

    def missing_cards(self) -> List[str]:
        """Return any expected cards not yet scanned."""
        return missing_cards_from(self.seen_cards.keys(), self.target_order)

    def simulate_gravity_drop_output(self) -> List[str]:
        """Return the resulting face-down deck order (top -> bottom) after combs open.

        Physical slot 0 lands on the tray floor first (bottom of deck), and the highest
        occupied slot lands last (top of deck).
        """
        if not self.slot_occupancy:
            return []
        occupied_slots_top_to_bottom = sorted(self.slot_occupancy.keys(), reverse=True)
        return [self.slot_occupancy[s] for s in occupied_slots_top_to_bottom]


def plan_from_order(cards: Sequence[str]) -> SinglePassSortPlan:
    return SinglePassSortPlan(target_order=list(cards))
