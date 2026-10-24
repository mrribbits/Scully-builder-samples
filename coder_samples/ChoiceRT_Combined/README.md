# ChoiceRT_Combined (Coder): two-choice auditory RT with EyeLink, Pixel Mode triggers and VPixx audio

This is the Coder (plain Python) version of `builder_samples/ChoiceRT_Combined`. It combines
the three smaller Coder samples:
- EyeLink eye tracking from `ChoiceRT_EyeLink`
- Pixel Mode B MEG triggers from `ChoiceRT_VPixxPixelMode`
- the DATAPixx3 audio scheduler from `ChoiceRT_VPixxAudio`

The task, timing, trigger codes, EDF messages, Data Viewer files, data columns and trial log
are the same as in the Builder version. If one of the pieces is new to you, read its smaller
sample first.

Built for PsychoPy 2026.2.3 with **psychopy-eyelink** v2.2.1.1 and `pypixxlib`, on the MEG
lab setup:
- display: 1920×1080, 120 Hz, 60.6 cm wide, 95 cm viewing distance → 52.5 px/deg
- eye tracker: EyeLink 1000 Plus in Remote mode at 500 Hz

## Running it
1. Install the psychopy-eyelink plugin and `pypixxlib` in PsychoPy's Python.
2. Keep `conditions.csv` and `images/fixTarget.bmp` next to `ChoiceRT_Combined.py`.
3. Open the script in the **Coder** window and click **Run**, not Pilot. With the real
   DATAPixx3, the script stops with an error unless the window is full screen.
4. The start dialog asks for participant, session, `dummy_vpixx` and the EDF name (at most 8
   characters). On a Mac it also asks whether the screen is a Retina display.
5. **Quitting:** press **Ctrl-C** during a trial. Esc is reserved for calibration. When you
   quit this way, the EDF is still retrieved, the data are saved and the DATAPixx3 is
   released.

## Flow
```
experimenter screen   SPACE -> Camera Setup (HV13)                    [Pixel Mode OFF]
instructions          7, 2 or SPACE; TASK_START
drift check
Pixel Mode ON         (section 18)
trials (2 sides x 20 reps = 40, random)
  Host PC fixation box, TRIALID, start recording
  blank 0.5 s -> fixation                                   trigger 1
  -> foreperiod U(0.8, 1.5) s -> tone (left or right ear)   trigger 2 (left) / 4 (right), TONE_ONSET_*
  -> response 7/2, or 1.5 s from tone onset
  TRIAL_SUMMARY, interest area, stop recording, TRIAL_RESULT 0
thanks                Pixel Mode OFF; TASK_END; 3 s; EDF copied
```

## One screen refresh, three events
On the frame the tone is due, the trial loop (section 19c) prepares three things *before*
calling `win.flip()`:
1. it queues the EDF message `TONE_ONSET_LEFT` / `TONE_ONSET_RIGHT` with `win.callOnFlip`;
2. it colours the trigger pixel (0, 0, 2) or (0, 0, 4);
3. it sends the DATAPixx3 the tone's start command with
   `DPxStartAudSched()` + `DPxWriteRegCacheAfterVideoSync()`.

At that flip the tone starts, the MEG trigger line goes high and the keyboard clock is reset.
`resp.rt` is therefore measured from tone onset. The tone's start command must be the
**last** VPixx command before the flip. The `.vp` clock readings run after the flip, so
they are safe.

## Pixel Mode is only on during the trials
The EyeLink library draws its own calibration and drift-check screens. Whatever colour those
screens put in the top-left pixel would reach the MEG as junk triggers. To prevent this:
- the DATAPixx3 is opened with Pixel Mode **off** (section 9);
- Pixel Mode is switched **on** after the drift check (section 18);
- it is switched **off** again on the thank-you screen (section 20), in `terminate_task`
  and in `closeVpixx`.

