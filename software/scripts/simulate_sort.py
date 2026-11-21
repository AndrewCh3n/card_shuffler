#!/usr/bin/env python3
"""CLI simulator to verify single-pass sorting, slot mapping, and fault recovery without hardware."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running directly as `python3 scripts/simulate_sort.py` from `software/`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shuffler.cards import fisher_yates_shuffle, new_deck_order
from shuffler.controller import ShufflerController, ShufflerState


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulate a full single-pass 52/54-card sort.")
    parser.add_argument(
        "--mode",
        choices=["random", "ndo", "fault-demo"],
        default="random",
        help="Simulation scenario to run.",
    )
    parser.add_argument("--jokers", action="store_true", help="Include 2 Jokers (54-card deck).")
    args = parser.parse_args()

    ctrl = ShufflerController(simulation=True, sim_step_delay_s=0.0)

    if args.mode == "ndo":
        target = new_deck_order(include_jokers=args.jokers)
        label = f"New Deck Order ({len(target)})"
        fault = None
    elif args.mode == "fault-demo":
        target = new_deck_order(include_jokers=args.jokers)
        label = f"Fault Recovery Demo ({len(target)})"
        fault = "face_up"
    else:
        target = fisher_yates_shuffle(include_jokers=args.jokers)
        label = f"Random Shuffle ({len(target)})"
        fault = None

    print(f"Starting simulated sort: {label}")
    ctrl.start_sort(target_order=target, mode_label=label, sim_fault=fault)

    state = ctrl.wait_until_done(timeout=10.0)
    if state == ShufflerState.PAUSED_ALERT:
        snap = ctrl.snapshot()
        print(f"  -> Paused as expected on alert [{snap['alert']['code']}]: {snap['alert']['message']}")
        print("  -> Simulating user flipping card face-down & tapping Resume...")
        ctrl.resume(fix_simulated_fault=True)
        state = ctrl.wait_until_done(timeout=10.0)

    snap = ctrl.snapshot()
    if state != ShufflerState.COMPLETE:
        print(f"FAILED: Ended in unexpected state {state.value}", file=sys.stderr)
        return 1

    exact_match = snap["output_deck"] == target
    print(f"Result: {state.value} | Cards placed: {snap['placed_count']}/{snap['expected_count']}")
    print(f"Exact top-to-bottom deck match after gravity drop: {exact_match}")
    print(f"Top 5 cards of output deck: {snap['output_deck'][:5]}")
    print(f"Bottom 5 cards of output deck: {snap['output_deck'][-5:]}")
    return 0 if exact_match else 1


if __name__ == "__main__":
    raise SystemExit(main())
