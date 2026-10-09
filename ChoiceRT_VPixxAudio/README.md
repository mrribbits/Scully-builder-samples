# ChoiceRT_VPixxAudio — two-choice auditory RT with the DATAPixx3 audio scheduler

PsychoPy 2026.2.3 Builder. Same task structure as `ChoiceRT_VPixxPixelMode` and `ChoiceRT_EyeLink`,
but the stimulus is a tone in the left or right ear instead of a left/right target.
No eye tracking, no Pixel Mode, no MEG triggers.

## Flow
```
instruct              instructions; press 7 or 2 to start
trials loop (2 sides x 20 reps = 40, random)
  trial               fixation cross for the whole trial
                      -> 0.5 s + foreperiod U(0.8, 1.5) s -> tone (left or right ear)
                      -> response 7/2, or 1.5 s deadline from tone onset
thanks                3 s
```
Responses: left index = `7`, right index = `2` (`conditions.csv` → `corrAns`).
To change the trial count, set **nReps** in the `trials` loop (total = 2 × nReps).

## Sound
- 1000 Hz sine, 100 ms, 10 ms cosine on/off ramps, 48 kHz int16, amplitude 0.8.
- Written once to DATAPixx3 RAM (address 16,000,000) at startup; replayed each trial.
- Ear is chosen by the audio schedule's `lrMode` (`'left'` / `'right'`, from the
  `toneSide` column of `conditions.csv`); the other ear gets nothing.
- Codec volume 0.5 for both ears (`VPIXX_AUDIO_VOLUME`). The codec opens at 0, which
  plays silently with no error, so don't remove that line.
- All tone and timing constants are at the top of the *Before Experiment* tabs of
  `vpixxAudio` (tone) and `trialCode` (timing).

## How the onset is locked to the screen
Same method as the oddball script:
1. *Begin Routine*: `prep_tone(toneSide)` loads the schedule (`DPxSetAudioSchedule`) and
   pushes it to the device. Playback is not started.
2. *Each Frame*: on the first frame at or after the tone time — the same test Builder
   uses to start `resp` — `arm_tone()` calls `DPxStartAudSched` and
   `DPxWriteRegCacheAfterVideoSync`.
3. That frame's flip: at its vsync the DATAPixx3 receives the start bit and plays the tone.
   So tone onset and the start of `resp`'s RT clock are the same flip.

Between steps 2 and 3 nothing may call `DPxUpdateRegCache` (it would overwrite the pending
start bit). Only `_stamp_tone`, which runs after the flip, calls it.

Remaining latency is acoustic (OPM headphone tubing or loudspeaker-to-ear); measure it
once with a microphone and subtract in analysis.

## Where the code is
- **`vpixxAudio`** (instruct routine)
  - *Before Experiment*: tone parameters, `pypixxlib` import, tone generation.
  - *Begin Experiment*: opens the DATAPixx3, initialises the codec, sets volume, loads
    the tone; defines `prep_tone`, `arm_tone`, `close_vpixx` (they need `win`, `thisExp`
    and `dp`, which exist only inside Builder's `run()`). Registers `close_vpixx` with
    atexit so the device is released after Esc.
  - *End Experiment*: stops schedules and closes the device.
- **`trialCode`** (trial routine): timing constants, foreperiod, `prep_tone`, arming on the
  tone frame, and ending the routine at the deadline.

## Data columns added
`tone.started` (PsychoPy global time of the tone flip), `tone.vp` (DATAPixx3 clock at that
flip), `foreperiod`, `timeout`, `dummy_vpixx`, plus `toneSide`/`corrAns` and Builder's
`resp.keys/rt/corr`. `resp.rt` is measured from tone onset.

## Dummy mode
Tick `dummy_vpixx` in the start dialog to run without the DATAPixx3. The tone then plays
through PsychoPy sound (correct ear, but **not** vsync-locked) and `tone.vp` is empty.
If `pypixxlib` isn't installed it switches to dummy mode automatically and logs a
warning — check the console before a real recording.

## Notes
- If the response pad sends keypad codes, change allowed keys to `num_7`/`num_2` in
  `ready`, `resp` and in `conditions.csv`.
- Use **Run**, not Pilot, for real sessions so the window is full screen at 120 Hz.
