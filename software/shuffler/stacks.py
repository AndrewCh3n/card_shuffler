"""Custom named stack persistence (JSON store) for the Phone Web UI."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from .cards import new_deck_order, validate_deck_order

DEFAULT_STORE_PATH = Path(__file__).resolve().parent.parent / "data" / "stacks.json"


@dataclass
class SavedStack:
    """A named target deck order (index 0 = top of finished face-down deck)."""

    id: str
    name: str
    include_jokers: bool
    cards: List[str]
    updated_at: str
    builtin: bool = False


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "custom-stack"


class StackStore:
    """Manages reading/writing named custom stacks to a local JSON file."""

    def __init__(self, path: Path | str = DEFAULT_STORE_PATH) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._stacks: Dict[str, SavedStack] = {}
        self._load_or_init()

    def _default_stacks(self) -> Dict[str, SavedStack]:
        now = datetime.now(timezone.utc).isoformat()
        ndo = SavedStack(
            id="new-deck-order",
            name="New Deck Order (52)",
            include_jokers=False,
            cards=new_deck_order(include_jokers=False),
            updated_at=now,
            builtin=True,
        )
        return {ndo.id: ndo}

    def _load_or_init(self) -> None:
        if not self.path.exists():
            self._stacks = self._default_stacks()
            self._save()
            return

        with self.path.open("r", encoding="utf-8") as fh:
            raw = json.load(fh)

        loaded: Dict[str, SavedStack] = {}
        for item in raw.get("stacks", []):
            stack = SavedStack(
                id=item["id"],
                name=item["name"],
                include_jokers=bool(item.get("include_jokers", len(item["cards"]) == 54)),
                cards=validate_deck_order(item["cards"]),
                updated_at=item.get("updated_at", ""),
                builtin=bool(item.get("builtin", False)),
            )
            loaded[stack.id] = stack

        # Ensure baseline New Deck Order is always present
        if "new-deck-order" not in loaded:
            loaded.update(self._default_stacks())
        self._stacks = loaded

    def _save(self) -> None:
        payload = {"stacks": [asdict(s) for s in self._stacks.values()]}
        tmp_path = self.path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        tmp_path.replace(self.path)

    def list_stacks(self) -> List[SavedStack]:
        return sorted(
            self._stacks.values(),
            key=lambda s: (not s.builtin, s.name.lower()),
        )

    def get_stack(self, stack_id: str) -> Optional[SavedStack]:
        return self._stacks.get(stack_id)

    def save_stack(
        self,
        name: str,
        cards: Sequence[str],
        stack_id: Optional[str] = None,
    ) -> SavedStack:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Stack name cannot be empty.")

        validated_cards = validate_deck_order(cards)
        include_jokers = len(validated_cards) == 54

        if stack_id:
            existing = self._stacks.get(stack_id)
            if existing and existing.builtin:
                raise ValueError("Built-in stack cannot be overwritten; save under a new name.")
            sid = stack_id
        else:
            base = _slugify(clean_name)
            sid = base
            counter = 2
            while sid in self._stacks:
                sid = f"{base}-{counter}"
                counter += 1

        stack = SavedStack(
            id=sid,
            name=clean_name,
            include_jokers=include_jokers,
            cards=validated_cards,
            updated_at=datetime.now(timezone.utc).isoformat(),
            builtin=False,
        )
        self._stacks[sid] = stack
        self._save()
        return stack

    def delete_stack(self, stack_id: str) -> bool:
        stack = self._stacks.get(stack_id)
        if not stack:
            return False
        if stack.builtin:
            raise ValueError("Built-in stack cannot be deleted.")
        del self._stacks[stack_id]
        self._save()
        return True
