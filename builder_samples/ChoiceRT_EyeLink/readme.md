# ChoiceRT_EyeLink — two-choice visual RT with EyeLink Plugin components

Built for PsychoPy 2026.2.3 and the **psychopy-eyelink** plugin (v2.2.1.1). The tracker is an EyeLink 1000 Plus in Remote mode at 500 Hz in the MEG lab.

## Before you open it
1. Launch PsychoPy first and confirm the EyeLink components appear in the Eyetracking panel. Then open the file with **File → Open**. If you double-click the .psyexp instead, the components can load as "puzzle pieces" (see section 4.3 of the plugin manual).
2. Keep `conditions.csv` and `images/fixTarget.bmp` next to the .psyexp file.

## Flow
```
eyelinkSetup          experimenter screen -> Initialize -> Camera Setup (HV13 calibration + validation, required for Remote mode)
instruct              task instructions (press 7 or 2); sends TASK_START
eyelinkDriftCheck     one drift check before the trials (Esc -> Camera Setup to recalibrate, O to return)
trials loop (N = 2 sides x nReps, random; default nReps 20 -> 40 trials)
  eyelinkStartRecording   Host backdrop (fixation + both target boxes), status msg, TRIALID, start recording
  trial                   fixation 0.2 s -> foreperiod U(0.8,1.5) s -> target (1.5 s deadline) / response
  eyelinkStopRecording    stop recording, TRIAL_RESULT
thanks                sends TASK_END
```

**To change N:** open the `trials` loop and set **nReps**. Each rep is one left trial and one right trial, so N = 2 × nReps.

## Code components
Every code component starts with a comment block that says when it runs and what it does, and each line is explained.

| Component (routine) | Tab(s) | Job |
|---|---|---|
| `elConfig` (eyelinkSetup) | Begin Routine | set 500 Hz; write SESSION_CONFIG |
| `taskStartMsg` (instruct) | End Routine | write TASK_START |
| `stimSettings` (trial) | Before Experiment | screen + stimulus sizes, degrees → pixels |
| `trialSetup` (trial) | Begin / End Routine | random foreperiod; score the response; TRIAL_SUMMARY + timeout messages |
| `targetOnsetMsg` (trial) | Begin Routine / Each Frame | TARGET_ONSET_LEFT/RIGHT on the target's first flip |
| `trialLog` (trial) | Begin Experiment / End Routine | create the trial log; add one row per trial |
| `taskEndMsg` (thanks) | Begin Routine | write TASK_END |

**Order inside the trial routine matters.** Builder runs components from top to bottom:
1. `stimSettings` and `trialSetup` sit above the stimuli, because the target's start time uses `foreperiod`.
2. `targetOnsetMsg` sits below `target`.
3. `trialLog` sits below `trialSetup`.
4. MarkEvents stays at the bottom.

## Stimuli (1920×1080 px, 60.6 cm wide, 95 cm viewing distance → 52.5 px/deg)
| Item | Size | Position |
|---|---|---|
| Fixation cross | 0.6° (32 px) | centre |
| Target disc | 1.5° (79 px) | ±6° (±315 px) horizontally |

To change the screen size, viewing distance or stimulus sizes, edit the numbers at the top of the **Before Experiment** tab of the `stimSettings` component. Sizes are entered in degrees and converted to pixels automatically.

## Responses
`7` = left index finger (left target) and `2` = right index finger (right target). If the MEG response pad sends keypad codes, change the allowed keys to `num_7`/`num_2` in the `resp` component and in `conditions.csv`.

## Dummy mode
Use the **Dummy Mode** checkbox on the `Initialize` component (eyelinkSetup routine).
- Ticked: runs without a tracker; drift checks and calibration are skipped.
- Unticked (default, for real data): connects to 100.1.1.1. If no tracker answers, the plugin asks whether to continue in dummy mode.

## Tracker settings
The `elConfig` code component (eyelinkSetup routine) sends `sample_rate 500` when not in dummy mode.

Remote mode itself is chosen on the Host PC: Set Options → camera mount/configuration, plus the forehead target sticker. There is a commented line (`elcl_select_configuration = RTABLER`) if you'd rather force the configuration from the script.

