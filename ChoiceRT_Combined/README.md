# ChoiceRT_Combined — two-choice auditory RT with EyeLink, Pixel Mode triggers and VPixx audio

All three ChoiceRT examples in one: the EyeLink plugin components from `ChoiceRT_EyeLink`,
the Pixel Mode B MEG triggers from `ChoiceRT_VPixxPixelMode`, and the DATAPixx3 audio scheduler
from `ChoiceRT_VPixxAudio`. Built for PsychoPy 2026.2.3 and **psychopy-eyelink** v2.2.1.1,
MEG lab display (1920×1080, 120 Hz) and EyeLink 1000 Plus (Remote mode, 500 Hz).

## Before you open it
1. Launch PsychoPy first and check that the EyeLink components appear in the Eyetracking
   panel, then open the file with **File → Open** (double-clicking can load the plugin
   components as "puzzle pieces").
2. Keep `conditions.csv` and `images/fixTarget.bmp` next to the `.psyexp`.
3. `pypixxlib` must be installed in PsychoPy's Python.
4. Use **Run**, not Pilot. With real VPixx hardware the experiment refuses to start unless
   the window is full screen (see "Run mode" below).

## Flow
```
eyelinkSetup          experimenter screen -> Initialize -> Camera Setup (HV13 calibration + validation)
instruct              task instructions (press 7 or 2); sends TASK_START   [vpixx init lives here]
eyelinkDriftCheck     one drift check before the trials
trials loop (2 sides x 20 reps = 40, random)
  eyelinkStartRecording   Host backdrop (fixation), status msg, TRIALID, start recording
  trial               blank 0.5 s -> fixation                                   trigger 1
                      -> foreperiod U(0.8, 1.5) s -> tone (left or right ear)   trigger 2 (left) / 4 (right)
                      -> response 7/2 or 1.5 s deadline
  eyelinkStopRecording    stop recording, TRIAL_RESULT
thanks                3 s; sends TASK_END; Pixel Mode off
```
To change the number of trials, set **nReps** in the `trials` loop (total = 2 × nReps).
The fixation cross stays on from its onset to the end of the trial; there is no visual target.

## One flip, three events
On the tone frame, `trialCode` does three things before that frame's flip, in this order:
1. queues the EDF message `TONE_ONSET_LEFT` / `TONE_ONSET_RIGHT` for the flip,
2. puts the tone trigger (2 or 4) on the trigger pixel,
3. arms the audio schedule (`DPxStartAudSched` + `DPxWriteRegCacheAfterVideoSync`).

At that flip's vsync the DATAPixx3 starts the tone and the trigger line goes high, and
Builder's `resp` clock starts on the same flip, so `resp.rt` is time from tone onset.
`arm_tone()` must stay the last VPixx call before the flip. Nothing may call
`DPxWriteRegCache` or `DPxUpdateRegCache` between it and the flip, or the pending start bit
is overwritten. The `.vp` time stamps run after the flip, so they are safe.

## Pixel Mode is only on during the trials
EyeLink calibration and drift-check screens are drawn by the plugin, and anything in the
top-left pixel would reach the MEG trigger lines. So:
- At startup the DATAPixx3 is opened with Pixel Mode **off**.
- `pixel_mode_on()` runs in Begin Routine of the first trial (after the drift check).
- `pixel_mode_off()` runs at the start of the thanks screen.

The 1×1 trigger patch is drawn black on every flip for the whole session.

## Trigger codes (Pixel Mode B, blue channel)
| Constant | RGB | Event |
|---|---|---|
| `TRIG_FIXATION` | (0, 0, 1) | fixation cross onset |
| `TRIG_TONE_L` | (0, 0, 2) | tone onset, left ear |
| `TRIG_TONE_R` | (0, 0, 4) | tone onset, right ear |
| `TRIG_RESET` | (0, 0, 0) | black, all lines low |

Spare values: 8, 16, 32, 64, 128. Each trigger is held for `TRIG_HOLD_FRAMES` (1 frame =
8.33 ms) and then reset to black. Responses are not pixel-triggered: use the button-box
BNC channels.