## Script layout
| Section | What it does | Builder equivalent |
|---|---|---|
| 1 | all settings: display, timing, triggers, tone, tracker | `stimSettings`, `trialSetup`, `triggerSetup`, `toneSetup` Before Experiment |
| 2 | cross size; makes the tone | `stimSettings`, `toneSetup` |
| 3–7 | dialog, session folder, tracker connection, data files, window | Experiment Settings; EyeLink Initialize |
| 8 | open the EDF, data filters | Initialize |
| 9 | DATAPixx3: dummy decision, full-screen check, connect (Pixel Mode off), `atexit` cleanup | `vpixxSetup` |
| 10 | trigger pixel and functions; tone to DATAPixx3 memory (or dummy sounds) | `triggerSetup`, `toneSetup` |
| 11–12 | EyeLink helpers, `terminate_task`, Data Viewer marking | plugin helpers; MarkEvents |
| 13 | stimuli, keyboard, trial log, Ctrl-C | the stimulus components; `trialLog` |
| 14 | clocks | `globalClock`, `routineTimer` |
| 15 | `elConfig`, SPACE screen, Camera Setup | routine `eyelinkSetup` |
| 16 | instructions; TASK_START | routine `instruct` |
| 17 | drift check | routine `eyelinkDriftCheck` |
| 18 | Pixel Mode on | routine `triggersOn` (`pixelModeOn`) |
| 19a | Host PC drawing, TRIALID, start recording | `eyelinkStartRecording` |
| 19b | foreperiod, audio schedule, trial variables | `trialSetup` Begin Routine, MarkEvents |
| 19c | frame loop: trigger 1 at fixation; at the tone, EDF message + trigger 2/4 + tone | routine `trial` (`onsetEvents` Each Frame) |
| 19d | scoring, TRIAL_SUMMARY, trial log, offsets/interest area, stop recording | `trialSetup` End Routine, `trialLog`, MarkEvents, `eyelinkStopRecording` |
| 20 | Pixel Mode off, TASK_END, thank-you screen, `terminate_task` | routine `thanks` |

## Trigger codes (Pixel Mode B, blue channel)
| Name | RGB | MEG trigger | Event |
|---|---|---|---|
| `TRIG_FIXATION` | (0, 0, 1) | 1 | fixation cross appears |
| `TRIG_TONE_L` | (0, 0, 2) | 2 | tone starts, left ear |
| `TRIG_TONE_R` | (0, 0, 4) | 4 | tone starts, right ear |
| `TRIG_OFF` | (0, 0, 0) | – | black, all lines off |

## Display latency (projector)
- **Tone (triggers 2/4, `TONE_ONSET_*`, `resp.rt`): no correction.** The DATAPixx3 starts
  the tone at the same vsync at which it sends the trigger, and sound does not pass through
  the projector. The only delay is acoustic.
- **Fixation cross (trigger 1, `fixation_ONSET`, `fixation_onset_s`, `fixation.vp`):** the
  cross becomes visible about 8.33 ms after these times.

## EDF messages
| Message | Sent in |
|---|---|
| `SESSION_CONFIG remote_mode sample_rate_500` | 15 (`elConfig`), not in dummy mode |
| `TASK_START` / `TASK_END` | 16 / 20 |
| `TRIALID n` … `TRIAL_RESULT 0` | 19a / 19d |
| `!V TRIAL_VAR` toneSide, corrAns, foreperiod | 19b |
| `<ms> fixation_ONSET`, `fixation_OFFSET`, `!V IAREA FILE`, `!V DRAW_LIST` | `mark_onset`, `dv_end_trial` |
| `TONE_ONSET_LEFT` / `TONE_ONSET_RIGHT` | 19c (on the tone's refresh) |
| `TRIAL_SUMMARY …`, `!V TRIAL_VAR timeout` | 19d |
| `<ms> Keyboard_EVENT`, `!V TRIAL_VAR Keyboard.*` | `mark_response` |

## Data
The **PsychoPy CSV** includes `fixation.trigger`, `tone.trigger`, `fixation.vp`, `tone.vp`,
`tone.started`, `foreperiod`, `timeout`, `dummy_vpixx`, plus `resp.keys/corr/rt` and the
condition columns.

The **trial log** (`…_trials_log.tsv`, one row per trial, flushed after each trial) has
these columns: `participant`, `session`, `date`, `edf_file`, `trial`, `eyelink_trialid`,
`tone_side`, `corr_ans`, `foreperiod_s`, `fixation_onset_s`, `tone_onset_s`, `fixation_vp`,
`tone_vp`, `resp_key`, `rt_s`, `correct`, `timeout`, `dummy_vpixx`.

Everything goes into `results/<EDFname>_<date>/`, together with the EDF and the Data Viewer
`aoi/` and `graphics/` folders.

## Dummy modes (independent)
- **EyeLink:** set `DUMMY_MODE = True` in section 1, or accept the "continue in Dummy Mode?"
  question when no tracker answers.
- **VPixx:** tick `dummy_vpixx`. You get no MEG triggers and empty `.vp` columns. The tone
  plays through PsychoPy in the correct ear, but **not** precisely timed. If `pypixxlib` is
  missing, VPixx dummy mode turns on by itself and a warning is printed.
