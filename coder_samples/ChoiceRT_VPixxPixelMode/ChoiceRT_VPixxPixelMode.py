#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ChoiceRT_VPixxPixelMode.py  -  PsychoPy CODER version
=====================================================================

Two-choice visual reaction time task with VPixx Pixel Mode B MEG triggers.
This is the Coder (pure Python) twin of the Builder experiment
builder_samples/ChoiceRT_VPixxPixelMode/ChoiceRT_VPixxPixelMode.psyexp.
Same task, same timing, same trigger codes and the same data columns.

Written for PsychoPy 2026.2.3 and the Scully Center OPM-MEG lab:
    display 1920 x 1080 px, 120 Hz, 60.6 cm wide, viewed from 95 cm
    DATAPixx3 between the stimulus PC and the projector
    response keys: 7 = left index finger, 2 = right index finger

---------------------------------------------------------------------
THE TASK
---------------------------------------------------------------------
    instructions        press 7 or 2 to start
    40 trials, random order (20 left, 20 right), each one:
        blank screen 0.5 s
        fixation cross appears                       -> MEG trigger 1
        random wait 0.8-1.5 s (the "foreperiod")
        white dot appears LEFT or RIGHT              -> MEG trigger 2 (left)
                                                        or 4 (right)
        press 7 (left) or 2 (right) within 1.5 s
    thank-you screen    3 s

---------------------------------------------------------------------
HOW TO RUN IT
---------------------------------------------------------------------
    1. Open this file in PsychoPy's Coder window (File > Open).
    2. Keep conditions.csv in the same folder as this file.
    3. Click "Run" (NOT "Pilot": pilot mode uses a small window, and Pixel
       Mode triggers need a full-screen window - see section 6).
    4. Fill in the start dialog. Tick "dummy_vpixx" to test on a computer
       with no DATAPixx3 (nothing is sent to the MEG).
    Press Esc at any time to stop. The data recorded so far are saved.

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
shows the new frame. Anything you want to happen "exactly when the
stimulus appears" must be timed to that flip (see win.callOnFlip below).
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
#   keyboard - PsychoPy's precise keyboard (it time-stamps each key press)
import psychopy
from psychopy import visual, core, data, gui, logging
from psychopy.hardware import keyboard
from psychopy.constants import NOT_STARTED, STARTED, FINISHED

import math      # Python's maths library: tan(), radians(), ...
import os        # file and folder names
import atexit    # lets us name a function that must run when Python quits

import numpy as np   # numbers and random numbers ("np" is its short name)

# pypixxlib is VPixx's Python library for talking to the DATAPixx3.
# "try / except ImportError" means: try to load it; if it is not installed
# on this computer, don't crash - remember that it is missing instead.
# Section 6 then switches to dummy mode (no hardware, no triggers).
# "as dp" gives the library the short name dp, so later lines can say
# dp.DPxOpen() instead of typing the full name each time.
try:
    from pypixxlib import _libdpx as dp
    PYPIXXLIB_INSTALLED = True
except ImportError:
    dp = None
    PYPIXXLIB_INSTALLED = False


# =====================================================================
# 1. SETTINGS - EDIT HERE
# =====================================================================
# Everything you might want to change is collected in this section.
# Names written in CAPITALS are "constants": set once, never changed.

# ---- The display (MEG lab projector) --------------------------------
SCREEN_SIZE_PX = (1920, 1080)   # width, height in pixels
SCREEN_WIDTH_CM = 60.6          # width of the visible image, cm
VIEWING_DISTANCE_CM = 95.0      # eye to screen, cm
BACKGROUND = (-1, -1, -1)       # black. PsychoPy colours go from -1 to +1
                                # for (red, green, blue): -1 = none, +1 = full.
                                # Black so the trigger pixel's "off" colour
                                # matches the rest of the screen.

# ---- Stimulus sizes, degrees of visual angle ------------------------
FIXATION_SIZE_DEG = 0.6         # width and height of the fixation cross
TARGET_SIZE_DEG = 1.5           # diameter of the target dot
TARGET_OFFSET_DEG = 6.0         # distance of the target from screen centre

