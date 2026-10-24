#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ChoiceRT_VPixxAudio.py  -  PsychoPy CODER version
=====================================================================

Two-choice AUDITORY reaction time task, with the tone played by the
DATAPixx3's audio scheduler and started exactly on a screen refresh.
This is the Coder (pure Python) twin of the Builder experiment
builder_samples/ChoiceRT_VPixxAudio/ChoiceRT_VPixxAudio.psyexp.
Same task, same timing, same tone and the same data columns.

No eye tracking, no Pixel Mode and no MEG triggers: tone times are saved
to the data file only. (ChoiceRT_Combined adds triggers and eye tracking.)

Written for PsychoPy 2026.2.3 and the Scully Center OPM-MEG lab:
    display 1920 x 1080 px, 120 Hz, 60.6 cm wide, viewed from 95 cm
    DATAPixx3 between the stimulus PC and the projector
    response keys: 7 = left index finger, 2 = right index finger

---------------------------------------------------------------------
THE TASK
---------------------------------------------------------------------
    instructions        press 7 or 2 to start
    40 trials, random order (20 left ear, 20 right ear), each one:
        fixation cross on for the whole trial
        wait 0.5 s + a random 0.8-1.5 s (the "foreperiod")
        100 ms tone in the LEFT or RIGHT ear
        press 7 (left) or 2 (right) within 1.5 s of the tone
    thank-you screen    3 s

---------------------------------------------------------------------
HOW TO RUN IT
---------------------------------------------------------------------
    1. Open this file in PsychoPy's Coder window (File > Open).
    2. Keep conditions.csv in the same folder as this file.
    3. Click "Run" (use Pilot only for quick tests).
    4. Fill in the start dialog. Tick "dummy_vpixx" to test on a computer
       with no DATAPixx3: the tone then plays through the computer's own
       sound card, in the correct ear, but NOT precisely timed.
    Press Esc at any time to stop. The data recorded so far are saved.

---------------------------------------------------------------------
HOW THE SOUND IS PLAYED (read this first)
---------------------------------------------------------------------
The tone is not played by the stimulus PC's sound card. It is played by
the DATAPixx3, VPixx's box that sits between the PC and the display. The
DATAPixx3 has its own memory and its own audio output.
    1. At the start of the experiment we copy the tone, once, into the
       DATAPixx3's memory (section 6).
    2. Each trial we give the DATAPixx3 an "audio schedule": play that
       tone, at 48000 samples per second, into the LEFT (or RIGHT) ear
       (start of the trial, section 11).
    3. On the frame the tone should start, we tell it "start", timed to
       arrive exactly when the screen refreshes. That way we know the tone
       started at that screen refresh, to well under 1 ms.
The stimulus PC's own audio is far less precise (often 20-60 ms of
unpredictable delay), which is why we use the DATAPixx3 instead.

---------------------------------------------------------------------
BUILDER vs CODER - IF YOU KNOW ONE BUT NOT THE OTHER
---------------------------------------------------------------------
Builder writes a Python script like this one for you every time you press
Run. In Coder you write that script yourself. Everything Builder hides
inside its components is written out here, step by step:

    Builder                          This script
    -------                          -----------
    Experiment Settings              sections 1, 4 (data files), 9 (clocks)
    start dialog (Experiment info)   section 3
    the window                       section 5
    stimulus components              section 8
    Code component, Before/Begin
        Experiment tabs              sections 2, 6, 7
    a routine (instruct, trial ...)  a "while" loop that draws one frame
                                     per pass and calls win.flip()
    a loop (trials)                  a "for" loop over a TrialHandler2
    Each Frame tab                   code inside the "while" loop
    a component's Start / Stop time  an "if" that compares the time of the
                                     next screen refresh with the start or
                                     stop time

