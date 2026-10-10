# ChoiceRT_VPixxPixelMode — two-choice visual RT with VPixx Pixel Mode B triggers

Same two-choice reaction time task as `ChoiceRT_EyeLink`, but no eye-tracking. Instead this
example shows how to use Pixel Mode triggers (i.e., the MEG triggers sent through the
DATAPixx3 in Pixel Mode B (blue channel of a 1×1 px patch, exact upper-left screen pixel)).
Built for PsychoPy 2026.2.3, MEG lab display (1920×1080, 120 Hz, 60.6 cm wide, 95 cm viewing
distance → 52.5 px/deg).

Keep `conditions.csv` next to the `.psyexp`. Needs `pypixxlib` in PsychoPy's Python.

## Flow
```
instruct              task instructions (press 7 or 2)           [VPixx setup lives here]
trials loop (2 sides x 20 reps = 40, random)
  trial               blank 0.5 s -> fixation                    trigger 1
                      -> foreperiod U(0.8, 1.5) s -> target      trigger 2 (left) / 4 (right)
                      -> response 7/2 or 1.5 s deadline
thanks                3 s
```

Single block. To change the number of trials, set **nReps** in the `trials` loop: total
trials = 2 × nReps (half left, half right).

## Trigger codes (Pixel Mode B, blue channel)
The trigger pixel uses `colorSpace='rgb255'`, so trigger colours are written literally as
(R, G, B):

| Constant | RGB | Event |
|---|---|---|
| `TRIG_FIXATION` | (0, 0, 1) | fixation cross onset |
| `TRIG_TARGET_L` | (0, 0, 2) | target onset, left |
| `TRIG_TARGET_R` | (0, 0, 4) | target onset, right |
| `TRIG_OFF` | (0, 0, 0) | black, all lines off |

Spare blue values: 8, 16, 32, 64, 128. The target trigger (2 or 4) is chosen by the trial's
target side (`targetSide` in `conditions.csv`).

Each trigger lasts one frame (8.33 ms ≈ 10 samples at 1200 Hz), then the pixel goes back to
black. The comment at the end of `onsetTriggers` shows how to make triggers longer.
Responses are not pixel-triggered: use the button-box BNC channels (7 = left index,
2 = right index).

The trigger edge marks the vsync at which the display *begins* scanning out the frame;
subtract one frame (8.33 ms) if you want perceived-onset timing, as in the oddball script.

## Code components
Every code component starts with a header saying when it runs, what it does, and where each
name it uses comes from. Each one has a single job:

| Routine | Component | Tab(s) | Job |
|---|---|---|---|
| instruct | `vpixxSetup` | Before Experiment | Trigger colours; loads `pypixxlib` |
| | | Begin Experiment | Dummy-mode decision, Run-mode check, connects to the DATAPixx3, turns on Pixel Mode B, registers clean-up, creates the trigger pixel, defines `set_trigger_pixel` / `send_trigger` |
| trial | `stimSettings` | Before Experiment | Screen geometry and stimulus sizes in degrees → pixels |
| | `trialSetup` | Before Experiment | Trial timing (ITI, foreperiod range, deadline) |
| | | Begin Routine | Picks this trial's random foreperiod |
| | | End Routine | Logs `timeout`; sets the trigger pixel black |
| | `onsetTriggers` | Each Frame | Sends trigger 1 at fixation onset and 2/4 at target onset |

### Order rules
Builder runs a routine's components from top to bottom on every frame, so position matters:

- **`trialSetup` must be above `fixation`, `target` and `resp`**: their Start/Stop times use
  `foreperiod`, which `trialSetup` creates at the start of each trial.
- **`onsetTriggers` must be below `fixation` and `target`**: it sees a stimulus switch on in
  the same pass, so the trigger lands on the same screen refresh as the stimulus. Above them,
  every trigger would be one frame late.
- `stimSettings` and `vpixxSetup` only use the Experiment tabs, which run once per session
  regardless of position.

### Why there is no "End Experiment" code
Builder skips End Experiment code when you press Esc. Instead, `vpixxSetup` registers
`close_vpixx` with Python's `atexit`, which runs whenever the experiment quits, normally or
with Esc, and turns Pixel Mode off and disconnects the DATAPixx3.

## Data columns added
`fixation.trigger`, `fixation.vp`, `target.trigger`, `target.vp` (`.trigger` is the blue
value; `.vp` is the DATAPixx3 clock at the trigger flip via `DPxGetTime`), plus `foreperiod`,
`timeout` (1 = no response before the deadline), `dummy_vpixx`. Builder's own
`resp.keys/rt/corr` and onset times remain.

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
- Background is black so the trigger pixel's "off" colour matches the screen.
- Stimulus sizes are set in degrees at the top of `stimSettings`: fixation cross 0.6°
  (32 px), target 1.5° (79 px) at ±6° (±315 px).
- If the response pad sends keypad codes, change allowed keys to `num_7`/`num_2` in `ready`,
  `resp` and in `conditions.csv`.