# ---- Trial timing, seconds ------------------------------------------
# A trial runs like this:
#   blank screen (ITI) -> fixation cross appears -> random wait (the
#   foreperiod) -> target appears -> response or deadline
ITI = 0.5                # blank screen at the start of each trial
FOREPERIOD_MIN = 0.8     # shortest wait from fixation to target
FOREPERIOD_MAX = 1.5     # longest wait from fixation to target
RESP_DEADLINE = 1.5      # how long the target stays up waiting for a response
THANKS_DURATION = 3.0    # how long the thank-you screen stays up

# ---- Trials ----------------------------------------------------------
CONDITIONS_FILE = 'conditions.csv'  # one row per condition (left, right)
N_REPS = 20                         # repeats of each row: 2 x 20 = 40 trials

# ---- Response keys ---------------------------------------------------
# If the MEG response pad sends keypad codes, use 'num_7' and 'num_2'
# here AND in conditions.csv.
RESP_KEYS = ['7', '2']   # 7 = left index finger, 2 = right index finger

# ---- MEG trigger colours (VPixx Pixel Mode B) -----------------------
# ---------------------------------------------------------------------
# HOW PIXEL MODE TRIGGERS WORK (read this first)
# ---------------------------------------------------------------------
# The DATAPixx3 box sits between the stimulus PC and the projector, so
# every frame the PC draws passes through it. Each time the screen
# refreshes (120 times per second here) the DATAPixx3 looks at ONE
# pixel: the very top-left pixel of the screen.
#
# In "Pixel Mode B" it reads that pixel's BLUE value (a whole number
# from 0 to 255) and puts it out on 8 digital lines. Those lines are
# recorded on the MEG trigger channel. The red and green values are
# ignored, so we always keep them at 0.
#
# Each of these blue values switches on exactly ONE of the 8 lines:
#     1, 2, 4, 8, 16, 32, 64, 128
# Blue = 0 (a black pixel) means all lines are off.
#
# So to "send trigger 2" we colour that one pixel (0, 0, 2) for one
# frame, then make it black again. The pixel is far too dark to see.
#
# Colours are written as (red, green, blue), each from 0 to 255.
# To add a new trigger, give it one of the unused blue values:
# 8, 16, 32, 64 or 128.
# ---------------------------------------------------------------------
TRIG_FIXATION = (0, 0, 1)   # fixation cross appears   -> MEG trigger 1
TRIG_TARGET_L = (0, 0, 2)   # target appears on LEFT   -> MEG trigger 2
TRIG_TARGET_R = (0, 0, 4)   # target appears on RIGHT  -> MEG trigger 4
TRIG_OFF      = (0, 0, 0)   # black pixel              -> all lines off


# =====================================================================
# 2. DEGREES OF VISUAL ANGLE -> PIXELS
# =====================================================================
# Papers report stimulus sizes in degrees of visual angle, but this
# experiment draws in pixels. Nothing to edit here: everything below is
# worked out from the numbers in section 1.

# Step 1: pixels per centimetre on the screen.
#   1920 px / 60.6 cm = about 31.7 px per cm
PIX_PER_CM = SCREEN_SIZE_PX[0] / SCREEN_WIDTH_CM

# Step 2: how many centimetres one degree covers at the screen centre.
#   Picture a triangle from the eye to the screen: the viewing distance
#   is one side, and 1 degree is the angle at the eye. Splitting it into
#   two halves of 0.5 degree each gives two right-angled triangles, so
#   1 degree spans 2 x distance x tan(0.5 degree) on the screen.
#   math.radians() converts degrees to radians, which math.tan() needs.
#   95 cm away -> about 1.66 cm per degree
CM_PER_DEG = 2 * VIEWING_DISTANCE_CM * math.tan(math.radians(0.5))

# Step 3: pixels per degree = pixels per cm x cm per degree
#   (about 52.5 for the MEG lab display).
PIX_PER_DEG = PIX_PER_CM * CM_PER_DEG

# Step 4: sizes in whole pixels. round() turns e.g. 78.8 into 79.
fixSizePix = round(FIXATION_SIZE_DEG * PIX_PER_DEG)        # 32 px
targetSizePix = round(TARGET_SIZE_DEG * PIX_PER_DEG)       # 79 px
targetOffsetPix = round(TARGET_OFFSET_DEG * PIX_PER_DEG)   # 315 px


