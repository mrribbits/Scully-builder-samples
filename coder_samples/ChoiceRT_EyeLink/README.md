# ChoiceRT_EyeLink (Coder): two-choice visual RT with an EyeLink 1000 Plus

This is the Coder (plain Python) version of `builder_samples/ChoiceRT_EyeLink`. The task and
timing are the same, and so are the eye-tracker set-up, the EDF messages, the Data Viewer
files and the trial log. Data Viewer and analysis scripts can therefore treat files from
either version the same way. In Builder, the EyeLink plugin components write all the
eye-tracker code for you. Here the same steps are written out with `pylink`, section by
section.

Built for PsychoPy 2026.2.3 with the **psychopy-eyelink** plugin (v2.2.1.1), which installs
`pylink` and `EyeLinkCoreGraphicsPsychoPy`. The tracker is an EyeLink 1000 Plus in Remote
mode at 500 Hz, with HV13 calibration.

## Running it
1. Install the psychopy-eyelink plugin (Tools → Plugins/Packages Manager) and restart
   PsychoPy.
2. Keep `conditions.csv` and `images/fixTarget.bmp` next to `ChoiceRT_EyeLink.py`.
3. Open the script in the **Coder** window and click **Run**. The start dialog asks for
   participant, session and the EDF name (at most 8 letters, digits or `_`). On a Mac it also
   asks whether the screen is a Retina display. In Builder the EDF name gets a dialog of
   its own.
4. **Dummy mode:** set `DUMMY_MODE = True` in section 1. This is the Coder equivalent of the
   Dummy Mode checkbox on Builder's Initialize component. If no tracker answers at
   100.1.1.1, the script asks whether to continue in dummy mode, just as the plugin does.
5. **Quitting:** Esc belongs to the calibration screens, so it does not quit. Press
   **Ctrl-C** during a trial. The EDF is still retrieved and the data are saved.

## Flow
```
experimenter screen   SPACE -> screen coords, calibration settings -> Camera Setup (HV13)
instructions          7, 2 or SPACE; sends TASK_START
drift check           one, before the trials (Esc -> Camera Setup, O to return)
trials (2 sides x 20 reps = 40, random)
  Host PC drawing (fixation box + both target boxes), status message
  TRIALID n, start recording, EYE_USED
  fixation at 0.2 s -> foreperiod U(0.8, 1.5) s -> target (1.5 s deadline) / response
  TRIAL_SUMMARY, interest areas, stop recording, TRIAL_RESULT 0
thanks                TASK_END; 3 s; EDF copied from the Host PC
```

## Script layout
| Section | What it does | Builder equivalent |
|---|---|---|
| 1 | settings (display, stimuli, timing, tracker) | `stimSettings`; Initialize/CameraSetup parameters |
| 2 | degrees → pixels | `stimSettings` |
| 3 | start dialog, including the EDF name | Experiment info + the plugin's EDF dialog |
| 4 | session folder `results/<EDF>_<date>/` with `aoi/` and `graphics/` | Initialize |
| 5 | connect to the tracker (or dummy) | Initialize |
| 6–7 | data files, window | Experiment Settings |
| 8 | open the EDF, data filters, button function | Initialize |
| 9 | PsychoPy ↔ EyeLink coordinates and colours | plugin helper functions |
| 10 | `abort_trial`, `terminate_task`; Data Viewer marking (`mark_onset`, `dv_end_trial`, `mark_response`) | plugin helpers; MarkEvents |
| 11 | stimuli, keyboard, trial log, Ctrl-C check | the stimulus components; `trialLog` Begin Experiment |
| 12 | clocks | `globalClock`, `routineTimer` |
| 13 | `elConfig` (500 Hz, SESSION_CONFIG); SPACE screen; `screen_pixel_coords`; calibration settings; `doTrackerSetup` | routine `eyelinkSetup` |
| 14 | instructions; TASK_START | routine `instruct` (+ `taskStartMsg`) |
| 15 | drift check | routine `eyelinkDriftCheck` |
| 16a | Host PC drawing, TRIALID, start recording | `eyelinkStartRecording` |
| 16b–c | foreperiod, trial variables, frame loop, TARGET_ONSET message | routine `trial` (`trialSetup`, `targetOnsetMsg`, MarkEvents) |
| 16d | scoring, TRIAL_SUMMARY, trial log row, offsets and interest areas, stop recording | `trialSetup` End Routine, `trialLog`, MarkEvents, `eyelinkStopRecording` |
| 17 | TASK_END, thank-you screen, `terminate_task` | routine `thanks` (+ `taskEndMsg`) |

