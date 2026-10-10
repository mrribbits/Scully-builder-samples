# ChoiceRT_Combined — two-choice auditory RT with EyeLink, Pixel Mode triggers and VPixx audio

All three ChoiceRT examples in one. It uses:
- the EyeLink plugin components from `ChoiceRT_EyeLink`,
- the Pixel Mode B MEG triggers from `ChoiceRT_VPixxPixelMode`,
- the DATAPixx3 audio scheduler from `ChoiceRT_VPixxAudio`.

The stimulus is a tone in the left or right ear. Built for PsychoPy 2026.2.3 and
**psychopy-eyelink** v2.2.1.1, on the MEG lab setup: display 1920×1080, 120 Hz, 60.6 cm wide,
95 cm viewing distance → 52.5 px/deg; EyeLink 1000 Plus in Remote mode at 500 Hz.

## Before you open it
1. Launch PsychoPy first and check that the EyeLink components appear in the Eyetracking
   panel. Then open the file with **File → Open**. If you double-click it instead, the plugin
   components can load as "puzzle pieces".
2. Keep `conditions.csv` and `images/fixTarget.bmp` next to the `.psyexp`.
3. Install `pypixxlib` in PsychoPy's Python.
4. Use **Run**, not Pilot. With the real DATAPixx3, the experiment refuses to start unless the
   window is full screen (see "Run mode" below).

## Flow
```
eyelinkSetup          experimenter screen -> Initialize -> Camera Setup (HV13 calibration + validation)
instruct              task instructions (press 7 or 2); sends TASK_START   [VPixx setup lives here]
eyelinkDriftCheck     one drift check before the trials
triggersOn            Pixel Mode on (nothing shown; ends at once)
trials loop (2 sides x 20 reps = 40, random)
  eyelinkStartRecording   Host backdrop (fixation), status msg, TRIALID, start recording
  trial               blank 0.5 s -> fixation                                   trigger 1
                      -> foreperiod U(0.8, 1.5) s -> tone (left or right ear)   trigger 2 (left) / 4 (right)
                      -> response 7/2, or 1.5 s from tone onset
  eyelinkStopRecording    stop recording, TRIAL_RESULT
thanks                Pixel Mode off; sends TASK_END; 3 s
```
- **Responses:** left index = `7`, right index = `2` (`corrAns` in `conditions.csv`).
- **Number of trials:** set **nReps** in the `trials` loop (total = 2 × nReps).
- **During the trial:** the fixation cross stays on from its onset to the end of the trial,
  and there is no visual target.

## One screen refresh, three events
On the frame the tone is due, `onsetEvents` does three things before the screen refreshes:
1. queues the EDF message `TONE_ONSET_LEFT` / `TONE_ONSET_RIGHT` for that refresh,
2. colours the trigger pixel (0, 0, 2) or (0, 0, 4),
3. sends the DATAPixx3 the "start" command for the tone, timed to that refresh.

At that refresh the tone starts and the MEG trigger line goes high. `resp` starts listening on
the same refresh, so `resp.rt` is the time from tone onset. The tone's start command must be
the **last** VPixx command before the refresh. Anything that calls `DPxWriteRegCache` or
`DPxUpdateRegCache` between it and the refresh erases it. The `.vp` clock readings happen just
after the refresh, so they are safe.

## Pixel Mode is only on during the trials
The EyeLink plugin draws its own calibration and drift-check screens. Whatever colour those
put in the top-left pixel would reach the MEG as junk triggers. So:
- the DATAPixx3 is opened with Pixel Mode **off** (`vpixxSetup`),
- the `triggersOn` routine switches it **on** after the drift check (`pixelModeOn`),
- the thanks screen switches it **off** again (`pixelModeOff`).

## Trigger codes (Pixel Mode B, blue channel)
| Name | RGB | MEG trigger | Event |
|---|---|---|---|
| `TRIG_FIXATION` | (0, 0, 1) | 1 | fixation cross appears |
| `TRIG_TONE_L` | (0, 0, 2) | 2 | tone starts, left ear |
| `TRIG_TONE_R` | (0, 0, 4) | 4 | tone starts, right ear |
| `TRIG_OFF` | (0, 0, 0) | – | black, all lines off |

Unused values: 8, 16, 32, 64, 128. Each trigger lasts one frame (8.3 ms ≈ 10 MEG samples at
1200 Hz); a comment in `onsetEvents` explains why. Responses are not pixel-triggered: use the
button-box BNC channels.

## Sound
- 1000 Hz sine, 100 ms, 10 ms fade-in and fade-out, 48 kHz, 16-bit.
- Copied once into DATAPixx3 memory at the start and replayed every trial.
- The ear comes from the `toneSide` column of `conditions.csv`. The other ear gets nothing.
- Output volume is 0.5 in both ears. The device opens at volume 0, which plays silently with
  no error, so keep the volume lines in `toneSetup`.
- The only remaining delay is acoustic (tubing or loudspeaker to the ear). Measure it once with
  a microphone and subtract it in analysis.

## Where to edit
| To change | Edit (Before Experiment tab) |
|---|---|
| the tone | `toneSetup` |
| trial timing | `trialSetup` |
| screen, viewing distance, cross size (in degrees) | `stimSettings` |
| trigger values | `triggerSetup` |

## Code components
Every code component starts with a comment block. It says when the component runs, what it
does and where each name comes from, including names that Builder or the EyeLink plugin create
out of sight. Each line is explained.