# =====================================================================
# 3. THE START DIALOG
# =====================================================================
# expInfo is a "dict": a set of named values, written {name: value, ...}.
# gui.DlgFromDict() shows one field per entry and fills in what you type.
# A True/False value (dummy_vpixx) is shown as a tick box.
expName = 'ChoiceRT_VPixxPixelMode'
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
# fullscr=True  -> covers the whole screen. Pixel Mode needs this (see
#                  the check in section 6).
# screen=0      -> the first display. Change to 1 for a second display.
# units='pix'   -> all sizes and positions are in pixels, and (0, 0) is the
#                  CENTRE of the screen; +x is right, +y is up.
# In Pilot mode we use a small window, like Builder.
win = visual.Window(
    size=SCREEN_SIZE_PX if not PILOTING else (800, 600),
    fullscr=not PILOTING,
    screen=0,
    color=BACKGROUND, colorSpace='rgb',
    units='pix',
    allowGUI=False,
    blendMode='avg', useFBO=True,
)
win.mouseVisible = False

# Measure the real refresh rate (should be about 120 Hz) and save it.
expInfo['frameRate'] = win.getActualFrameRate()


# =====================================================================
# 6. CONNECT TO THE DATAPixx3 AND SWITCH ON PIXEL MODE B
# =====================================================================
# --- Step 1: real hardware or dummy mode? ----------------------------
# str(...) == 'True' works whether the dialog hands back True or 'True'.
DUMMY_VPIXX = str(expInfo['dummy_vpixx']) == 'True'

# Without pypixxlib we cannot talk to the hardware, so force dummy mode
# and print a loud warning.
if not PYPIXXLIB_INSTALLED and not DUMMY_VPIXX:
    logging.warning('pypixxlib is not installed: running in dummy mode, '
                    'NO TRIGGERS WILL BE SENT')
    DUMMY_VPIXX = True

# Save the mode in the data file so you can tell a dummy run apart later.
thisExp.addData('dummy_vpixx', DUMMY_VPIXX)

# --- Step 2: stop if the window is not full screen -------------------
# The DATAPixx3 reads the top-left pixel of the whole SCREEN. If our
# window is smaller than the screen, that pixel belongs to the desktop,
# and the trigger lines show whatever colour the desktop has there.
# Pilot mode always uses a small window, so it would cause exactly that.
# "raise RuntimeError" stops the experiment with this message.
if not DUMMY_VPIXX and (PILOTING or not win.fullscr):
    message = ('VPixx Pixel Mode triggers need a FULL-SCREEN window in RUN '
               'mode. Switch from Pilot to Run, or tick dummy_vpixx to test '
               'without triggers.')
    logging.error(message)
    win.close()
    raise RuntimeError(message)

# --- Step 3: connect to the DATAPixx3 and turn on Pixel Mode B -------
# pypixxlib changes settings in a copy kept on this PC (the "register
# cache"). Nothing reaches the device until DPxWriteRegCache() sends
# that copy over USB.
if not DUMMY_VPIXX:
    dp.DPxOpen()                    # connect to the DATAPixx3 over USB
    dp.DPxStopAllScheds()           # stop anything an earlier script left running
    dp.DPxEnableDoutPixelModeB()    # Pixel Mode B: top-left blue value -> trigger lines
    dp.DPxWriteRegCache()           # send these settings to the device


# --- Step 4: release the DATAPixx3 when the experiment quits ---------
# "def" defines a function: a named block of code that runs later, each
# time something calls it by name.
def close_vpixx():
    """Turn Pixel Mode off and disconnect from the DATAPixx3."""
    if DUMMY_VPIXX:
        return                      # nothing to close in dummy mode
    try:
        dp.DPxDisableDoutPixelMode()    # stop driving the trigger lines
        dp.DPxWriteRegCache()           # send that change to the device
        dp.DPxClose()                   # disconnect
    except Exception:
        pass    # the device was already closed or unplugged: nothing to do

# atexit.register() asks Python to run close_vpixx when the script ends,
# however it ends: normally, after Esc, or after an error.
atexit.register(close_vpixx)