### Messages timed to the flip
`win.callOnFlip(f, x)` runs `f(x)` right after the next `win.flip()`. The script uses it to
send `TARGET_ONSET_LEFT/RIGHT` and to run `mark_onset`, which writes the
`<ms> fixation_ONSET` / `<ms> target_ONSET` messages. These messages are therefore sent at
the moment the stimulus first appears on the screen. The `<ms>` number tells Data Viewer how
many milliseconds before the message the flip happened.

## EDF messages (identical to the Builder version)
| Message | Sent in |
|---|---|
| `SESSION_CONFIG remote_mode sample_rate_500` | section 13 (`elConfig`), not in dummy mode |
| `DISPLAY_COORDS 0 0 1919 1079` | section 13 |
| `TASK_START` / `TASK_END` | sections 14 / 17 |
| `TRIALID n` … `TRIAL_RESULT 0`, `EYE_USED` | 16a / 16d |
| `!V TRIAL_VAR` targetSide, targetX, corrAns, foreperiod | 16b |
| `!V CLEAR`, `<ms> !V IAREA FILE aoi/…`, `<ms> !V DRAW_LIST graphics/…` | 16b / `mark_onset` |
| `<ms> fixation_ONSET`, `<ms> target_ONSET`, `!V TRIAL_VAR *_ONSET_TIME` | `mark_onset` (flip-locked) |
| `TARGET_ONSET_LEFT` / `TARGET_ONSET_RIGHT` | 16c (flip-locked) |
| `TRIAL_SUMMARY trial= side= key= rt= corr= timeout=`, `!V TRIAL_VAR timeout` | 16d |
| `fixation_OFFSET`, `target_OFFSET` | `dv_end_trial` |
| `<ms> Keyboard_EVENT`, `!V TRIAL_VAR Keyboard.rt(s) / .corr / .keys` | `mark_response` |

Each trial also writes `aoi/TRIAL_nnnn_ROUTINE_01.ias` (ellipse interest areas with a 20 px
margin) and `graphics/TRIAL_nnnn_ROUTINE_01.dlf` (red boxes for Trial View). Both use the
same format as the plugin.

## Display latency (projector)
A frame appears on the projector screen **one frame (≈8.33 ms) after** the flip. All onset
messages and times are flip times, so the stimulus is actually visible 8.33 ms after
`fixation_ONSET`, `target_ONSET`, `TARGET_ONSET_*`, `fixation_onset_s` and
`target_onset_s`. The true RT is `rt_s` − 8.33 ms.

## Output files
Everything goes in `results/<EDFname>_<YYYY_MM_DD_HH_MM>/`, the same layout Builder uses:
- `<EDFname>_<date>.EDF`, copied from the Host PC at the end
- `aoi/`, `graphics/`: Data Viewer interest areas and drawing lists
- `<participant>_ChoiceRT_EyeLink_<date>.csv / .psydat / .log`: PsychoPy's data
- `<…>_trials_log.tsv`: one row per trial, flushed after each trial, with the same columns
  as the Builder version

## One deliberate difference from the Builder version
In `builder_samples/ChoiceRT_EyeLink`, the `fixation` component has no stop time. On a trial
where the participant does not respond, the target and `resp` finish after 1.5 s, but the
routine keeps waiting for `fixation` to finish, which never happens, so the run hangs at
the fixation cross. The Coder version ends a no-response trial at the 1.5 s deadline, as
`ChoiceRT_VPixxPixelMode` and `ChoiceRT_Combined` do. To fix the Builder file, give
`fixation` a duration of `foreperiod + 1.5`.