## Sound
1000 Hz sine, 100 ms, 10 ms cosine ramps, 48 kHz, written once to DATAPixx3 RAM and
replayed each trial to one ear (`lrMode` from `toneSide` in `conditions.csv`). Codec volume
0.5 (`VPIXX_AUDIO_VOLUME`). The codec opens at 0, which is silent with no error, so keep
that line. Remaining latency is acoustic (tubing or speaker to ear): measure it once and
subtract in analysis.

## Where the code is
- **`vpixx`** (instruct routine)
  - *Before Experiment*: trigger codes, tone parameters, `pypixxlib` import, tone generation.
  - *Begin Experiment*: opens the DATAPixx3 (audio codec, tone buffer, Pixel Mode off).
    It defines the trigger helpers (`send_trigger`, `tick_trigger`, `reset_trigger`,
    `pixel_mode_on/off`), the audio helpers (`prep_tone`, `arm_tone`) and `close_vpixx`.
    It also creates the trigger patch and registers `close_vpixx` with atexit.
  - *End Experiment*: pixel black, Pixel Mode off, audio stopped, device closed.
- **`trialCode`** (trial routine, after `fixation` and `resp`, before `MarkEvents`): timing
  constants, foreperiod, triggers, tone, trial log.
- **`taskEndMsg`** (thanks): Pixel Mode off, `TASK_END`.

## EDF messages
| Message | Sent by |
|---|---|
| `SESSION_CONFIG remote_mode sample_rate_500` | elConfig |
| `TASK_START` / `TASK_END` | instruct / thanks code |
| `TRIALID n` … `TRIAL_RESULT 0` | Start/Stop Record |
| `<offset> fixation_ONSET` / `_OFFSET`, `<offset> Keyboard_EVENT` | MarkEvents |
| `TONE_ONSET_LEFT` / `TONE_ONSET_RIGHT` | trialCode (on the tone flip) |
| `!V TRIAL_VAR` toneSide, corrAns, foreperiod, response RT/keys/corr | MarkEvents |
| `!V TRIAL_VAR timeout 0/1`, `TRIAL_SUMMARY …` | trialCode |

## Data
**PsychoPy CSV** adds these columns:
- `fixation.trigger` and `fixation.vp`
- `tone.trigger` and `tone.vp` (`.vp` is the DATAPixx3 clock at that flip)
- `tone.started`: PsychoPy time of the tone flip
- `foreperiod`, `timeout` and `dummy_vpixx`

**Trial log** (`…_trials_log.tsv`, one row per trial, flushed every trial):
- `participant`, `session`, `date`, `edf_file`
- `trial` and `eyelink_trialid`
- `tone_side`, `corr_ans`, `foreperiod_s`
- `fixation_onset_s`, `tone_onset_s` (PsychoPy clock)
- `fixation_vp`, `tone_vp` (DATAPixx3 clock)
- `resp_key`, `rt_s`, `correct`, `timeout`, `dummy_vpixx`

Everything goes into `results/<EDFname>_<date>/`, together with the EDF.

## Dummy modes (independent)
- **EyeLink:** Dummy Mode checkbox on the `Initialize` component.
- **VPixx:** `dummy_vpixx` in the start dialog. This gives no triggers, empty `.vp` columns
  and PsychoPy sound in the correct ear, but **not** vsync-locked. If `pypixxlib` is
  missing, VPixx dummy mode is forced and a warning is logged.

## Run mode, not Pilot mode
Pilot mode forces an 800×600 window, so the top-left screen pixel belongs to the desktop.
With real VPixx hardware the experiment stops with an error in that case. To pilot, tick
`dummy_vpixx`.

## Notes
- **Quitting:** Escape is disabled because the calibration and drift-check screens use it.
  Press **Ctrl-C** during a trial to quit cleanly. The EDF is still retrieved, and the
  DATAPixx3 is released by atexit.
- **Keypad codes:** if the response pad sends keypad codes, change the allowed keys to
  `num_7`/`num_2` in `ready`, `resp` and `conditions.csv`.
- **Summary CSV:** this is turned off. In 2026.2.3 it crashes at the end of a repeated loop.
