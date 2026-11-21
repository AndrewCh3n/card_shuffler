"""Canonical representation and validation for Bicycle Poker decks (52 cards + optional 2 Jokers)."""

from __future__ import annotations

import secrets
from typing import Iterable, List, Sequence

SUITS = ("S", "H", "C", "D")  # Spades, Hearts, Clubs, Diamonds
SUIT_SYMBOLS = {"S": "♠", "H": "♥", "C": "♣", "D": "♦"}
RANKS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
JOKERS = ("JK1", "JK2")

MAX_SLOTS = 54


def new_deck_order(include_jokers: bool = False) -> List[str]:
    """Return standard USPC Bicycle New Deck Order (top card index 0 -> bottom index N-1).

    Order: A-K Spades, A-K Diamonds, K-A Clubs, K-A Hearts (+ optional JK1, JK2).
    """
    cards: List[str] = []
    cards.extend(f"{r}S" for r in RANKS)
    cards.extend(f"{r}D" for r in RANKS)
    cards.extend(f"{r}C" for r in reversed(RANKS))
    cards.extend(f"{r}H" for r in reversed(RANKS))
    if include_jokers:
        cards.extend(JOKERS)
    return cards


STANDARD_52 = tuple(new_deck_order(include_jokers=False))
STANDARD_54 = tuple(new_deck_order(include_jokers=True))
VALID_CARD_SET = frozenset(STANDARD_54)


def normalize_card(code: str) -> str:
    """Normalize user input like 'as', '10h', 'jk1' into canonical form ('AS', '10H', 'JK1')."""
    cleaned = code.strip().upper()
    if cleaned not in VALID_CARD_SET:
        raise ValueError(f"Unknown card code: {code!r}")
    return cleaned


def card_display_label(code: str) -> str:
    """Return human-readable label like 'A♠', '10♥', 'Joker 1'."""
    card = normalize_card(code)
    if card == "JK1":
        return "Joker 1"
    if card == "JK2":
        return "Joker 2"
    return f"{card[:-1]}{SUIT_SYMBOLS[card[-1]]}"


def validate_deck_order(cards: Sequence[str], include_jokers: bool | None = None) -> List[str]:
    """Validate that `cards` is an exact permutation of a 52-card or 54-card deck.

    Returns the normalized list of card codes, or raises ValueError with specific details.
    """
    normalized = [normalize_card(c) for c in cards]

    if include_jokers is None:
        if len(normalized) == 52:
            include_jokers = False
        elif len(normalized) == 54:
            include_jokers = True
        else:
            raise ValueError(
                f"Deck must contain exactly 52 cards (or 54 with Jokers), got {len(normalized)}."
            )

    expected = set(STANDARD_54 if include_jokers else STANDARD_52)
    seen = set()
    duplicates = []
    for c in normalized:
        if c in seen:
            duplicates.append(c)
        seen.add(c)

    if duplicates:
        raise ValueError(f"Duplicate cards in deck: {', '.join(duplicates)}")

    missing = sorted(expected - seen)
    extra = sorted(seen - expected)
    if missing or extra:
        parts = []
        if missing:
            parts.append(f"missing: {', '.join(missing[:8])}" + ("..." if len(missing) > 8 else ""))
        if extra:
            parts.append(f"unexpected: {', '.join(extra[:8])}")
        raise ValueError("Invalid deck composition (" + "; ".join(parts) + ")")

    return normalized


def fisher_yates_shuffle(include_jokers: bool = False) -> List[str]:
    """Generate a cryptographically unbiased random deck order using Fisher-Yates."""
    deck = list(STANDARD_54 if include_jokers else STANDARD_52)
    for i in range(len(deck) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        deck[i], deck[j] = deck[j], deck[i]
    return deck


def missing_cards_from(seen_cards: Iterable[str], expected_cards: Iterable[str]) -> List[str]:
    """Return missing cards preserving their order in `expected_cards`."""
    seen_set = set(seen_cards)
    return [c for c in expected_cards if c not in seen_set]