# =====================================================================
# 7. THE TRIGGER PIXEL AND THE TRIGGER FUNCTIONS
# =====================================================================
# A rectangle 1 pixel wide and 1 pixel high. In pixel units, (0, 0) is
# the CENTRE of the screen, so the top-left corner is at
# (-width/2, +height/2). Adding/subtracting 0.5 puts the centre of our
# 1-pixel square in the middle of that corner pixel.
#   colorSpace='rgb255' -> colours are given as (R, G, B) from 0 to 255,
#                          exactly like the TRIG_ values
#   lineWidth=0         -> no outline around the square
#   setAutoDraw(True)   -> PsychoPy draws it on every win.flip(), on every
#                          screen, until the experiment ends. We never
#                          have to remember to draw it.
screen_width, screen_height = win.size
trigger_pixel = visual.Rect(
    win,
    units='pix',
    width=1,
    height=1,
    pos=(-screen_width / 2 + 0.5, screen_height / 2 - 0.5),
    colorSpace='rgb255',
    fillColor=TRIG_OFF,
    lineColor=TRIG_OFF,
    lineWidth=0,
    interpolate=False,
    autoLog=False,
)
trigger_pixel.setAutoDraw(True)


def set_trigger_pixel(colour):
    """Give the trigger pixel a new colour, e.g. TRIG_FIXATION or TRIG_OFF.

    The change appears at the next screen refresh (the next win.flip()).
    """
    trigger_pixel.fillColor = colour
    trigger_pixel.lineColor = colour


def record_vpixx_time(column_name):
    """Save the DATAPixx3's own clock time in the data file.

    send_trigger() arranges for this to run immediately after the screen
    refresh that showed the trigger, so the time stamps the trigger.
    """
    if DUMMY_VPIXX:
        return                          # no device, no clock: leave the cell empty
    dp.DPxUpdateRegCache()              # fetch fresh values from the device (incl. its clock)
    thisExp.addData(column_name, dp.DPxGetTime())


def send_trigger(colour, stim_name):
    """Show a trigger colour on the next screen refresh and log it.

    colour    : one of the TRIG_ values, e.g. TRIG_TARGET_L
    stim_name : the stimulus it belongs to, e.g. 'target'; used to name
                the data file columns 'target.trigger' and 'target.vp'
    """
    set_trigger_pixel(colour)
    # colour[2] is the third number in (R, G, B): the blue value, which
    # is the trigger number recorded on the MEG.
    thisExp.addData(stim_name + '.trigger', colour[2])
    # win.callOnFlip(function, argument) runs the function right after
    # the next screen refresh, the one that shows this trigger.
    win.callOnFlip(record_vpixx_time, stim_name + '.vp')


