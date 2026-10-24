# ChoiceRT_VPixxAudio (Coder): two-choice auditory RT with the DATAPixx3 audio scheduler

This is the Coder (plain Python) version of `builder_samples/ChoiceRT_VPixxAudio`. The task,
timing, tone and data columns are the same. It shows how to play precisely timed sounds
through the DATAPixx3's audio scheduler, started on a screen refresh. There is no eye
tracking, no Pixel Mode and no MEG triggers. Built for PsychoPy 2026.2.3 and the MEG lab
display (1920×1080, 120 Hz, 60.6 cm wide, 95 cm viewing distance → 52.5 px/deg).

Keep `conditions.csv` next to `ChoiceRT_VPixxAudio.py`. You need `pypixxlib` installed in
PsychoPy's Python.

## Running it
1. Open `ChoiceRT_VPixxAudio.py` in PsychoPy's **Coder** window and click **Run**.
2. To test without the DATAPixx3, tick `dummy_vpixx` in the start dialog. The tone then
   plays through the computer's sound card in the correct ear, but **not** precisely timed.
3. Press **Esc** to stop early. The data collected so far are saved.

## Flow
```
instructions          press 7 or 2
trials (2 sides x 20 reps = 40, random)
  fixation cross for the whole trial
  -> wait 0.5 s + foreperiod U(0.8, 1.5) s -> tone (left or right ear)
  -> response 7/2, or 1.5 s from tone onset
thanks                3 s
```

## Sound
- 1000 Hz sine, 100 ms, 10 ms fade-in and fade-out, 48 kHz, 16-bit (section 2 makes it).
- It is copied into DATAPixx3 memory once, at the start (section 6), and replayed on every
  trial.
- The ear comes from `toneSide` in `conditions.csv`. The other ear gets nothing.
- The output volume is 0.5 in both ears. The device opens at volume 0, which plays silently
  with no error message, so keep the volume lines.

## How the tone is locked to the screen
1. **Start of each trial** (section 11): the DATAPixx3 is given that trial's audio schedule,
   which says which ear to play in. The schedule is not started yet.
2. **The frame the tone is due:** `DPxStartAudSched()` + `DPxWriteRegCacheAfterVideoSync()`.
   The DATAPixx3 holds the start command until the next screen refresh, which is the
   `win.flip()` that follows.
3. **That refresh:** the tone starts. The keyboard clock is reset on the same flip, so
   `resp.rt` is measured from tone onset.

Between steps 2 and 3, nothing may call `DPxUpdateRegCache`, because it would erase the
pending start. `saveToneTime` reads the DATAPixx3 clock only *after* the flip, so it is safe.

## Script layout
| Section | What it does | Builder equivalent |
|---|---|---|
| 1 | settings (display, timing, tone, keys) | `stimSettings`, `trialSetup`, `vpixxAudioSetup` Before Experiment |
| 2 | cross size in pixels; makes the tone | `stimSettings`; `vpixxAudioSetup` Before Experiment |
| 3–5 | start dialog, data files, window | Experiment Settings |
| 6 | dummy-mode decision; connect, audio on, volume, copy the tone; `atexit` cleanup; dummy-mode sounds | `vpixxAudioSetup` Begin Experiment |
| 7 | `saveToneTime` | `vpixxAudioSetup` Begin Experiment |
| 8 | stimuli, keyboard, `saveAndQuit`, Esc check | the stimulus and Keyboard components |
| 9 | clocks | `globalClock`, `routineTimer` |
| 10 | instructions | routine `instruct` |
| 11 | trials loop: schedule, then one `while` pass per frame (cross, tone, response) | loop `trials` + routine `trial` (+ `toneStart` Each Frame) |
| 12 | thank-you screen; save and quit | routine `thanks` |

## Data
Files are saved as `data/<participant>_<session>_<date>.*`. The columns match the Builder
version:

| Column | Meaning |
|---|---|
| `tone.started` | PsychoPy clock time of the refresh at which the tone started |
| `tone.vp` | DATAPixx3 clock time at that refresh (empty in dummy mode) |
| `foreperiod` | this trial's random part of the wait (s) |
| `timeout` | 1 = no answer within 1.5 s, 0 = answered |
| `dummy_vpixx` | True if the run used no DATAPixx3 |

The data also include `toneSide` and `corrAns` from `conditions.csv`, plus `resp.keys`,
`resp.rt`, `resp.corr` and the start and stop times.

The only remaining delay is acoustic: the time sound takes through the tubing or from the
loudspeaker to the ear. Measure it once with a microphone and subtract it in your analysis.
