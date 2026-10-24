# ChoiceRT_VPixxAudio — two-choice auditory RT with the DATAPixx3 audio scheduler

Same two-choice reaction time task as `ChoiceRT_EyeLink` and `ChoiceRT_VPixxPixelMode`, but the
stimulus is a tone in the left or right ear instead of a target on the left or right.
This example shows how to play precisely timed sounds through the DATAPixx3's audio
scheduler, started on a screen refresh. No eye tracking, no Pixel Mode, no MEG triggers.
Built for PsychoPy 2026.2.3, MEG lab display (1920×1080, 120 Hz, 60.6 cm wide, 95 cm viewing
distance → 52.5 px/deg).

## Flow
```
instruct              instructions; press 7 or 2 to start
trials loop (2 sides x 20 reps = 40, random)
  trial               fixation cross for the whole trial
                      -> wait 0.5 s + foreperiod U(0.8, 1.5) s -> tone (left or right ear)
                      -> response 7/2, or 1.5 s from tone onset
thanks                3 s
```
Responses: left index = `7`, right index = `2` (`conditions.csv` → `corrAns`).
To change the number of trials, set **nReps** in the `trials` loop (total = 2 × nReps).

## Sound
- 1000 Hz sine, 100 ms, 10 ms fade-in and fade-out, 48 kHz, 16-bit.
- Copied once into DATAPixx3 memory at the start, then replayed every trial.
- The ear comes from the `toneSide` column of `conditions.csv` (`left` / `right`), which
  is passed straight to the audio schedule. The other ear gets nothing.
- DATAPixx3 output volume 0.5 in both ears. The device opens at volume 0, which plays
  silently with no error, so keep the volume lines in `vpixxAudioSetup`.

To change the tone, edit the numbers at the top of the **Before Experiment** tab of
`vpixxAudioSetup`. To change the timing, edit the **Before Experiment** tab of `trialSetup`.
To change the screen, viewing distance or cross size, edit the **Before Experiment** tab of
`stimSettings` (sizes are in degrees and converted to pixels).

## How the tone is locked to the screen
1. **Start of each trial** (`trialSetup`): the DATAPixx3 gets that trial's audio schedule
   (which ear), but it isn't started.
2. **The frame the tone is due** (`toneStart`): the "start" command is sent with
   `DPxWriteRegCacheAfterVideoSync`, so the DATAPixx3 holds it until the next screen refresh.
3. **That refresh**: the tone starts. `resp` starts listening on the same refresh, so
   `resp.rt` is the time from tone onset.

Between steps 2 and 3, nothing may call `DPxUpdateRegCache`; it would erase the pending start.

The only remaining delay is acoustic (OPM headphone tubing or loudspeaker to ear). Measure it
once with a microphone and subtract it in analysis.

## Code components
Every code component starts with a comment block that says when it runs, what it does and
where each name comes from, and each line is explained.

| Component (routine) | Tab(s) | Job |
|---|---|---|
| `vpixxAudioSetup` (instruct) | Before Experiment | tone settings; make the tone; load pypixxlib |
| | Begin Experiment | dummy mode or not; connect, set volume, copy the tone to the DATAPixx3; close it at exit; dummy-mode PsychoPy sounds |
| `stimSettings` (trial) | Before Experiment | screen + cross size, degrees → pixels |
| `trialSetup` (trial) | Before Experiment | trial timing |
| | Begin Routine | random foreperiod; tone time; this trial's audio schedule |
| | End Routine | `timeout` column |
| `toneStart` (trial) | Each Frame | start the tone on the right frame; save `tone.started` and `tone.vp` |

**Order inside the trial routine.** Builder runs components from top to bottom:
1. `stimSettings` and `trialSetup` sit above `fixation` and `resp`, because the cross's size
   and duration and `resp`'s start time use values they set.
2. `toneStart` sits at the bottom. Its position doesn't change the timing (all Each Frame
   code runs before the frame is shown), and it uses the same start test as `resp`, so the
   tone and the reaction-time clock start on the same frame.

**No End Experiment code, on purpose.** Builder skips the End Experiment tab when you press
Esc. The DATAPixx3 is closed through Python's `atexit` instead, which runs on a normal
finish and after Esc.

## Data columns added
| Column | Meaning |
|---|---|
| `tone.started` | PsychoPy clock time of the screen refresh at which the tone started |
| `tone.vp` | DATAPixx3 clock time at that refresh (empty in dummy mode) |
| `foreperiod` | this trial's random part of the wait (s) |
| `timeout` | 1 = no answer within 1.5 s, 0 = answered |
| `dummy_vpixx` | True if run without the DATAPixx3 (first row) |

Plus `toneSide` and `corrAns` from `conditions.csv`, and Builder's `resp.keys`, `resp.rt`
and `resp.corr`.

## Dummy mode
Tick `dummy_vpixx` in the start dialog to run without the DATAPixx3. The tone then plays
through PsychoPy in the correct ear, but its timing is **not** precise, and `tone.vp` is
empty. If `pypixxlib` isn't installed, dummy mode turns on by itself and a warning is printed
— check the console before a real recording.

## Notes
- If the response pad sends keypad codes, change the allowed keys to `num_7`/`num_2` in
  `ready`, `resp` and in `conditions.csv`.
- Use **Run**, not Pilot, for real sessions, so the window is full screen at 120 Hz.