# =====================================================================
# 8. STIMULI, KEYBOARD AND QUITTING
# =====================================================================
# Stimuli are created ONCE here and reused on every trial. Creating them
# inside the trial loop would be slow and could make frames late.
taskInstructions = visual.TextStim(
    win, name='taskInstructions',
    text=('Reaction time task\n\n'
          'Keep your eyes on the cross in the centre of the screen.\n\n'
          'A white dot will appear on the LEFT or RIGHT.\n\n'
          'LEFT dot  ->  LEFT index finger\n'
          'RIGHT dot  ->  RIGHT index finger\n\n'
          'Respond as quickly and accurately as you can.\n\n'
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
    size=(fixSizePix, fixSizePix), pos=(0, 0),
    lineWidth=1.0, lineColor='white', fillColor='white', interpolate=True)

# The target dot. Its position (left or right) is set on each trial.
target = visual.ShapeStim(
    win, name='target', vertices='circle', units='pix',
    size=(targetSizePix, targetSizePix), pos=(0, 0),
    lineWidth=1.0, lineColor='white', fillColor='white', interpolate=True)

# PsychoPy's precise keyboard. Each key press it reports comes with a
# reaction time measured on kb.clock, which we reset at target onset.
kb = keyboard.Keyboard()


def save_and_quit():
    """Save the data files, close the window and stop the script."""
    thisExp.saveAsWideText(fileStem + '.csv', delim='auto')
    thisExp.saveAsPickle(fileStem)
    thisExp.abort()        # tells PsychoPy the files are saved (no second copy)
    logging.flush()
    win.close()
    core.quit()            # close_vpixx() runs now, through atexit


def check_for_escape():
    """Quit (saving the data) if the experimenter pressed Esc."""
    # waitRelease=False: report the key as soon as it goes down.
    # clear=False: leave other keys (7, 2) for the response code to read.
    if kb.getKeys(keyList=['escape'], waitRelease=False, clear=False):
        logging.warning('Esc pressed: stopping the experiment')
        save_and_quit()


# =====================================================================
# 9. CLOCKS
# =====================================================================
# globalClock starts at 0 now, just before the first screen, and runs
# for the rest of the experiment (Builder starts it at the same point). All
# ".started" / ".stopped" times in the data file are on this clock.
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
    check_for_escape()
    keys = kb.getKeys(keyList=RESP_KEYS, waitRelease=False)
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
# per row: [{'targetSide': 'left', 'targetX': -1, 'corrAns': '7'}, ...]
# TrialHandler2 repeats that list N_REPS times in random order.
# thisExp.addLoop() makes the condition columns appear in the data file.
trials = data.TrialHandler2(
    trialList=data.importConditions(CONDITIONS_FILE),
    nReps=N_REPS, method='random', extraInfo=expInfo, name='trials')
thisExp.addLoop(trials)

# "for thisTrial in trials" runs the indented block once per trial.
# thisTrial holds this trial's row of conditions.csv.
for thisTrial in trials:
    targetSide = thisTrial['targetSide']   # 'left' or 'right'
    targetX = thisTrial['targetX']         # -1 (left) or 1 (right)
    corrAns = str(thisTrial['corrAns'])    # '7' or '2'

    # ---- Prepare the trial (Builder's "Begin Routine") ---------------
    # A random foreperiod between FOREPERIOD_MIN and FOREPERIOD_MAX,
    # every value equally likely. Example: 0.8 + 0.5 x 0.7 = 1.15 s.
    foreperiod = FOREPERIOD_MIN + np.random.random() * (FOREPERIOD_MAX - FOREPERIOD_MIN)
    thisExp.addData('foreperiod', foreperiod)

    # When each thing starts, in seconds from the trial start. Fixation,
    # target and the response window all end together, RESP_DEADLINE
    # seconds after the target (see "the deadline" below).
    fixationOn = ITI
    targetOn = ITI + foreperiod

    # Put the target on the correct side: -315 px (left) or +315 px (right).
    target.pos = (targetX * targetOffsetPix, 0)

    # Every stimulus starts the trial "not started". We use .status the
    # same way Builder does: NOT_STARTED -> STARTED -> FINISHED.
    fixation.status = NOT_STARTED
    target.status = NOT_STARTED
    respStatus = NOT_STARTED
    respKey = None           # the key pressed, once there is one
    respRT = None            # its reaction time (s from target onset)
    respDuration = None      # how long the key was held (if known)

    set_trigger_pixel(TRIG_OFF)        # start the trial with a black pixel
    kb.clearEvents()

    # Start the trial clock at the moment of the next flip, and note the
    # trial's start time in the data file.
    thisExp.timestampOnFlip(win, 'trial.started')
    win.callOnFlip(trialClock.reset)
    win.flip()                         # the first frame: a blank screen

    # ---- Run the trial: one pass of this loop per frame -------------
    # On every pass we:
    #   1. ask when the NEXT flip will happen (tThisFlip)
    #   2. switch stimuli on or off if their time has come
    #   3. set the trigger pixel for the next frame
    #   4. read the keyboard
    #   5. flip
    # Because steps 2 and 3 happen before the same flip, a stimulus and
    # its trigger always appear on the SAME screen refresh. (In Builder
    # this is why onsetTriggers has to sit below fixation and target.)
    while True:
        # Time of the coming flip on the trial clock and on the global
        # clock. Comparing THIS time (not "now") with the start times
        # means each stimulus appears on the first frame that is due.
        tThisFlip = win.getFutureFlipTime(clock=trialClock)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)

        # Step 3a: start every frame with the trigger pixel black. If a
        # trigger was sent on the previous frame, this switches it off,
        # so each trigger lasts exactly one frame (8.3 ms, about 10 MEG
        # samples at 1200 Hz). An onset below overrides it, because the
        # colour that counts is the last one set before the flip.
        set_trigger_pixel(TRIG_OFF)

        # ---- fixation cross: on at fixationOn, off at trialEnd -------
        if fixation.status == NOT_STARTED and tThisFlip >= fixationOn - frameTolerance:
            fixation.setAutoDraw(True)       # draw it on every flip from now on
            fixation.status = STARTED
            # tStartRefresh = when the cross appears, on the global clock.
            # tThisFlipGlobal is our best guess now; timestampOnFlip and
            # timeOnFlip replace it with the ACTUAL flip time once the
            # flip has happened.
            fixation.tStartRefresh = tThisFlipGlobal
            thisExp.timestampOnFlip(win, 'fixation.started')
            win.timeOnFlip(fixation, 'tStartRefresh')
            send_trigger(TRIG_FIXATION, 'fixation')        # MEG trigger 1

        # ---- target: on at targetOn, off at trialEnd ----------------
        if target.status == NOT_STARTED and tThisFlip >= targetOn - frameTolerance:
            target.setAutoDraw(True)
            target.status = STARTED
            thisExp.timestampOnFlip(win, 'target.started')
            # Our best guess of the onset time now; replaced by the real
            # flip time once the flip has happened.
            target.tStartRefresh = tThisFlipGlobal
            win.timeOnFlip(target, 'tStartRefresh')
            # Choose the trigger by the side the target is on.
            if targetSide == 'left':
                send_trigger(TRIG_TARGET_L, 'target')      # MEG trigger 2
            else:
                send_trigger(TRIG_TARGET_R, 'target')      # MEG trigger 4

            # The response window opens on the same flip. At that flip
            # the keyboard clock is reset to 0 (so RTs are measured from
            # target onset) and any earlier key presses are thrown away.
            respStatus = STARTED
            thisExp.timestampOnFlip(win, 'resp.started')
            win.callOnFlip(kb.clock.reset)
            win.callOnFlip(kb.clearEvents, eventType='keyboard')
            respJustStarted = True    # don't read keys until after that flip
        else:
            respJustStarted = False

        # To make triggers last longer than one frame, you could keep the
        # trigger colour for e.g. 3 frames instead of switching it off at
        # the top of the next pass.

        # ---- the response --------------------------------------------
        if respStatus == STARTED and not respJustStarted:
            keys = kb.getKeys(keyList=RESP_KEYS, waitRelease=False)
            if keys:
                respKey = keys[0].name         # the first key pressed
                respRT = keys[0].rt            # seconds since target onset
                respDuration = keys[0].duration
                break                          # a response ends the trial

        # ---- the deadline --------------------------------------------
        # If no key was pressed, everything stops RESP_DEADLINE seconds
        # after the target actually appeared (target.tStartRefresh, on
        # the global clock), as Builder does it.
        if (target.status == STARTED
                and tThisFlipGlobal > target.tStartRefresh + RESP_DEADLINE - frameTolerance):
            thisExp.addData('target.stopped', tThisFlipGlobal)
            thisExp.addData('fixation.stopped', tThisFlipGlobal)
            thisExp.addData('resp.stopped', tThisFlipGlobal)
            break

        check_for_escape()
        win.flip()

    # ---- End of the trial (Builder's "End Routine") -----------------
    fixation.setAutoDraw(False)
    target.setAutoDraw(False)
    fixation.status = FINISHED
    target.status = FINISHED
    thisExp.addData('trial.stopped', globalClock.getTime())

    # Save the response the way Builder's Keyboard component does:
    # resp.keys, resp.corr (1 = correct, 0 = wrong or none), resp.rt.
    thisExp.addData('resp.keys', respKey)
    if respKey is not None:
        thisExp.addData('resp.corr', int(respKey == corrAns))
        thisExp.addData('resp.rt', respRT)
        thisExp.addData('resp.duration', respDuration)
        thisExp.addData('timeout', 0)     # responded in time
    else:
        thisExp.addData('resp.corr', 0)
        thisExp.addData('timeout', 1)     # no response before the deadline

    # Safety step: trigger pixel back to black between trials.
    set_trigger_pixel(TRIG_OFF)

    # Finish this trial's row of the data file and start a new one.
    thisExp.nextEntry()


# =====================================================================
# 12. THANK-YOU SCREEN (Builder routine "thanks")
# =====================================================================
thanksText.setAutoDraw(True)
thisExp.timestampOnFlip(win, 'thanksText.started')
win.callOnFlip(trialClock.reset)
win.flip()
while trialClock.getTime() < THANKS_DURATION:
    check_for_escape()
    win.flip()
thanksText.setAutoDraw(False)
win.flip()

# Save everything and quit. close_vpixx() runs automatically (atexit).
save_and_quit()
