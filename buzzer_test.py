#!/usr/bin/env python3
"""
HW-508 Piezo Buzzer Hardware Test — PYNQ-Z2
============================================
Verifies the buzzer wiring and generates an 880 Hz tone.

Pin connections (PMODA, top row):
  ┌────────┬──────────────────────────────────┐
  │ HW-508 │ PMODA connector                  │
  ├────────┼──────────────────────────────────┤
  │   "+"  │ Data 3  (pin 4, index 3)  ← PWM │
  │   "-"  │ GND     (pin 5)                  │
  │ center │ 3.3 V   (pin 6)                  │
  └────────┴──────────────────────────────────┘

All three module pins land on the same six-pin row, so no jumper wires
cross between rows.

Run on PYNQ-Z2:
    python3 buzzer_test.py
"""

import time
from pynq.overlays.base import BaseOverlay
from pynq.lib import Pmod_GPIO

# ── Constants ─────────────────────────────────────────────────────────────────
PMODA_PIN_INDEX  = 3      # 0-indexed data pin  (D0=0 … D3=3)
TEST_FREQ_HZ     = 880    # A5 — same tone used in alarm_code.ipynb
TONE_DURATION_S  = 1.0    # long tone for initial verification
BEEP_DURATION_S  = 0.15   # each short beep
BEEP_GAP_S       = 0.15   # silence between beeps
BEEP_COUNT       = 3      # number of confirmation beeps

# ── GPIO helpers ──────────────────────────────────────────────────────────────
_buzzer: Pmod_GPIO = None  # module-level handle; set in main()


def write_buzzer_gpio(val: int) -> None:
    """Write 0 or 1 to the buzzer signal pin."""
    _buzzer.write(val)


def play_tone(freq_hz: float, duration_s: float) -> dict:
    """
    Software square-wave at freq_hz for duration_s seconds.

    Implements the pseudocode from the assignment spec:
        write HIGH  →  sleep 1/(2·f)  →  write LOW  →  sleep 1/(2·f)

    Returns a dict with actual measured frequency and cycle count.
    Note: Python sleep granularity on Linux is ~50–100 µs; at 880 Hz the
    half-period is ≈ 568 µs so timing will be close but not perfect.
    """
    if freq_hz <= 0:
        return {"cycles": 0, "measured_hz": 0.0}

    half_period = 1.0 / (2.0 * freq_hz)
    cycles      = 0
    t_start     = time.monotonic()
    t_end       = t_start + duration_s

    while time.monotonic() < t_end:
        write_buzzer_gpio(1)
        time.sleep(half_period)
        write_buzzer_gpio(0)
        time.sleep(half_period)
        cycles += 1

    elapsed = time.monotonic() - t_start
    return {
        "cycles":      cycles,
        "measured_hz": round(cycles / elapsed, 1) if elapsed > 0 else 0.0,
        "elapsed_s":   round(elapsed, 4),
    }


# ── Test sequence ─────────────────────────────────────────────────────────────
def run_test() -> None:
    global _buzzer

    sep = "=" * 54
    print(sep)
    print("  HW-508 Piezo Buzzer Test  —  PYNQ-Z2")
    print(sep)
    print(f"  Target frequency : {TEST_FREQ_HZ} Hz  (half-period ≈ "
          f"{1000.0 / (2 * TEST_FREQ_HZ):.0f} µs)")
    print(f"  PMODA pin index  : {PMODA_PIN_INDEX}  (physical connector pin 4)")
    print()

    # ── Step 1: load overlay ──────────────────────────────────────────────────
    print("[1/4] Loading base overlay …", end=" ", flush=True)
    base = BaseOverlay("base.bit")
    print("OK")

    # ── Step 2: initialise GPIO ───────────────────────────────────────────────
    print("[2/4] Configuring PMODA data-3 as output …", end=" ", flush=True)
    _buzzer = Pmod_GPIO(base.PMODA, PMODA_PIN_INDEX, "out")
    write_buzzer_gpio(0)   # start silent
    print("OK")
    print()

    # ── Step 3: 1-second tone ─────────────────────────────────────────────────
    print(f"[3/4] Playing {TEST_FREQ_HZ} Hz tone for {TONE_DURATION_S} s …")
    result = play_tone(TEST_FREQ_HZ, TONE_DURATION_S)
    print(f"      {result['cycles']} cycles in {result['elapsed_s']} s  "
          f"→  measured ≈ {result['measured_hz']} Hz")

    time.sleep(0.4)   # brief pause before beeps

    # ── Step 4: 3 short confirmation beeps ───────────────────────────────────
    print(f"[4/4] Playing {BEEP_COUNT}× short beep ({BEEP_DURATION_S} s each) …")
    for i in range(1, BEEP_COUNT + 1):
        r = play_tone(TEST_FREQ_HZ, BEEP_DURATION_S)
        print(f"      Beep {i}/{BEEP_COUNT}  —  {r['cycles']} cycles, "
              f"≈ {r['measured_hz']} Hz")
        if i < BEEP_COUNT:
            time.sleep(BEEP_GAP_S)

    # ── Clean up ──────────────────────────────────────────────────────────────
    write_buzzer_gpio(0)   # ensure pin ends LOW (buzzer silent)
    print()
    print("Buzzer de-energised.  Test complete.")

    # ── Pass / warn check ─────────────────────────────────────────────────────
    tolerance_pct = 15
    lo = TEST_FREQ_HZ * (1 - tolerance_pct / 100)
    hi = TEST_FREQ_HZ * (1 + tolerance_pct / 100)
    measured = result["measured_hz"]
    if lo <= measured <= hi:
        print(f"PASS  —  measured {measured} Hz is within "
              f"±{tolerance_pct}% of {TEST_FREQ_HZ} Hz")
    else:
        print(f"WARN  —  measured {measured} Hz is outside "
              f"±{tolerance_pct}% of {TEST_FREQ_HZ} Hz")
        print("         Check wiring or increase OS scheduling priority.")
    print(sep)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_test()