The one idea that matters most: THE SCREEN ONLY CHANGES WHEN YOU CALL
win.flip(). You draw everything for the next frame first, then flip. The
flip waits for the display's next refresh (every 8.33 ms at 120 Hz) and
shows the new frame. Anything you want to happen "exactly when the frame
appears" must be timed to that flip (see win.callOnFlip below).
"""

# =====================================================================
# 0. IMPORT THE LIBRARIES WE NEED
# =====================================================================
# "import" loads code that someone else wrote so we can use it here.
#   visual   - windows and things to draw (text, shapes, ...)
#   core     - clocks and quitting
#   data     - the data file, the trial list and the trials loop
#   gui      - the start dialog box
#   logging  - writes messages to the console and to a .log file
#   sound    - PsychoPy's own sounds (used only in dummy mode)
#   keyboard - PsychoPy's precise keyboard (it time-stamps each key press)
import psychopy
from psychopy import visual, core, data, gui, logging, sound
from psychopy.hardware import keyboard
from psychopy.constants import NOT_STARTED, STARTED, FINISHED

import math      # Python's maths library: tan(), radians(), ...
import os        # file and folder names
import atexit    # lets us name a function that must run when Python quits

# "numpy" is a maths library for working with long lists of numbers,
# such as the thousands of numbers that make up a sound. "np" is its
# short name.
import numpy as np

# pypixxlib is VPixx's Python library for talking to the DATAPixx3.
# "try / except ImportError" means: try to load it; if it is not installed
# on this computer, don't crash - remember that it is missing instead.
# Section 6 then switches to dummy mode (no DATAPixx3).
# "as dp" gives the library the short name dp, so later lines can say
# dp.DPxOpen() instead of typing the full name each time.
try:
    from pypixxlib import _libdpx as dp
    pypixxlibInstalled = True
except ImportError:
    dp = None
    pypixxlibInstalled = False


# =====================================================================
# 1. SETTINGS - EDIT HERE
# =====================================================================
# Everything you might want to change is collected in this section.

# ---- The display (MEG lab projector) --------------------------------
screenSizePix = (1920, 1080)  # width, height in pixels
screenWidthCm = 60.6          # width of the image on the screen, in cm
viewingDistanceCm = 95        # distance from the eyes to the screen, in cm
background = (-1, -1, -1)     # black. PsychoPy colours go from -1 to +1 for
                              # (red, green, blue): -1 = none, +1 = full.

# ---- Stimulus size, in degrees of visual angle ----------------------
fixationSizeDeg = 0.6         # width and height of the central cross

# ---- Trial timing, seconds ------------------------------------------
# A trial: fixation cross on -> wait ITI + foreperiod -> tone -> up to
# responseWindow seconds to answer. The cross stays on the whole time.
ITI = 0.5                     # fixed part of the wait before the tone
foreperiodMin = 0.8           # plus a random extra wait between these two
foreperiodMax = 1.5           #   values, so the tone can't be predicted
responseWindow = 1.5          # time allowed to answer, from tone onset
thanksDuration = 3.0          # how long the thank-you screen stays up
# (The wait is split into ITI + foreperiod only so the timing and the
#  "foreperiod" data column match the two visual versions of this task,
#  where the ITI was a blank screen.)

# ---- Trials ----------------------------------------------------------
conditionsFile = 'conditions.csv'  # one row per condition (left, right)
nReps = 20                         # repeats of each row: 2 x 20 = 40 trials

# ---- Response keys ---------------------------------------------------
# If the MEG response pad sends keypad codes, use 'num_7' and 'num_2'
# here AND in conditions.csv.
respKeys = ['7', '2']   # 7 = left index finger, 2 = right index finger

# ---- The tone --------------------------------------------------------
toneFreqHz = 1000          # pitch of the tone, in Hz (cycles per second)
toneDurationSec = 0.100    # how long the tone lasts: 100 ms
rampSec = 0.010            # 10 ms fade-in and fade-out (avoids clicks)
sampleRate = 48000         # numbers per second the DATAPixx3 plays
toneLoudness = 0.8         # 0 to 1: how much of the full range to use
audioVolume = 0.5          # 0 to 1: DATAPixx3 output volume, both ears

# Where in the DATAPixx3's memory the tone is stored. 16,000,000 is the
# address VPixx uses by default for audio. Leave it as it is.
toneMemoryAddress = 16000000


# =====================================================================
# 2. WORK OUT THE CROSS SIZE AND MAKE THE TONE
# =====================================================================
# Nothing to edit here: everything is worked out from section 1.

# ---- Degrees -> pixels ----------------------------------------------
# 1 degree covers 2 * distance * tan(0.5 degrees) centimetres of screen.
# math.radians() converts degrees to radians, which tan() expects.
cmPerDeg = 2 * viewingDistanceCm * math.tan(math.radians(0.5))

# How many pixels fit in 1 cm of screen.
pixPerCm = screenSizePix[0] / screenWidthCm

# How many pixels make up 1 degree (about 52.5 with the numbers above).
pixPerDeg = cmPerDeg * pixPerCm

# Final size in pixels. round() gives a whole number of pixels.
fixationSizePix = round(fixationSizeDeg * pixPerDeg)    # 32 px

# ---- Make the tone ---------------------------------------------------
# A sound is just a long list of numbers: the position of the
# loudspeaker at each moment. For a pure tone those numbers follow a
# sine wave.

# How many numbers (samples) the tone needs: 0.1 s x 48000 = 4800.
nSamples = int(round(toneDurationSec * sampleRate))

# The time of each sample in seconds: 0, 1/48000, 2/48000, ...
# np.arange(n) makes the list 0, 1, 2, ... n-1.
sampleTimes = np.arange(nSamples) / sampleRate

# The sine wave itself, with values from -1 to +1.
tone = np.sin(2 * np.pi * toneFreqHz * sampleTimes)

# Fade-in and fade-out. Without them, the sudden start and stop of the
# wave is heard as a click. "fade" rises smoothly from 0 to 1.
nRampSamples = int(round(rampSec * sampleRate))           # 480 samples
fade = 0.5 * (1 - np.cos(np.pi * np.arange(nRampSamples) / nRampSamples))
tone[:nRampSamples] = tone[:nRampSamples] * fade          # first 10 ms
tone[-nRampSamples:] = tone[-nRampSamples:] * fade[::-1]  # last 10 ms
# ([:n] means "the first n values", [-n:] means "the last n values" and
#  [::-1] means "in reverse order", so the end fades out.)

# The DATAPixx3 wants whole numbers from -32767 to +32767 (16-bit audio,
# "int16"), so scale the wave and convert it.
toneWave = (tone * toneLoudness * 32767).astype(np.int16)


# =====================================================================
# 3. THE START DIALOG
# =====================================================================
# expInfo is a "dict": a set of named values, written {name: value, ...}.
# gui.DlgFromDict() shows one field per entry and fills in what you type.
# A True/False value (dummy_vpixx) is shown as a tick box.
expName = 'ChoiceRT_VPixxAudio'
expInfo = {
    'participant': '',
    'session': '001',
    'dummy_vpixx': False,
}

# "Pilot" mode: PsychoPy's Pilot/Run switch (top of the Coder window)
# passes "--pilot" to this script. setPilotModeFromArgs() reads it and
# gives True (Pilot) or False (Run).
PILOTING = core.setPilotModeFromArgs()
if PILOTING:
    expInfo['participant'] = 'pilot'

dlg = gui.DlgFromDict(dictionary=expInfo, sortKeys=False, title=expName)
if not dlg.OK:          # the experimenter pressed Cancel
    core.quit()

# Extra information saved with every row of the data file.
expInfo['date'] = data.getDateStr()     # e.g. 2026-10-23_14h05.31.123
expInfo['expName'] = expName
expInfo['psychopyVersion'] = psychopy.__version__   # e.g. 2026.2.3


# =====================================================================
# 4. DATA FILES
# =====================================================================
# Builder saves files called data/<participant>_<session>_<date>.* in the
# experiment's folder. We do the same, so files from both versions look
# alike.

# Make sure we work in the folder that contains this script, so that
# 'conditions.csv' and 'data' are found there.
thisDir = os.path.dirname(os.path.abspath(__file__))
os.chdir(thisDir)

# File names without the ending (.csv, .log ... are added later).
fileStem = os.path.join(thisDir, 'data', '%s_%s_%s' % (
    expInfo['participant'], expInfo['session'], expInfo['date']))
os.makedirs(os.path.dirname(fileStem), exist_ok=True)  # create data/ if needed

# The ExperimentHandler collects everything we save with addData() and
# writes it to a .csv file (one row per trial) and a .psydat file at the
# end. extraInfo=expInfo copies the dialog answers into every row.
thisExp = data.ExperimentHandler(
    name=expName, extraInfo=expInfo,
    savePickle=True, saveWideText=True,
    dataFileName=fileStem, sortColumns='time')
thisExp.addData('piloting', PILOTING)

# The .log file: a time-stamped list of everything that happened
# (stimuli on and off, key presses, warnings). "info" is fairly detailed.
logging.console.setLevel(logging.WARNING)   # only warnings in the console
logFile = logging.LogFile(fileStem + '.log', level=logging.INFO)


# =====================================================================
# 5. THE WINDOW
# =====================================================================
# fullscr=True  -> covers the whole screen, so nothing else on the
#                  desktop can steal frames.
# screen=0      -> the first display. Change to 1 for a second display.
# units='pix'   -> all sizes and positions are in pixels, and (0, 0) is the
#                  CENTRE of the screen; +x is right, +y is up.
# In Pilot mode we use a small window, like Builder.
win = visual.Window(
    size=screenSizePix if not PILOTING else (800, 600),
    fullscr=not PILOTING,
    screen=0,
    color=background, colorSpace='rgb',
    units='pix',
    allowGUI=False,
    blendMode='avg', useFBO=True,
)
win.mouseVisible = False

# Measure the real refresh rate (should be about 120 Hz) and save it.
expInfo['frameRate'] = win.getActualFrameRate()


# =====================================================================
# 6. CONNECT TO THE DATAPixx3, SWITCH ITS AUDIO ON, LOAD THE TONE
# =====================================================================
# ---- Dummy mode? -----------------------------------------------------
# The "dummy_vpixx" tick box runs the experiment without a DATAPixx3,
# for testing on any computer. str(...) == 'True' works whether the
# dialog hands back True or the text 'True'.
DUMMY_VPIXX = str(expInfo['dummy_vpixx']) == 'True'

# Without pypixxlib we can't talk to a DATAPixx3, so force dummy mode.
if not pypixxlibInstalled and not DUMMY_VPIXX:
    logging.warning('pypixxlib is not installed, so dummy_vpixx was turned '
                    'on: tones play through PsychoPy and are NOT precisely timed')
    DUMMY_VPIXX = True

# Record the mode in the data file, so a dummy run can't be mistaken for
# a real one later.
thisExp.addData('dummy_vpixx', DUMMY_VPIXX)

if not DUMMY_VPIXX:
    # ---- Real DATAPixx3 ----------------------------------------------
    # How VPixx commands work: most dp.DPx... commands only change a
    # local copy of the DATAPixx3's settings (the "register cache") on
    # the stimulus PC. Nothing reaches the device until we send that
    # copy with dp.DPxWriteRegCache().
    dp.DPxOpen()                       # connect over USB
    dp.DPxStopAllScheds()              # stop anything left playing
    dp.DPxInitAudCodec()               # switch the audio output on
    # The volume starts at 0 (silent!) every time the device is opened,
    # so it must be set here, or every tone plays silently with no error.
    dp.DPxSetAudLeftVolume(audioVolume)
    dp.DPxSetAudRightVolume(audioVolume)
    dp.DPxWriteRegCache()              # send the settings above

    # Copy the tone into the DATAPixx3's memory. This is done once; each
    # trial just replays it.
    dp.DPxWriteAudioBuffer(toneWave, toneMemoryAddress)
    dp.DPxWriteRegCache()

    logging.exp('DATAPixx3 audio ready: %d samples = %.1f ms'
                % (len(toneWave), 1000 * len(toneWave) / sampleRate))
    # (%d puts a whole number into the text and %.1f a number with one
    #  decimal place, in the order listed after the %.)

    # ---- Close the connection when the experiment ends ------------------
    # "def" defines a function: a named block of code that runs later,
    # when something calls it by name.
    def closeVpixx():
        """Stop playback and disconnect from the DATAPixx3."""
        try:
            dp.DPxStopAllScheds()
            dp.DPxWriteRegCache()
            dp.DPxClose()
        except Exception:
            pass   # the device was already closed or unplugged

    # atexit.register() means: run closeVpixx when the script ends,
    # however it ends: normally, after Esc, or after an error.
    atexit.register(closeVpixx)

else:
    # ---- Dummy mode ---------------------------------------------------
    # Make two stereo PsychoPy sounds from the same tone: one with the
    # tone in the left channel and silence in the right, and one the
    # other way round. They play in the correct ear, but their timing
    # is NOT precise, so use dummy mode for testing only.
    toneFloat = toneWave / 32767.0        # PsychoPy wants -1 to +1
    silence = np.zeros(len(toneFloat))    # a list of zeros, same length
    # np.column_stack([a, b]) puts two lists side by side as two
    # columns: column 1 = left ear, column 2 = right ear.
    dummySounds = {
        'left':  sound.Sound(np.column_stack([toneFloat, silence]),
                             sampleRate=sampleRate, stereo=True),
        'right': sound.Sound(np.column_stack([silence, toneFloat]),
                             sampleRate=sampleRate, stereo=True),
    }
    # dummySounds['left'] is the left-ear sound, dummySounds['right'] the
    # right-ear one.


# =====================================================================
# 7. FUNCTIONS USED DURING THE TRIALS
# =====================================================================
def saveToneTime():
    """Save the DATAPixx3's clock time as the column 'tone.vp'.

    Not run now. The trial hands it to win.callOnFlip(), which runs it
    straight after the screen refresh at which the tone starts.
    """
    if not DUMMY_VPIXX:
        dp.DPxUpdateRegCache()   # fetch the device's current state...
        thisExp.addData('tone.vp', dp.DPxGetTime())   # ...and its clock


# =====================================================================
# 8. STIMULI, KEYBOARD AND QUITTING
# =====================================================================
# Stimuli are created ONCE here and reused on every trial. Creating them
# inside the trial loop would be slow and could make frames late.
taskInstructions = visual.TextStim(
    win, name='taskInstructions',
    text=('On each trial you will hear a short tone in your LEFT or RIGHT ear.\n\n'
          'Tone in the LEFT ear: press with your LEFT index finger.\n'
          'Tone in the RIGHT ear: press with your RIGHT index finger.\n\n'
          'Respond as quickly and accurately as you can, and keep your eyes '
          'on the cross.\n\n'
          'Press either button to start.'),
    font='Arial', height=32, wrapWidth=1400, color='white', units='pix')

thanksText = visual.TextStim(
    win, name='thanksText',
    text='Thank you!\n\nThe task is complete.',
    font='Arial', height=32, wrapWidth=1400, color='white', units='pix')

# The fixation cross. ShapeStim with vertices='cross' is what Builder's
# Polygon component makes when you choose the "cross" shape.
fixation = visual.ShapeStim(
    win, name='fixation', vertices='cross', units='pix',
    size=(fixationSizePix, fixationSizePix), pos=(0, 0),
    lineWidth=1.0, lineColor='white', fillColor='white', interpolate=True)

# PsychoPy's precise keyboard. Each key press it reports comes with a
# reaction time measured on kb.clock, which we reset at tone onset.
kb = keyboard.Keyboard()


def saveAndQuit():
    """Save the data files, close the window and stop the script."""
    thisExp.saveAsWideText(fileStem + '.csv', delim='auto')
    thisExp.saveAsPickle(fileStem)
    thisExp.abort()        # tells PsychoPy the files are saved (no second copy)
    logging.flush()
    win.close()
    core.quit()            # closeVpixx() runs now, through atexit


def checkForEscape():
    """Quit (saving the data) if the experimenter pressed Esc."""
    # waitRelease=False: report the key as soon as it goes down.
    # clear=False: leave other keys (7, 2) for the response code to read.
    if kb.getKeys(keyList=['escape'], waitRelease=False, clear=False):
        logging.warning('Esc pressed: stopping the experiment')
        saveAndQuit()


# =====================================================================
# 9. CLOCKS
# =====================================================================
# globalClock starts at 0 now, just before the first screen, and runs
# for the rest of the experiment (Builder starts it at the same point).
# All ".started" / ".stopped" times in the data file are on this clock.
# setDefaultClock() makes the log file and win.getFutureFlipTime() use it
# too, exactly as Builder does.
globalClock = core.Clock()
logging.setDefaultClock(globalClock)

# trialClock is reset to 0 at the start of every trial (Builder calls it
# "routineTimer"). Start and stop times within a trial are measured on it.
trialClock = core.Clock()

# Builder's "frameTolerance": a tiny margin (1 ms), so that a frame due at
# exactly the start time is not missed because of rounding.
frameTolerance = 0.001


# =====================================================================
# 10. INSTRUCTIONS SCREEN (Builder routine "instruct")
# =====================================================================
# This is the simplest kind of "routine": draw, flip, repeat, until a key
# is pressed. One pass of the "while" loop = one frame.
kb.clearEvents()                   # forget keys pressed before this screen
taskInstructions.setAutoDraw(True)  # draw it on every flip from now on
thisExp.timestampOnFlip(win, 'instruct.started')
while True:
    checkForEscape()
    keys = kb.getKeys(keyList=respKeys, waitRelease=False)
    if keys:                       # a list with something in it counts as True
        thisExp.addData('ready.keys', keys[-1].name)
        thisExp.addData('ready.rt', keys[-1].rt)
        break                      # leave the "while" loop
    win.flip()
taskInstructions.setAutoDraw(False)
thisExp.addData('instruct.stopped', globalClock.getTime())
thisExp.nextEntry()                # finish this row of the data file


# =====================================================================
# 11. THE TRIALS LOOP (Builder loop "trials" + routine "trial")
# =====================================================================
# data.importConditions() reads conditions.csv into a list with one entry
# per row: [{'toneSide': 'left', 'corrAns': '7'}, ...]
# TrialHandler2 repeats that list nReps times in random order.
# thisExp.addLoop() makes the condition columns appear in the data file.
trials = data.TrialHandler2(
    trialList=data.importConditions(conditionsFile),
    nReps=nReps, method='random', extraInfo=expInfo, name='trials')
thisExp.addLoop(trials)

# "for thisTrial in trials" runs the indented block once per trial.
# thisTrial holds this trial's row of conditions.csv.
for thisTrial in trials:
    toneSide = thisTrial['toneSide']       # 'left' or 'right'
    corrAns = str(thisTrial['corrAns'])    # '7' or '2'

    # ---- Prepare the trial (Builder's "Begin Routine") ---------------
    # A random number between foreperiodMin and foreperiodMax.
    foreperiod = np.random.uniform(foreperiodMin, foreperiodMax)
    thisExp.addData('foreperiod', foreperiod)

    # When the tone starts, in seconds from the start of the trial. The
    # response window opens at this time too, so the reaction time is
    # measured from the tone.
    toneOnset = ITI + foreperiod

    if not DUMMY_VPIXX:
        # The audio schedule: start at once when told (0.0), play at
        # sampleRate, play all the tone's samples, send them to toneSide
        # ('left' or 'right' ear only) and read them from
        # toneMemoryAddress.
        dp.DPxSetAudioSchedule(0.0, sampleRate, len(toneWave), toneSide,
                               toneMemoryAddress)
        dp.DPxWriteRegCache()   # send it to the DATAPixx3 (not started yet)

    # Every stimulus starts the trial "not started". We use .status the
    # same way Builder does: NOT_STARTED -> STARTED -> FINISHED.
    fixation.status = NOT_STARTED
    toneStarted = False      # set to True once the tone has been started
    respStatus = NOT_STARTED
    respKey = None           # the key pressed, once there is one
    respRT = None            # its reaction time (s from tone onset)
    respDuration = None      # how long the key was held (if known)

    kb.clearEvents()

    # Start the trial clock at the moment of the next flip, and note the
    # trial's start time in the data file.
    thisExp.timestampOnFlip(win, 'trial.started')
    win.callOnFlip(trialClock.reset)
    win.flip()

    # ---- Run the trial: one pass of this loop per frame -------------
    # On every pass we:
    #   1. ask when the NEXT flip will happen (tThisFlip)
    #   2. switch the cross on if its time has come
    #   3. start the tone (and the response window) if its time has come
    #   4. read the keyboard
    #   5. flip
    while True:
        # Time of the coming flip on the trial clock and on the global
        # clock. Comparing THIS time (not "now") with the start times
        # means each event happens on the first frame that is due.
        tThisFlip = win.getFutureFlipTime(clock=trialClock)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)

        # ---- fixation cross: on at the start of the trial ------------
        if fixation.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
            fixation.setAutoDraw(True)       # draw it on every flip from now on
            fixation.status = STARTED
            # tStartRefresh = when the cross appears, on the global clock.
            # tThisFlipGlobal is our best guess now; timestampOnFlip and
            # timeOnFlip replace it with the ACTUAL flip time once the
            # flip has happened.
            fixation.tStartRefresh = tThisFlipGlobal
            thisExp.timestampOnFlip(win, 'fixation.started')
            win.timeOnFlip(fixation, 'tStartRefresh')

        # ---- the tone: start it on the frame it is due ---------------
        # The same test opens the response window, so the tone and the
        # reaction-time clock start on the same frame.
        respJustStarted = False
        if not toneStarted and tThisFlip >= toneOnset - frameTolerance:

            if not DUMMY_VPIXX:
                # Mark the schedule "start" in the local copy of the
                # settings...
                dp.DPxStartAudSched()
                # ...and send it to the DATAPixx3, which holds it until
                # the next screen refresh, the one we are about to show
                # with win.flip(). The tone starts exactly then.
                dp.DPxWriteRegCacheAfterVideoSync()
                # IMPORTANT: between these two lines and the screen
                # refresh, nothing may call dp.DPxUpdateRegCache(). It
                # would replace the local copy with the device's state and
                # erase the "start". (saveToneTime calls it, but only
                # AFTER the refresh, so it is safe.)
            else:
                # Dummy mode: play the PsychoPy sound when the frame is
                # shown. win.callOnFlip(f) means "run f straight after the
                # next frame appears". Note "play" without (): we hand
                # over the function so it can be run later, instead of
                # running it now.
                dummySounds[toneSide].stop()          # in case it's still playing
                win.callOnFlip(dummySounds[toneSide].play)

            # After the frame appears, save the DATAPixx3's clock (tone.vp).
            win.callOnFlip(saveToneTime)

            # Save the tone's start time on PsychoPy's clock (tone.started).
            thisExp.addData('tone.started', tThisFlipGlobal)
            toneStarted = True   # don't start it again this trial

            # The response window opens on the same flip. At that flip
            # the keyboard clock is reset to 0 (so RTs are measured from
            # tone onset) and any earlier key presses are thrown away.
            respStatus = STARTED
            # respTiming['start'] = when the window opened, on the global
            # clock: our best guess now, replaced by the actual flip time
            # once the flip has happened (timeOnFlip works on a dict too).
            respTiming = {'start': tThisFlipGlobal}
            win.timeOnFlip(respTiming, 'start')
            thisExp.timestampOnFlip(win, 'resp.started')
            win.callOnFlip(kb.clock.reset)
            win.callOnFlip(kb.clearEvents, eventType='keyboard')
            respJustStarted = True    # don't read keys until after that flip

        # ---- the response --------------------------------------------
        if respStatus == STARTED and not respJustStarted:
            keys = kb.getKeys(keyList=respKeys, waitRelease=False)
            if keys:
                respKey = keys[0].name         # the first key pressed
                respRT = keys[0].rt            # seconds since tone onset
                respDuration = keys[0].duration
                break                          # a response ends the trial

        # ---- the deadline --------------------------------------------
        # If no key was pressed, the trial (cross and response window)
        # ends responseWindow seconds after the tone.
        if respStatus == STARTED and tThisFlipGlobal > respTiming['start'] + responseWindow - frameTolerance:
            thisExp.addData('fixation.stopped', tThisFlipGlobal)
            thisExp.addData('resp.stopped', tThisFlipGlobal)
            break

        checkForEscape()
        win.flip()

    # ---- End of the trial (Builder's "End Routine") -----------------
    fixation.setAutoDraw(False)
    fixation.status = FINISHED
    thisExp.addData('trial.stopped', globalClock.getTime())

    # Save the response the way Builder's Keyboard component does:
    # resp.keys, resp.corr (1 = correct, 0 = wrong or none), resp.rt.
    thisExp.addData('resp.keys', respKey)
    if respKey is not None:
        thisExp.addData('resp.corr', int(respKey == corrAns))
        thisExp.addData('resp.rt', respRT)
        thisExp.addData('resp.duration', respDuration)
        thisExp.addData('timeout', 0)
    else:
        thisExp.addData('resp.corr', 0)
        thisExp.addData('timeout', 1)     # no answer in time

    # Finish this trial's row of the data file and start a new one.
    thisExp.nextEntry()


# =====================================================================
# 12. THANK-YOU SCREEN (Builder routine "thanks")
# =====================================================================
thanksText.setAutoDraw(True)
thisExp.timestampOnFlip(win, 'thanksText.started')
win.callOnFlip(trialClock.reset)
win.flip()
while trialClock.getTime() < thanksDuration:
    checkForEscape()
    win.flip()
thanksText.setAutoDraw(False)
win.flip()

# Save everything and quit. closeVpixx() runs automatically (atexit).
saveAndQuit()
