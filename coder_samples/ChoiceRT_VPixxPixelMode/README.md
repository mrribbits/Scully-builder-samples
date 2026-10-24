# ChoiceRT_VPixxPixelMode (Coder): two-choice visual RT with VPixx Pixel Mode B triggers

This is the Coder (plain Python) version of `builder_samples/ChoiceRT_VPixxPixelMode`. The
task, timing, trigger codes and data columns are the same. The script does by hand what
Builder's components and code components do, and the comments say which Builder piece each
part replaces. Built for PsychoPy 2026.2.3 and the MEG lab display (1920×1080, 120 Hz,
60.6 cm wide, 95 cm viewing distance → 52.5 px/deg).

Keep `conditions.csv` next to `ChoiceRT_VPixxPixelMode.py`. You need `pypixxlib` installed in
PsychoPy's Python.

## Running it
1. Open `ChoiceRT_VPixxPixelMode.py` in PsychoPy's **Coder** window (File → Open).
2. Click **Run**, not Pilot. Pilot uses a small window, and with the real DATAPixx3 the
   script will not start unless the window is full screen.
3. To test without the DATAPixx3, tick `dummy_vpixx` in the start dialog.
4. Press **Esc** to stop early. The data collected so far are saved.

## Flow
```
instructions          press 7 or 2
trials (2 sides x 20 reps = 40, random)
  blank 0.5 s -> fixation                    trigger 1
  -> foreperiod U(0.8, 1.5) s -> target      trigger 2 (left) / 4 (right)
  -> response 7/2 or 1.5 s deadline
thanks                3 s
```
To change the number of trials, set `N_REPS` in section 1. Total trials = 2 × `N_REPS`.

## Where to edit (section 1 of the script)
| To change | Edit |
|---|---|
| screen size, width, viewing distance | `SCREEN_SIZE_PX`, `SCREEN_WIDTH_CM`, `VIEWING_DISTANCE_CM` |
| stimulus sizes (degrees) | `FIXATION_SIZE_DEG`, `TARGET_SIZE_DEG`, `TARGET_OFFSET_DEG` |
| timing | `ITI`, `FOREPERIOD_MIN/MAX`, `RESP_DEADLINE` |
| trigger values | `TRIG_FIXATION`, `TRIG_TARGET_L`, `TRIG_TARGET_R` |
| response keys | `RESP_KEYS` (and `conditions.csv`) |

## Script layout
| Section | What it does | Builder equivalent |
|---|---|---|
| 0 | imports; loads `pypixxlib` (or notes that it is missing) | top of the compiled script; `vpixxSetup` Before Experiment |
| 1 | settings and trigger colours | `stimSettings`, `trialSetup`, `vpixxSetup` Before Experiment |
| 2 | degrees → pixels | `stimSettings` |
| 3–5 | start dialog, data files, window | Experiment Settings |
| 6 | dummy-mode decision, full-screen check, connect, Pixel Mode B on, `atexit` cleanup | `vpixxSetup` Begin Experiment |
| 7 | the trigger pixel; `set_trigger_pixel`, `send_trigger`, `record_vpixx_time` | `vpixxSetup` Begin Experiment |
| 8 | stimuli, keyboard, `save_and_quit`, Esc check | the stimulus and Keyboard components |
| 9 | clocks | Builder's `globalClock` and `routineTimer` |
| 10 | instructions screen | routine `instruct` |
| 11 | trials loop, one `while` pass per frame | loop `trials` + routine `trial` (+ `onsetTriggers` Each Frame) |
| 12 | thank-you screen; save and quit | routine `thanks` |

### How a trigger lands on the same refresh as its stimulus
On every frame, the trial loop does three things in this order: it sets the trigger pixel to
black, it switches on any stimulus that is due and sets its trigger colour, and then it
calls `win.flip()`. The stimulus and its trigger are therefore drawn into the same frame.
In Builder this is why `onsetTriggers` has to sit below `fixation` and `target`. In Coder,
the order of the lines inside the loop does the same job.

### Cleanup without "End Experiment" code
`close_vpixx` is registered with Python's `atexit`. It runs however the script ends: a normal
finish, Esc, or an error. It turns Pixel Mode off and disconnects the DATAPixx3.

## Trigger codes (Pixel Mode B, blue channel, `colorSpace='rgb255'`)
| Constant | RGB | Event |
|---|---|---|
| `TRIG_FIXATION` | (0, 0, 1) | fixation cross onset |
| `TRIG_TARGET_L` | (0, 0, 2) | target onset, left |
| `TRIG_TARGET_R` | (0, 0, 4) | target onset, right |
| `TRIG_OFF` | (0, 0, 0) | black, all lines off |

Unused values: 8, 16, 32, 64, 128. Each trigger lasts one frame (8.33 ms ≈ 10 samples at
1200 Hz). Responses are not sent as pixel triggers: use the button-box BNC channels.

## Display latency (projector)
A frame appears on the projector screen **one frame (≈8.33 ms) after** the DATAPixx3 sends
its trigger. That means:
- the target is visible at trigger 2/4 time **+ 8.33 ms** (the same applies to trigger 1);
- the true reaction time is `resp.rt` **− 8.33 ms**;
- `fixation.started`, `target.started` and `target.vp` are flip times, so add 8.33 ms to
  them as well.

## Data
Files are saved as `data/<participant>_<session>_<date>.csv / .psydat / .log`, the same
names Builder uses. The columns match the Builder version: `fixation.trigger`,
`fixation.vp`, `target.trigger`, `target.vp`, `foreperiod`, `timeout`, `dummy_vpixx`,
`resp.keys`, `resp.corr`, `resp.rt`, `fixation.started`, `target.started`, `resp.started`,
plus the `conditions.csv` columns and the loop counters.

## Dummy mode
Tick `dummy_vpixx` to run without the DATAPixx3. No triggers are sent and the `.vp`
columns stay empty. If `pypixxlib` isn't installed, the script switches to dummy mode by
itself and prints a warning, so check the console before a real recording.

## Notes
- The background is black, so the trigger pixel's "off" colour matches the rest of the
  screen.
- If the response pad sends keypad codes, change `RESP_KEYS` to `num_7`/`num_2`, and change
  `conditions.csv` to match.