## EDF messages
| Message | Sent by |
|---|---|
| `SESSION_CONFIG remote_mode sample_rate_500` | elConfig (session note when 500 Hz is set) |
| `TASK_START` / `TASK_END` | taskStartMsg / taskEndMsg |
| `TRIALID n` … `TRIAL_RESULT 0` | Start/Stop Record |
| `<offset> fixation_ONSET`, `<offset> target_ONSET`, `*_OFFSET` | MarkEvents (flip-locked) |
| `TARGET_ONSET_LEFT` / `TARGET_ONSET_RIGHT` | targetOnsetMsg (sent on the target's first flip; condition in the name) |
| `<offset> Keyboard_EVENT` (response) | MarkEvents |
| `!V TRIAL_VAR` targetSide, targetX, corrAns, foreperiod | MarkEvents (trial condition) |
| `!V TRIAL_VAR` Keyboard.rt(s), Keyboard.keys, Keyboard.corr | MarkEvents (response) |
| `!V TRIAL_VAR timeout 0/1` | trialSetup |
| `TRIAL_SUMMARY trial= side= key= rt= corr= timeout=` | trialSetup |
| Data Viewer drawing messages and interest areas (fixation + target; ellipse, 20 px margin) | MarkEvents |

The interest-area files (`aoi/`) and drawing lists are saved in the session folder under `results/`, next to the EDF.

## Display latency (projector)
In the MEG lab, a frame appears on the projector screen **one frame (≈8.33 ms) after**
PsychoPy's flip, because the projector adds one frame of delay. Everything this experiment
times is locked to the flip, not to when the image is actually visible:
- **EDF messages:** `fixation_ONSET`, `target_ONSET` and `TARGET_ONSET_LEFT/RIGHT` are about
  8.33 ms before the stimulus is visible. Gaze responses to the target (e.g. saccade latency)
  measured from these messages are 8.33 ms too long.
- **Trial log:** `fixation_onset_s` and `target_onset_s` are flip times. Add 8.33 ms for the
  visible onset.
- **Reaction time:** `resp.rt` / `rt_s` starts at the flip, so the true RT is the value
  **− 8.33 ms**.

## Trial log (`<participant>_ChoiceRT_EyeLink_<date>_trials_log.tsv`)
A tab-separated file with one row per trial, written and flushed after every trial, so rows survive a Ctrl-C abort. Its rows match the EDF by `eyelink_trialid` (= the `TRIALID` number).

| Column | Meaning |
|---|---|
| participant, session, date | from the start-up dialog |
| edf_file | local EDF name in `results/` |
| trial | trial number (1…N) |
| eyelink_trialid | `TRIALID` number in the EDF |
| target_side, target_x_pix, corr_ans | condition |
| foreperiod_s | fixation-to-target interval |
| fixation_onset_s, target_onset_s | flip times on the PsychoPy global clock |
| resp_key, rt_s | response; RT is from target onset (`NA` on timeouts) |
| correct, timeout | 1/0 |

## Output files
Everything for a session goes into one folder, `results/<EDFname>_<YYYY_MM_DD_HH_MM>/`:
- `<EDFname>_<date>.EDF`: eye data, copied from the Host PC at the end of the run
- `aoi/`, `graphics/`: Data Viewer interest areas and drawing lists
- `<participant>_ChoiceRT_EyeLink_<date>.csv`: PsychoPy wide CSV (one row per routine/trial)
- `..._trials_log.tsv`: the trial log described above
- `....log`: PsychoPy log at the "exp" level (stimulus onsets, key presses, routine events)
- `....psydat`: PsychoPy pickle

The summary CSV ("Save csv file") is turned off: in PsychoPy 2026.2.3 it crashes at the end of a repeated loop (`IndexError` in `TrialHandler2.saveAsText`).

## Other notes
- **Quitting:** "Enable escape" is off, because Esc is used during calibration and drift checks. Press **Ctrl-C** during a trial to quit cleanly; the EDF is still retrieved.