| Component (routine) | Tab(s) | Job |
|---|---|---|
| `elConfig` (eyelinkSetup) | Begin Routine | set 500 Hz; write SESSION_CONFIG |
| `vpixxSetup` (instruct) | Before / Begin Experiment | load pypixxlib; real or dummy mode; full-screen check; connect (Pixel Mode off); close at exit |
| `triggerSetup` (instruct) | Before / Begin Experiment | trigger colours; the trigger pixel; `setTriggerPixel`, `sendTrigger`, `recordVpixxTime` |
| `toneSetup` (instruct) | Before / Begin Experiment | make the tone; audio on, volume, copy the tone to the DATAPixx3; dummy-mode sounds |
| `taskStartMsg` (instruct) | End Routine | write TASK_START |
| `pixelModeOn` (triggersOn) | Begin Routine | switch Pixel Mode on |
| `stimSettings` (trial) | Before Experiment | screen + cross size, degrees → pixels |
| `trialSetup` (trial) | Before Experiment | trial timing |
| | Begin Routine | random foreperiod; tone time; this trial's audio schedule |
| | End Routine | score the response; `timeout`; TRIAL_SUMMARY + timeout EDF messages |
| `onsetEvents` (trial) | Each Frame | trigger 1 at fixation; at the tone: EDF message, trigger 2/4, start the tone |
| `trialLog` (trial) | Begin Experiment / End Routine | create the trial log; add one row per trial |
| `pixelModeOff` (thanks) | Begin Routine | switch Pixel Mode off |
| `taskEndMsg` (thanks) | Begin Routine | write TASK_END |

**Order matters.** Builder runs components from top to bottom.
- **instruct:** `vpixxSetup` → `triggerSetup` → `toneSetup`. The later two use names the
  earlier ones make.
- **trial:**
  1. `stimSettings` and `trialSetup` sit above `fixation` and `resp`, because the cross's
     size, start and duration and `resp`'s start time use values they set.
  2. `onsetEvents` sits below `fixation`. It then sees the cross switch on in the same pass,
     so trigger 1 lands on the same refresh as the cross. Moved above it, trigger 1 would be
     one frame (8.3 ms) late.
  3. `trialLog` sits below `trialSetup`, which works out the response values it writes.
  4. The EyeLink MarkEvents component stays at the bottom.

**No End Experiment code, on purpose.** The EyeLink plugin ends the program itself after
copying the EDF, before Builder reaches its End Experiment tabs. So:
- the DATAPixx3 is closed through Python's `atexit`, which runs at a normal finish, after
  Ctrl-C and after an error;
- the trial log saves each row to disk as it is written.

## EDF messages
| Message | Sent by |
|---|---|
| `SESSION_CONFIG remote_mode sample_rate_500` | elConfig |
| `TASK_START` / `TASK_END` | taskStartMsg / taskEndMsg |
| `TRIALID n` … `TRIAL_RESULT 0` | Start/Stop Record |
| `<offset> fixation_ONSET` / `_OFFSET`, `<offset> Keyboard_EVENT` | MarkEvents |
| `TONE_ONSET_LEFT` / `TONE_ONSET_RIGHT` | onsetEvents (on the tone's refresh) |
| `!V TRIAL_VAR` toneSide, corrAns, foreperiod, response RT/keys/corr | MarkEvents |
| `!V TRIAL_VAR timeout 0/1`, `TRIAL_SUMMARY …` | trialSetup |

## Data
**PsychoPy CSV** adds these columns:

| Column | Meaning |
|---|---|
| `fixation.trigger`, `tone.trigger` | trigger number sent (1; 2 or 4) |
| `fixation.vp`, `tone.vp` | DATAPixx3 clock at that refresh (empty in dummy mode) |
| `tone.started` | PsychoPy clock time of the refresh at which the tone started |
| `foreperiod` | this trial's random wait (s) |
| `timeout` | 1 = no answer within 1.5 s, 0 = answered |
| `dummy_vpixx` | True if run without the DATAPixx3 |

**Trial log** (`…_trials_log.tsv`) has one row per trial and is saved after every trial.
Its columns:
- `participant`, `session`, `date`, `edf_file`
- `trial` and `eyelink_trialid` (the TRIALID in the EDF)
- `tone_side`, `corr_ans`, `foreperiod_s`
- `fixation_onset_s`, `tone_onset_s` (PsychoPy clock)
- `fixation_vp`, `tone_vp` (DATAPixx3 clock)
- `resp_key`, `rt_s` (both `NA` on timeouts), `correct`, `timeout`, `dummy_vpixx`

Everything goes into `results/<EDFname>_<date>/`, together with the EDF.

## Dummy modes (independent)
- **EyeLink:** the Dummy Mode tick box on the `Initialize` component.
- **VPixx:** the `dummy_vpixx` tick box in the start dialog. You get no MEG triggers and empty
  `.vp` columns, and the tone plays through PsychoPy in the correct ear, but **not** precisely
  timed. If `pypixxlib` isn't installed, VPixx dummy mode turns on by itself and a warning is
  printed, so check the console before a real recording.

## Run mode, not Pilot mode
Pilot mode forces an 800×600 window, so the top-left screen pixel belongs to the desktop. With
the real DATAPixx3 the experiment stops with an error in that case. To pilot, tick
`dummy_vpixx`.

## Notes
- **Quitting:** Esc is disabled because calibration and the drift check use it. Press **Ctrl-C**
  during a trial to quit cleanly. The EDF is still retrieved, and the DATAPixx3 is released.
- **Keypad codes:** if the response pad sends them, change the allowed keys to `num_7`/`num_2` in
  `ready`, `resp` and `conditions.csv`.
- **Summary CSV:** turned off, because in 2026.2.3 it crashes at the end of a repeated loop.
