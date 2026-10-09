# Scully Builder samples

Small PsychoPy Builder (2026.2.3) experiments for the OPM-MEG lab at the Scully Center,
Princeton Neuroscience Institute. Each one is the same two-choice reaction time task. They
show, one piece at a time, how to add the lab's hardware to a Builder experiment.

| Folder | Stimulus | EyeLink | Pixel Mode triggers | VPixx audio |
|---|---|---|---|---|
| `ChoiceRT_EyeLink` | left/right dot | ✓ (psychopy-eyelink plugin) | | |
| `ChoiceRT_VPixxPixelMode` | left/right dot | | ✓ | |
| `ChoiceRT_VPixxAudio` | left/right-ear tone | | | ✓ |
| `ChoiceRT_Combined` | left/right-ear tone | ✓ | ✓ | ✓ |

Each folder has its own README with the flow, trigger codes, data columns and dummy modes.

## Lab setup these assume
- **Display:** 1920×1080 px, 120 Hz, 60.6 cm wide, 95 cm viewing distance.
- **Responses:** left index finger = `7`, right index finger = `2`.
- **EyeLink:** 1000 Plus in Remote mode, 500 Hz, HV13 calibration; uses the `psychopy-eyelink` plugin.
- **VPixx:** DATAPixx3 with Pixel Mode B (blue channel of the top-left pixel, 8 trigger
  lines) and its audio scheduler; uses `pypixxlib` from Code Components, because VPixx has
  no Builder components.

## Use
- **Opening:** open the `.psyexp` from inside PsychoPy (File → Open), with the files in
  its folder next to it.
- **Testing without hardware:** use the dummy modes. They are the `dummy_vpixx` box in the
  start dialog and the Dummy Mode checkbox on the EyeLink Initialize component.
- **Real recordings:** use Run, not Pilot.
