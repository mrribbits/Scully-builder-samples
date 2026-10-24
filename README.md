# Scully PsychoPy samples

These are small PsychoPy (2026.2.3) experiments for the OPM-MEG lab at the Scully Center,
Princeton Neuroscience Institute. Every sample runs the same two-choice reaction time task.
Each one adds one piece of the lab's hardware, and the Combined sample uses all of them.

Each experiment comes in two versions:

- **`builder_samples/`**: the experiment as a Builder `.psyexp` file, with code components
  where Builder has no ready-made component.
- **`coder_samples/`**: the same experiment as one plain Python script for PsychoPy's Coder
  window. The script writes out by hand what Builder's components do. Comments mark which
  Builder piece each part replaces, so you can read the two versions side by side.

Both versions use the same timing, trigger codes, EDF messages and data columns.

| Experiment | Stimulus | EyeLink | Pixel Mode triggers | VPixx audio |
|---|---|---|---|---|
| `ChoiceRT_EyeLink` | left/right dot | ✓ | | |
| `ChoiceRT_VPixxPixelMode` | left/right dot | | ✓ | |
| `ChoiceRT_VPixxAudio` | left/right-ear tone | | | ✓ |
| `ChoiceRT_Combined` | left/right-ear tone | ✓ | ✓ | ✓ |

```
builder_samples/<experiment>/   <experiment>.psyexp, conditions.csv, (images/), README.md
coder_samples/<experiment>/     <experiment>.py,     conditions.csv, (images/), README.md
```
Each folder has its own README covering the flow, trigger codes, EDF messages, data columns
and dummy modes. The Coder READMEs also include a table mapping each script section to its
Builder equivalent.

## Lab setup these assume
- **Display:** 1920×1080 px, 120 Hz, 60.6 cm wide, 95 cm viewing distance.
- **Responses:** left index finger = `7`, right index finger = `2`.
- **EyeLink:** 1000 Plus in Remote mode, 500 Hz, HV13 calibration. Both versions use the
  `psychopy-eyelink` plugin: Builder uses its components, and Coder uses the `pylink` and
  `EyeLinkCoreGraphicsPsychoPy` it installs.
- **VPixx:** DATAPixx3 with Pixel Mode B (blue channel of the top-left pixel, 8 trigger
  lines) and its audio scheduler, through `pypixxlib`. VPixx has no Builder components, so
  the Builder versions use code components.

## Use
- **Builder:** open the `.psyexp` from inside PsychoPy (File → Open), with the other files
  in its folder next to it.
- **Coder:** open the `.py` in the Coder window (File → Open) and press Run. The settings
  you are most likely to change are in section 1 at the top of each script.
- **Testing without hardware:** use the dummy modes.
  - VPixx: the `dummy_vpixx` checkbox in the start dialog.
  - EyeLink, Builder: the Dummy Mode checkbox on the Initialize component.
  - EyeLink, Coder: `DUMMY_MODE = True` in section 1.
- **Real recordings:** use Run, not Pilot.
