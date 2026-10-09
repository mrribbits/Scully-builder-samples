# ChoiceRT_VPixxPixelMode — two-choice visual RT with VPixx Pixel Mode B triggers

Same two-choice reaction time task as `ChoiceRT_EyeLink`, but no eye-tracking. Instead this
example shows how to use Pixel Mode triggers (i.e., the MEG triggers sent through the
DATAPixx3 in Pixel Mode B (blue channel of a 1×1 px patch, exact upper-left screen pixel)).
Built for PsychoPy 2026.2.3, MEG lab display (1920×1080, 120 Hz, 60.6 cm wide, 95 cm viewing
distance → 52.5 px/deg).

Keep `conditions.csv` next to the `.psyexp`. Needs `pypixxlib` in PsychoPy's Python.

## Flow
```
instruct              task instructions (press 7 or 2)           [vpixx init lives here]
trials loop (2 sides x 20 reps = 40, random)
  trial               blank 0.5 s -> fixation                    trigger 1
                      -> foreperiod U(0.8, 1.5) s -> target      trigger 2 (left) / 4 (right)
                      -> response 7/2 or 1.5 s deadline
thanks                3 s
```

Single block. To change the number of trials, set **nReps** in the `trials` loop: total
trials = 2 × nReps (half left, half right).

## Trigger codes (Pixel Mode B, blue channel)
The patch uses `colorSpace='rgb255'`, so trigger colours are written literally as (R, G, B):

| Constant | RGB | Event |
|---|---|---|
| `TRIG_FIXATION` | (0, 0, 1) | fixation cross onset |
| `TRIG_TARGET_L` | (0, 0, 2) | target onset, left |
| `TRIG_TARGET_R` | (0, 0, 4) | target onset, right |
| `TRIG_RESET` | (0, 0, 0) | black, all lines low |

Spare blue values: 8, 16, 32, 64, 128. The target trigger (2 or 4) is chosen by the trial's
target side (`targetSide` in `conditions.csv`).

Each trigger is held for `TRIG_HOLD_FRAMES` (default 1 frame = 8.33 ms ≈ 10 samples at
1200 Hz) and the pixel is then reset to black. Responses are not pixel-triggered: use the
button-box BNC channels (7 = left index, 2 = right index).

The trigger edge marks the vsync at which the display *begins* scanning out the frame;
subtract one frame (8.33 ms) if you want perceived-onset timing, as in the oddball script.

## Where the code is
- **`vpixx`** code component (instruct routine)
  - *Before Experiment* (module level): trigger constants, `pypixxlib` import with dummy
    fallback, and the trigger colour constants.
  - *Begin Experiment* (inside Builder's `run()`): opens the DATAPixx3, enables Pixel Mode B,
    defines `send_trigger`, `tick_trigger`, `reset_trigger`, `close_vpixx` (they need `win`,
    `thisExp` and `dp`, which only exist inside `run()`), creates the 1×1 patch (auto-drawn
    on every flip) and registers `close_vpixx` with atexit so the device is released after Esc.
  - *End Experiment*: pixel to black, pixel mode off, device closed.
- **`trialCode`** sits *after* the stimuli in the trial routine. On the frame a
  stimulus starts (`frameNStart == frameN`) it calls `send_trigger`, so the trigger lands on
  the same flip as the stimulus. `tick_trigger()` runs first every frame and resets the pixel.
- Geometry and timing constants: Before Experiment tab of `trialCode`.

## Data columns added
`fixation.trigger`, `fixation.vp`, `target.trigger`, `target.vp` (`.trigger` is the blue value; `.vp` is the DATAPixx3 clock at the trigger flip via `DPxGetTime`), plus `foreperiod`,
`timeout`, `dummy_vpixx`. Builder's own `resp.keys/rt/corr` and onset times remain.

## Run mode, not Pilot mode
Pixel Mode reads the top-left pixel of the whole screen, so the window must be full screen.
Builder's Pilot mode forces an 800×600 window, which leaves the desktop in that corner and
puts a constant garbage value on the trigger lines. With real hardware the experiment refuses
to start unless it is full screen in Run mode; pilot with `dummy_vpixx` ticked instead.

## Dummy mode
Set `dummy_vpixx` in the start dialog to run without the DATAPixx3 (no triggers, `.vp`
columns empty). If `pypixxlib` isn't installed it switches to dummy mode automatically and
logs a warning — check the console before a real recording.

## Notes
- Background is black so the reset value matches the screen.
- If the response pad sends keypad codes, change allowed keys to `num_7`/`num_2` in `ready`,
  `resp` and in `conditions.csv`.
