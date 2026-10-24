#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ChoiceRT_EyeLink.py  -  PsychoPy CODER version
=====================================================================

Two-choice visual reaction time task with an EyeLink 1000 Plus eye
tracker. This is the Coder (pure Python) twin of the Builder experiment
builder_samples/ChoiceRT_EyeLink/ChoiceRT_EyeLink.psyexp. Same task, same
timing, the same eye-tracker set-up and the same messages in the
eye-tracking data file (EDF), so Data Viewer and your analysis scripts
treat both versions the same way.

In Builder, the EyeLink plugin's components (Initialize, CameraSetup,
DriftCheck, HostDrawing, StartRecord, MarkEvents, StopRecord) write the
eye-tracker code for you. Here it is written out with "pylink", SR
Research's Python library, so you can see what each component does.

Written for PsychoPy 2026.2.3 with the psychopy-eyelink plugin installed
(it provides pylink and EyeLinkCoreGraphicsPsychoPy), and the Scully
Center OPM-MEG lab:
    display 1920 x 1080 px, 120 Hz, 60.6 cm wide, viewed from 95 cm
    EyeLink 1000 Plus in Remote Mode, 500 Hz, 13-point (HV13) calibration
    response keys: 7 = left index finger, 2 = right index finger

---------------------------------------------------------------------
THE TASK
---------------------------------------------------------------------
    experimenter screen   press SPACE -> Camera Setup (calibrate, validate)
    instructions          press 7, 2 or SPACE to go on     EDF: TASK_START
    drift check           one, before the trials
    40 trials, random order (20 left, 20 right), each one:
        start recording                                  EDF: TRIALID n
        fixation cross appears at 0.2 s
        random wait 0.8-1.5 s (the "foreperiod")
        white dot appears LEFT or RIGHT                  EDF: TARGET_ONSET_LEFT
                                                              /_RIGHT
        press 7 (left) or 2 (right) within 1.5 s
        stop recording                                   EDF: TRIAL_RESULT 0
    thank-you screen 3 s                                 EDF: TASK_END
    the EDF is copied from the EyeLink Host PC to this computer

---------------------------------------------------------------------
HOW TO RUN IT
---------------------------------------------------------------------
    1. Install the psychopy-eyelink plugin (Tools > Plugins/Packages
       Manager), then restart PsychoPy.
    2. Open this file in PsychoPy's Coder window (File > Open).
    3. Keep conditions.csv and images/fixTarget.bmp next to this file.
    4. Click "Run". Fill in the start dialog, including an EDF file name of
       up to 8 letters, digits or underscores.
    5. To test without an eye tracker, set DUMMY_MODE = True in section 1
       (or answer "OK" when the script says it can't find the tracker).
    QUITTING: Esc is used by the calibration screens, so it does NOT quit
    this experiment. Press Ctrl-C during a trial to stop. The EDF is still
    copied over and the data so far are saved.

---------------------------------------------------------------------
EYE TRACKER BASICS (read this first)
---------------------------------------------------------------------
The EyeLink has its own computer, the "Host PC". It records the eye data
and saves them in an .EDF file ON THE HOST PC. This script, on the
stimulus PC, talks to the Host PC over an Ethernet cable (address
100.1.1.1) using pylink. It:
    - sends COMMANDS (sendCommand) that change tracker settings, e.g.
      "sample_rate 500";
    - sends MESSAGES (sendMessage) that are written into the EDF with a
      time stamp, e.g. "TARGET_ONSET_LEFT". Messages are how you find the
      events of your experiment in the eye data later;
    - starts and stops recording around each trial;
    - copies the EDF over to this computer at the end.
Data Viewer (SR Research's analysis program) understands a few special
messages: TRIALID / TRIAL_RESULT mark the start and end of a trial,
"!V TRIAL_VAR name value" adds a trial variable, and "!V IAREA" /
"!V DRAW_LIST" point to interest-area and drawing files.

---------------------------------------------------------------------
BUILDER vs CODER - IF YOU KNOW ONE BUT NOT THE OTHER
---------------------------------------------------------------------
Builder writes a Python script like this one for you every time you press
Run. In Coder you write that script yourself. The table shows where each
Builder piece went:

    Builder                          This script
    -------                          -----------
    Experiment Settings              sections 1, 4, 6, 7, 12
    start dialog (Experiment info)   section 3
    EyeLink Initialize component     sections 5 and 8, and the start of 13
    EyeLink CameraSetup component    section 13
    EyeLink DriftCheck component     section 15
    EyeLink HostDrawing + StartRecord   start of each trial (section 16)
    EyeLink MarkEvents component     section 10 (functions) and the trial
    EyeLink StopRecord component     end of each trial (section 16)
    stimulus components              section 11
    code components                  where they ran, with the same
                                     comments (elConfig, taskStartMsg, ...)
    a routine (instruct, trial ...)  a "while" loop that draws one frame
                                     per pass and calls win.flip()
    a loop (trials)                  a "for" loop over a TrialHandler2

The one idea that matters most: THE SCREEN ONLY CHANGES WHEN YOU CALL
win.flip(). You draw everything for the next frame first, then flip. The
flip waits for the display's next refresh (every 8.33 ms at 120 Hz) and
shows the new frame. Anything you want to happen "exactly when the
stimulus appears" - such as an EDF message - must be timed to that flip
with win.callOnFlip().
"""

# =====================================================================
# 0. IMPORT THE LIBRARIES WE NEED
# =====================================================================
# "import" loads code that someone else wrote so we can use it here.
import psychopy
# activatePlugins() makes the packages installed with PsychoPy's plugin
# manager (here: psychopy-eyelink, which brings pylink with it)
# available to this script. Builder does the same at the top of every
# script it writes.
from psychopy import plugins
plugins.activatePlugins()

#   visual   - windows and things to draw (text, shapes, ...)
#   core     - clocks and quitting
#   data     - the data file, the trial list and the trials loop
#   gui      - dialog boxes
#   logging  - writes messages to the console and to a .log file
#   keyboard - PsychoPy's precise keyboard (it time-stamps each key press)
from psychopy import visual, core, data, gui, logging
from psychopy.hardware import keyboard
from psychopy.constants import NOT_STARTED, STARTED, FINISHED

import math        # Python's maths library: tan(), radians(), ...
import os          # file and folder names
import sys         # used to stop the script
import time        # the date and time, and short pauses
import platform    # which operating system we are on (macOS or not)
from string import ascii_letters, digits   # allowed EDF file name characters

import numpy as np   # numbers and random numbers ("np" is its short name)

# pylink: SR Research's library for controlling the EyeLink.
import pylink
# EyeLinkCoreGraphicsPsychoPy draws the calibration and drift-check
# screens in OUR PsychoPy window, and shows the camera image during
# Camera Setup. It comes with the psychopy-eyelink plugin.
from EyeLinkCoreGraphicsPsychoPy import EyeLinkCoreGraphicsPsychoPy


# =====================================================================
# 1. SETTINGS - EDIT HERE
# =====================================================================
# Everything you might want to change is collected in this section.

# ---- The display (MEG lab projector) --------------------------------
screenSizePix = (1920, 1080)  # width, height in pixels
screenWidthCm = 60.6          # width of the image on the screen, in cm
viewingDistanceCm = 95        # distance from the eyes to the screen, in cm
background = (0, 0, 0)        # mid-grey. PsychoPy colours go from -1 to +1
                              # for (red, green, blue): -1 = none, +1 = full

# ---- Stimulus sizes, in degrees of visual angle ---------------------
fixationSizeDeg = 0.6         # width and height of the central cross
targetSizeDeg = 1.5           # diameter of the target dot
targetEccDeg = 6.0            # distance of the target from the centre
                              # (the same distance on the left and right)

# ---- Trial timing, seconds ------------------------------------------
fixationOnset = 0.2           # cross appears 0.2 s into the trial
foreperiodMin = 0.8           # then a random wait between these two
foreperiodMax = 1.5           #   values before the target
respDeadline = 1.5            # the target stays up this long; the trial
                              # ends at a response or at this deadline
thanksDuration = 3.0          # how long the thank-you screen stays up

# ---- Trials ----------------------------------------------------------
conditionsFile = 'conditions.csv'  # one row per condition (left, right)
nReps = 20                         # repeats of each row: 2 x 20 = 40 trials

# ---- Response keys ---------------------------------------------------
# If the MEG response pad sends keypad codes, use 'num_7' and 'num_2'
# here AND in conditions.csv.
respKeys = ['7', '2']   # 7 = left index finger, 2 = right index finger

# ---- Eye tracker -----------------------------------------------------
DUMMY_MODE = False            # True = no eye tracker; just pretend (for
                              # testing). This is the "Dummy Mode" tick box
                              # of Builder's Initialize component.
hostIP = '100.1.1.1'          # the EyeLink Host PC's network address
calibrationType = 'HV13'      # 13-point calibration (needed in Remote Mode)
calTargetFile = 'images/fixTarget.bmp'   # calibration / drift-check target
interestAreaMargin = 20       # pixels added around each stimulus to make its
                              # interest area (for Data Viewer)


# =====================================================================
# 2. DEGREES OF VISUAL ANGLE -> PIXELS
# =====================================================================
# Papers report stimulus sizes in degrees of visual angle, but this
# experiment draws in pixels. Nothing to edit here.

# 1 degree covers 2 * distance * tan(0.5 degrees) centimetres of screen.
# math.radians() converts degrees to radians, which tan() expects.
cmPerDeg = 2 * viewingDistanceCm * math.tan(math.radians(0.5))

# How many pixels fit in 1 cm of screen.
pixPerCm = screenSizePix[0] / screenWidthCm

# How many pixels make up 1 degree (about 52.5 with the numbers above).
pixPerDeg = cmPerDeg * pixPerCm

# Final sizes in pixels. round() gives a whole number of pixels.
fixationSizePix = round(fixationSizeDeg * pixPerDeg)   # 32 px
targetSizePix = round(targetSizeDeg * pixPerDeg)       # 79 px
targetEccPix = round(targetEccDeg * pixPerDeg)         # 315 px


# =====================================================================
# 3. THE START DIALOG
# =====================================================================
# expInfo is a "dict": a set of named values, written {name: value, ...}.
# gui.DlgFromDict() shows one field per entry and fills in what you type.
# (Builder shows the EDF name in a dialog of its own, before this one;
# here it is one more field.)
expName = 'ChoiceRT_EyeLink'
expInfo = {
    'participant': '',
    'session': '01',
    'edf_name': 'Test',   # name of the EDF file on the Host PC
}
# On a Mac, the calibration screens need to know whether the display is a
# high-resolution ("Retina") one. A True/False value shows as a tick box.
onMac = 'Darwin' in platform.system()
if onMac:
    expInfo['retina_display'] = False

# "Pilot" mode: PsychoPy's Pilot/Run switch (top of the Coder window)
# passes "--pilot" to this script. setPilotModeFromArgs() reads it and
# gives True (Pilot) or False (Run).
PILOTING = core.setPilotModeFromArgs()
if PILOTING:
    expInfo['participant'] = 'pilot'

# Show the dialog until the EDF name is valid. The Host PC only accepts
# file names of up to 8 letters, digits or underscores.
# "while True" repeats forever, until "break" leaves the loop.
allowedChars = ascii_letters + digits + '_'
while True:
    dlg = gui.DlgFromDict(dictionary=expInfo, sortKeys=False, title=expName)
    if not dlg.OK:                       # the experimenter pressed Cancel
        core.quit()
    # Remove spaces at the end and any ".edf" ending.
    edfName = str(expInfo['edf_name']).rstrip().split('.')[0]
    if not edfName:
        edfName = 'Test'                 # empty -> use the default name
        break
    if not all(c in allowedChars for c in edfName):
        print('ERROR: the EDF file name may only use letters, digits and _')
    elif len(edfName) > 8:
        print('ERROR: the EDF file name must be 8 characters or fewer')
    else:
        break                            # the name is fine
expInfo['edf_name'] = edfName
useRetina = onMac and str(expInfo.get('retina_display')) == 'True'

# Extra information saved with every row of the data file.
expInfo['date'] = data.getDateStr()     # e.g. 2026-10-23_14h05.31.123
expInfo['expName'] = expName
expInfo['psychopyVersion'] = psychopy.__version__   # e.g. 2026.2.3


# =====================================================================
# 4. THE SESSION FOLDER
# =====================================================================
# Everything for one session goes into one folder:
#     results/<EDFname>_<YYYY_MM_DD_HH_MM>/
# the EDF (copied from the Host PC at the end), the Data Viewer files
# (aoi/ and graphics/), PsychoPy's data files and the trial log. This is
# exactly what Builder's EyeLink Initialize component does.

# Make sure we work in the folder that contains this script, so that
# 'conditions.csv', 'images' and 'results' are found there.
thisDir = os.path.dirname(os.path.abspath(__file__))
os.chdir(thisDir)

resultsFolder = 'results'
# time.strftime() writes the current date and time in the given pattern,
# e.g. "_2026_10_23_14_05".
timeStr = time.strftime('_%Y_%m_%d_%H_%M', time.localtime())
sessionIdentifier = edfName + timeStr          # e.g. Test_2026_10_23_14_05
sessionFolder = os.path.join(resultsFolder, sessionIdentifier)
os.makedirs(sessionFolder, exist_ok=True)      # create the folders if needed

# The Data Viewer drawing files (graphics/) and interest-area files
# (aoi/) for each trial go into sub-folders of the session folder.
drawListFolder = os.path.join(sessionFolder, 'graphics')
interestAreaFolder = os.path.join(sessionFolder, 'aoi')
os.makedirs(drawListFolder, exist_ok=True)
os.makedirs(interestAreaFolder, exist_ok=True)


# =====================================================================
# 5. CONNECT TO THE EYE TRACKER
# =====================================================================
# pylink.EyeLink(address) connects to the Host PC. pylink.EyeLink(None)
# makes a pretend ("dummy") tracker that accepts every command and does
# nothing, so the rest of the script can run unchanged without a tracker.
dummyMode = DUMMY_MODE
if dummyMode:
    el_tracker = pylink.EyeLink(None)
else:
    try:
        el_tracker = pylink.EyeLink(hostIP)
    except RuntimeError as error:
        # No tracker answered. Ask whether to carry on without one.
        dlg = gui.Dlg('Dummy Mode?')
        dlg.addText('Could not connect to tracker at %s -- continue in Dummy Mode?'
                    % hostIP)
        dlg.show()
        if dlg.OK:
            dummyMode = True
            el_tracker = pylink.EyeLink(None)
        else:
            print('user cancelled')
            core.quit()
expInfo['dummy_eyelink'] = dummyMode


# =====================================================================
# 6. DATA FILES
# =====================================================================
# PsychoPy's own files go into the session folder too:
#     <participant>_ChoiceRT_EyeLink_<date>.csv / .psydat / .log
fileStem = os.path.join(thisDir, sessionFolder, '%s_%s_%s' % (
    expInfo['participant'], expName, expInfo['date']))

# The ExperimentHandler collects everything we save with addData() and
# writes it to a .csv file (one row per trial) and a .psydat file at the
# end. extraInfo=expInfo copies the dialog answers into every row.
thisExp = data.ExperimentHandler(
    name=expName, extraInfo=expInfo,
    savePickle=True, saveWideText=True,
    dataFileName=fileStem, sortColumns='time')
thisExp.addData('piloting', PILOTING)

# The .log file: a time-stamped list of everything that happened
# (stimulus onsets, key presses, routine events). "exp" level, as in the
# Builder version.
logging.console.setLevel(logging.WARNING)   # only warnings in the console
logFile = logging.LogFile(fileStem + '.log', level=logging.EXP)


# =====================================================================
# 7. THE WINDOW
# =====================================================================
# fullscr=True  -> covers the whole screen.
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

# The screen size in pixels, as the eye tracker needs it. On a Mac with a
# Retina display, PsychoPy's pixels are twice the size of the screen's.
scn_width, scn_height = win.size
if useRetina:
    scn_width = int(scn_width / 2.0)
    scn_height = int(scn_height / 2.0)


# =====================================================================
# 8. OPEN THE EDF AND CONFIGURE THE TRACKER
#    (Builder: the EyeLink Initialize component)
# =====================================================================
# Open an EDF data file on the Host PC. It is copied to this computer at
# the end (see terminate_task in section 10).
edfFile = edfName + '.EDF'
try:
    el_tracker.openDataFile(edfFile)
except RuntimeError as err:
    print('ERROR:', err)
    if el_tracker.isConnected():
        el_tracker.close()
    core.quit()

# A note at the top of the EDF saying which script recorded it. Data
# Viewer shows text starting with "RECORDED BY" in its Inspector window.
el_tracker.sendCommand("add_file_preamble_text 'RECORDED BY %s'"
                       % os.path.basename(__file__))

# Settings can only be changed while the tracker is "offline" (idle).
el_tracker.setOfflineMode()

# Which EyeLink model is this? 5 = EyeLink 1000 Plus. (0 in dummy mode.)
eyelinkVer = 0
if not dummyMode:
    vstr = el_tracker.getTrackerVersionString()
    eyelinkVer = int(vstr.split()[-1].split('.')[0])
    print('Running experiment on %s, version %d' % (vstr, eyelinkVer))

# What to save in the EDF ("file") and what to send to this computer
# while recording ("link"). These lists include everything, as the
# Builder plugin does. HTARGET = the head-target sticker used in Remote
# Mode.
fileEventFlags = 'LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON,INPUT'
linkEventFlags = 'LEFT,RIGHT,FIXATION,SACCADE,BLINK,BUTTON,FIXUPDATE,INPUT'
if eyelinkVer > 3:
    fileSampleFlags = 'LEFT,RIGHT,GAZE,HREF,RAW,AREA,HTARGET,GAZERES,BUTTON,STATUS,INPUT'
    linkSampleFlags = 'LEFT,RIGHT,GAZE,GAZERES,AREA,HTARGET,STATUS,INPUT'
else:
    fileSampleFlags = 'LEFT,RIGHT,GAZE,HREF,PUPIL,AREA,GAZERES,BUTTON,STATUS,INPUT'
    linkSampleFlags = 'LEFT,RIGHT,GAZE,GAZERES,AREA,STATUS,INPUT'
el_tracker.sendCommand('file_event_filter = %s' % fileEventFlags)
el_tracker.sendCommand('file_sample_data = %s' % fileSampleFlags)
el_tracker.sendCommand('link_event_filter = %s' % linkEventFlags)
el_tracker.sendCommand('link_sample_data = %s' % linkSampleFlags)
# Let a gamepad/button box on the Host PC accept calibration targets.
el_tracker.sendCommand("button_function 5 'accept_target_fixation'")


# =====================================================================
# 9. SMALL HELPERS: COORDINATES AND COLOURS FOR THE EYELINK
# =====================================================================
# PsychoPy and the EyeLink measure positions differently:
#   PsychoPy (units='pix'): (0, 0) is the CENTRE of the screen, +y is UP.
#   EyeLink:                (0, 0) is the TOP-LEFT corner,    +y is DOWN.
def eyelink_pos_size(stim):
    """Return a stimulus' centre and size in EyeLink pixel coordinates,
    as ([x, y], [width, height]) in whole pixels."""
    x = stim.pos[0] + scn_width / 2
    y = scn_height / 2 - stim.pos[1]
    return ([int(round(x)), int(round(y))],
            [int(round(stim.size[0])), int(round(stim.size[1]))])


def eyelink_color():
    """The window's background colour as 0-255 (R, G, B) numbers, the way
    Data Viewer wants it. PsychoPy's -1..+1 becomes 0..255."""
    return tuple(int(round((c + 1) / 2 * 255)) for c in win.color)


# =====================================================================
# 10. EYELINK FUNCTIONS USED DURING THE EXPERIMENT
# =====================================================================
# "def" defines a function: a named block of code that runs later, each
# time something calls it by name.

def clear_screen():
    """Fill the window with the calibration background colour."""
    win.fillColor = genv.getBackgroundColor()
    win.flip()


def show_msg(text):
    """Show a short message in the middle of the screen."""
    msg = visual.TextStim(win, text, color=genv.getForegroundColor(),
                          wrapWidth=scn_width / 2)
    clear_screen()
    msg.draw()
    win.flip()


def abort_trial():
    """Stop recording and mark the trial as failed in the EDF."""
    el_tracker = pylink.getEYELINK()
    if el_tracker.isRecording():
        pylink.pumpDelay(100)            # 100 ms more, to catch the last events
        el_tracker.stopRecording()
    clear_screen()
    # Tell Data Viewer to clear its picture of the screen (grey).
    el_tracker.sendMessage('!V CLEAR %d %d %d' % (116, 116, 116))
    el_tracker.sendMessage('TRIAL_RESULT %d' % pylink.TRIAL_ERROR)
    return pylink.TRIAL_ERROR


def terminate_task():
    """End the session: close the EDF, copy it to this computer, save
    PsychoPy's data and quit. Used at the normal end AND after Ctrl-C."""
    el_tracker = pylink.getEYELINK()
    if el_tracker.isConnected():
        # Finish the current trial first if we stopped in the middle of one.
        if el_tracker.isRecording() == pylink.TRIAL_OK:
            abort_trial()
        el_tracker.setOfflineMode()
        el_tracker.sendCommand('clear_screen 0')   # clear the Host PC display
        pylink.msecDelay(500)
        el_tracker.closeDataFile()                 # close the EDF on the Host PC

        # Copy the EDF from the Host PC into the session folder, renamed to
        # include the date and time: results/<session>/<session>.EDF
        show_msg('EDF data is transferring from EyeLink Host PC...')
        localEdf = os.path.join(sessionFolder, sessionIdentifier + '.EDF')
        try:
            el_tracker.receiveDataFile(edfFile, localEdf)
        except RuntimeError as error:
            print('ERROR:', error)
        el_tracker.close()                         # disconnect

    # Save PsychoPy's data files and close the trial log.
    thisExp.saveAsWideText(fileStem + '.csv', delim='auto')
    thisExp.saveAsPickle(fileStem)
    thisExp.abort()        # tells PsychoPy the files are saved (no second copy)
    trialLog.close()
    logging.flush()
    win.close()
    core.quit()


# ---- Data Viewer event marking (Builder: the MarkEvents component) ---
# For every stimulus, MarkEvents writes into the EDF:
#   "<ms> fixation_ONSET"    when the stimulus appears. <ms> is how many
#                            milliseconds BEFORE the message the flip was
#                            (Data Viewer subtracts it), so the event is
#                            placed exactly at the flip.
#   "!V TRIAL_VAR fixation_ONSET_TIME <ms>"   the onset time as a variable
#   "fixation_OFFSET"        at the end of the trial
# and, for Data Viewer's Trial View:
#   graphics/TRIAL_xxxx_ROUTINE_01.dlf   a red box where each stimulus was
#   aoi/TRIAL_xxxx_ROUTINE_01.ias        an ellipse "interest area" around
#                                        each stimulus, and when it was on
# The functions below do the same for this experiment's two stimuli.
# "dv" is a dict that holds this trial's Data Viewer bookkeeping.
dv = {}


def dv_start_trial(trialIndex):
    """Open this trial's drawing (.dlf) and interest-area (.ias) files."""
    dv['dlfName'] = 'TRIAL_%04d_ROUTINE_%02d.dlf' % (trialIndex, 1)
    dv['iasName'] = 'TRIAL_%04d_ROUTINE_%02d.ias' % (trialIndex, 1)
    dv['dlf'] = open(os.path.join(drawListFolder, dv['dlfName']), 'w')
    dv['ias'] = open(os.path.join(interestAreaFolder, dv['iasName']), 'w')
    dv['zeroTime'] = None     # time of the first onset in this trial
    dv['onStims'] = []        # stimuli that have appeared so far
    dv['iaStart'] = {}        # when each one appeared


def mark_onset(stim, iaIndex):
    """Write the EDF messages and Data Viewer lines for a stimulus that
    has just appeared. Run with win.callOnFlip(), so it runs straight
    after the flip that showed the stimulus.

    stim    : the stimulus (fixation or target)
    iaIndex : its interest-area number (1, 2, ...)
    """
    el_tracker = pylink.getEYELINK()
    frameTime = globalClock.getTime()          # (just after) the flip
    # stim.tStartRefresh is the flip time, set by win.timeOnFlip().
    el_tracker.sendMessage('%s %s_ONSET' % (
        int(round((globalClock.getTime() - stim.tStartRefresh) * 1000)), stim.name))
    el_tracker.sendMessage('!V TRIAL_VAR %s_ONSET_TIME %i' % (
        stim.name, stim.tStartRefresh * 1000))
    if dv['zeroTime'] is None:
        # The first stimulus of the trial: tell Data Viewer where this
        # trial's interest-area and drawing files are. Times inside those
        # files are counted from this moment.
        dv['zeroTime'] = frameTime
        el_tracker.sendMessage('%s !V IAREA FILE aoi/%s' % (
            int(round((globalClock.getTime() - frameTime) * 1000)), dv['iasName']))
        el_tracker.sendMessage('%s !V DRAW_LIST graphics/%s' % (
            int(round((globalClock.getTime() - frameTime) * 1000)) - 3, dv['dlfName']))
        dv['dlf'].write('0 CLEAR %d %d %d\n' % eyelink_color())
    # A red box where the stimulus is, in Data Viewer's Trial View.
    (x, y), (w, h) = eyelink_pos_size(stim)
    dv['dlf'].write('%i DRAWBOX 255 0 0 %i %i %i %i\n' % (
        int(round((dv['zeroTime'] - frameTime) * 1000)),
        x - w / 2, y - h / 2, x + w / 2, y + h / 2))
    dv['onStims'].append((stim, iaIndex))
    dv['iaStart'][stim.name] = frameTime


def dv_end_trial():
    """At the end of the trial: offset messages, and the interest area of
    every stimulus that was shown. Then close this trial's files."""
    el_tracker = pylink.getEYELINK()
    for stim, iaIndex in dv['onStims']:
        el_tracker.sendMessage('%s_OFFSET' % stim.name)
    # One interest-area line per stimulus: start and end time (ms,
    # counted from zeroTime), shape, number, left, top, right, bottom,
    # name. The ellipse is the stimulus plus interestAreaMargin pixels.
    m = interestAreaMargin
    for stim, iaIndex in dv['onStims']:
        (x, y), (w, h) = eyelink_pos_size(stim)
        dv['ias'].write('%i %i IAREA %s %i %i %i %i %i %s\n' % (
            int(round((dv['zeroTime'] - dv['iaStart'][stim.name]) * 1000)),
            int(round((dv['zeroTime'] - globalClock.getTime()) * 1000 - 1)),
            'ELLIPSE', iaIndex,
            x - (w / 2 + m), y - (h / 2 + m), x + (w / 2 + m), y + (h / 2 + m),
            stim.name))
    dv['ias'].close()
    dv['dlf'].close()


def mark_response(respStart, respKey, respRT, respCorr):
    """EDF messages for the key press (Builder: MarkEvents' response part).

    respStart : flip time at which the response window opened
    respKey, respRT, respCorr : the response, or None / None / 0
    """
    el_tracker = pylink.getEYELINK()
    if respKey is not None:
        # "<ms> Keyboard_EVENT": <ms> = how long ago the key was pressed.
        offset = int(round((globalClock.getTime() - (respStart + respRT)) * 1000))
        el_tracker.sendMessage('%i %s_EVENT' % (offset, 'Keyboard'))
        el_tracker.sendMessage('!V TRIAL_VAR Keyboard.rt(s) %s' % respRT)
    else:
        el_tracker.sendMessage('!V TRIAL_VAR Keyboard.rt(s) []')
    el_tracker.sendMessage('!V TRIAL_VAR Keyboard.corr %s' % respCorr)
    el_tracker.sendMessage('!V TRIAL_VAR Keyboard.keys %s' % respKey)


# =====================================================================
# 11. STIMULI, KEYBOARD AND THE TRIAL LOG
# =====================================================================
# Stimuli are created ONCE here and reused on every trial. Creating them
# inside the trial loop would be slow and could make frames late.
elInstructions = visual.TextStim(
    win, name='elInstructions',
    text=('Eye tracker setup\n\n'
          'Please keep your head still and look at the screen.\n\n'
          'We will now calibrate the eye tracker: follow the dot with your '
          'eyes and look at its centre until it moves.\n\n'
          '(Experimenter: press SPACE to enter Camera Setup.\n'
          'Enter = camera image, C = calibrate, V = validate, '
          'O = continue to the task.)'),
    font='Open Sans', height=36, wrapWidth=1500, color='white', units='pix')

taskInstructions = visual.TextStim(
    win, name='taskInstructions',
    text=('Reaction time task\n\n'
          'Keep your eyes on the cross in the centre of the screen.\n\n'
          'A white dot will appear on the LEFT or RIGHT.\n\n'
          'LEFT dot  ->  LEFT index finger\n'
          'RIGHT dot  ->  RIGHT index finger\n\n'
          'Respond as quickly and accurately as you can.\n\n'
          'First, look at the target dot so we can check the eye tracker.\n\n'
          'Press either button when ready.'),
    font='Open Sans', height=36, wrapWidth=1500, color='white', units='pix')

endScreen = visual.TextStim(
    win, name='endScreen',
    text='All done - thank you!\n\nPlease stay still while we save the data.',
    font='Open Sans', height=36, wrapWidth=1500, color='white', units='pix')

# The fixation cross. ShapeStim with vertices='cross' is what Builder's
# Polygon component makes when you choose the "cross" shape. The name is
# used in the EDF messages (fixation_ONSET ...).
fixation = visual.ShapeStim(
    win, name='fixation', vertices='cross', units='pix',
    size=(fixationSizePix, fixationSizePix), pos=(0, 0),
    lineWidth=1.0, lineColor='white', fillColor='white', interpolate=True)

# The target dot. Its position (left or right) is set on each trial.
target = visual.ShapeStim(
    win, name='target', vertices='circle', units='pix',
    size=(targetSizePix, targetSizePix), pos=(0, 0),
    lineWidth=1.0, lineColor='white', fillColor='white', interpolate=True)

# PsychoPy's precise keyboard. Each key press it reports comes with a
# reaction time measured on kb.clock, which we reset at target onset.
kb = keyboard.Keyboard()

# ---- The trial log (Builder: the trialLog code component) -----------
# A simple table with ONE ROW PER TRIAL. Columns are separated by tabs,
# so it opens in Excel, R, Python, etc. It sits next to PsychoPy's data
# files and its name ends in "_trials_log.tsv".
logColumns = ['participant', 'session', 'date', 'edf_file', 'trial',
              'eyelink_trialid', 'target_side', 'target_x_pix', 'corr_ans',
              'foreperiod_s', 'fixation_onset_s', 'target_onset_s',
              'resp_key', 'rt_s', 'correct', 'timeout']
# Open the file for writing ('w'), then write the row of column names.
# '\t'.join(...) puts a tab between the names; '\n' ends the line.
trialLog = open(fileStem + '_trials_log.tsv', 'w')
trialLog.write('\t'.join(logColumns) + '\n')

# ---- Ctrl-C to quit ----------------------------------------------------
# Esc belongs to the calibration screens, so Ctrl-C quits instead. We
# remember which of the keys are held down right now.
heldKeys = []


def check_for_ctrl_c():
    """Quit cleanly (EDF copied, data saved) if Ctrl-C is pressed."""
    for key in kb.getKeys(keyList=['lctrl', 'rctrl', 'c'], waitRelease=False, clear=False):
        if key.name not in heldKeys:
            heldKeys.append(key.name)
    if ('lctrl' in heldKeys or 'rctrl' in heldKeys) and 'c' in heldKeys:
        pylink.getEYELINK().sendMessage('terminated_by_user')
        terminate_task()
    for key in kb.getKeys(keyList=['lctrl', 'rctrl', 'c'], waitRelease=True, clear=False):
        if key.name in heldKeys:
            heldKeys.remove(key.name)


# =====================================================================
# 12. CLOCKS
# =====================================================================
# globalClock starts at 0 now, just before the first screen, and runs
# for the rest of the experiment (Builder starts it at the same point).
# All ".started" / ".stopped" times in the data file and the trial log
# are on this clock. setDefaultClock() makes the log file and
# win.getFutureFlipTime() use it too, exactly as Builder does.
globalClock = core.Clock()
logging.setDefaultClock(globalClock)

# trialClock is reset to 0 at the start of every trial (Builder calls it
# "routineTimer"). Start and stop times within a trial are measured on it.
trialClock = core.Clock()

# Builder's "frameTolerance": a tiny margin (1 ms), so that a frame due at
# exactly the start time is not missed because of rounding.
frameTolerance = 0.001


# =====================================================================
# 13. EXPERIMENTER SCREEN AND CAMERA SETUP
#     (Builder routine "eyelinkSetup": elConfig, Initialize, CameraSetup)
# =====================================================================
# ---- elConfig: tracker settings for this lab -------------------------
# Only send settings when a real eye tracker is connected.
if not dummyMode:
    # Put the tracker in "offline" mode (idle, not recording). Its
    # settings can only be changed while it is offline.
    el_tracker.setOfflineMode()

    # Record at 500 samples per second. In Remote Mode, 500 Hz is the
    # fastest rate the EyeLink 1000 Plus can record.
    el_tracker.sendCommand('sample_rate 500')

    # Remote Mode itself (no chin rest; a small target sticker on the
    # participant's forehead) is chosen on the EyeLink Host PC, under
    # "Set Options". To choose it from this script instead, delete the
    # "#" at the start of the next line.
    # RTABLER means: desktop mount, remote mode, one eye.
    # el_tracker.sendCommand('elcl_select_configuration = RTABLER')

    # Write a note into the EDF so anyone analysing it later can see
    # which settings were used.
    el_tracker.sendMessage('SESSION_CONFIG remote_mode sample_rate_500')

# ---- The experimenter screen: wait for SPACE --------------------------
kb.clearEvents()
elInstructions.setAutoDraw(True)
while True:
    keys = kb.getKeys(keyList=['space'], waitRelease=False)
    if keys:
        thisExp.addData('key_setup.keys', keys[-1].name)
        thisExp.addData('key_setup.rt', keys[-1].rt)
        break
    win.flip()
elInstructions.setAutoDraw(False)

# ---- Initialize: tell the tracker the screen size ---------------------
# Pass the display's pixel coordinates (left, top, right, bottom) to the
# tracker, and write them into the EDF for Data Viewer.
el_tracker.sendCommand('screen_pixel_coords = 0 0 %d %d' % (scn_width - 1, scn_height - 1))
el_tracker.sendMessage('DISPLAY_COORDS  0 0 %d %d' % (scn_width - 1, scn_height - 1))

# The TRIALID number written into the EDF at the start of each trial.
trial_index = 1

# ---- The calibration "graphics environment" ---------------------------
# genv draws the calibration targets and the camera image in our window.
genv = EyeLinkCoreGraphicsPsychoPy(el_tracker, win, False)
print(genv)   # prints the version of the graphics library
if useRetina:
    genv.fixMacRetinaDisplay()
# Ask pylink to use our PsychoPy window for calibration.
pylink.openGraphicsEx(genv)

# ---- CameraSetup: calibration settings --------------------------------
# Background and target colours, in PsychoPy's -1..+1 colours.
genv.setCalibrationColors((1, 1, 1), win.color)   # white target, grey screen
# The target: a picture (images/fixTarget.bmp). Other choices are
# 'circle', 'movie' and 'spiral'.
genv.setTargetType('picture')
genv.setPictureTarget(os.path.normpath(calTargetFile))
# Beeps for target moves, success and errors: '' = the default sounds,
# 'off' = no sound, or the name of a .wav file.
genv.setCalibrationSounds('', '', '')
# 13-point calibration: needed in Remote Mode.
el_tracker.sendCommand('calibration_type = %s' % calibrationType)
clear_screen()

# ---- CameraSetup: hand control to the experimenter --------------------
# doTrackerSetup() shows the camera image on the stimulus screen and lets
# the experimenter calibrate (C), validate (V) and leave (O) from the
# keyboard. It returns when the experimenter presses O.
# Skipped in dummy mode.
if not dummyMode:
    try:
        el_tracker.doTrackerSetup()
    except RuntimeError as err:
        print('ERROR:', err)
        el_tracker.exitCalibration()
    win.mouseVisible = False
thisExp.nextEntry()


# =====================================================================
# 14. INSTRUCTIONS SCREEN (Builder routine "instruct")
# =====================================================================
# This is the simplest kind of "routine": draw, flip, repeat, until a key
# is pressed. One pass of the "while" loop = one frame.
kb.clearEvents()                   # forget keys pressed before this screen
taskInstructions.setAutoDraw(True)  # draw it on every flip from now on
thisExp.timestampOnFlip(win, 'instruct.started')
while True:
    keys = kb.getKeys(keyList=respKeys + ['space'], waitRelease=False)
    if keys:                       # a list with something in it counts as True
        thisExp.addData('ready.keys', keys[-1].name)
        thisExp.addData('ready.rt', keys[-1].rt)
        break                      # leave the "while" loop
    win.flip()
taskInstructions.setAutoDraw(False)
thisExp.addData('instruct.stopped', globalClock.getTime())

# ---- taskStartMsg ------------------------------------------------------
# Write TASK_START into the EDF, so the start of the task is easy to find
# when you analyse the data.
el_tracker = pylink.getEYELINK()
el_tracker.sendMessage('TASK_START')
thisExp.nextEntry()                # finish this row of the data file


# =====================================================================
# 15. DRIFT CHECK (Builder routine "eyelinkDriftCheck")
# =====================================================================
# One drift check before the trials: the participant looks at a target
# in the centre, and the tracker checks that its estimate of gaze is
# still accurate. The experimenter can press Esc here to go back to
# Camera Setup and recalibrate (then O to return).
genv.setCalibrationColors((1, 1, 1), win.color)
genv.setTargetType('picture')
genv.setPictureTarget(os.path.normpath(calTargetFile))
genv.setCalibrationSounds('', '', '')

# The screen centre in EyeLink coordinates (top-left = 0, 0).
dcX, dcY = int(round(scn_width / 2)), int(round(scn_height / 2))
# Skipped in dummy mode.
while not dummyMode:
    # Quit if the tracker is gone, or the experimenter pressed Ctrl-C.
    if (not el_tracker.isConnected()) or el_tracker.breakPressed():
        terminate_task()
    try:
        # Arguments: x, y, draw the target (1), allow Esc -> setup (1).
        error = el_tracker.doDriftCorrect(dcX, dcY, 1, 1)
        if error is not pylink.ESC_KEY:   # anything but Esc: done
            break
    except Exception:
        pass
win.mouseVisible = False


# =====================================================================
# 16. THE TRIALS LOOP
#     (Builder loop "trials" with routines eyelinkStartRecording, trial,
#      eyelinkStopRecording)
# =====================================================================
# data.importConditions() reads conditions.csv into a list with one entry
# per row: [{'targetSide': 'left', 'targetX': -1, 'corrAns': '7'}, ...]
# TrialHandler2 repeats that list nReps times in random order.
# thisExp.addLoop() makes the condition columns appear in the data file.
trials = data.TrialHandler2(
    trialList=data.importConditions(conditionsFile),
    nReps=nReps, method='random', extraInfo=expInfo, name='trials')
thisExp.addLoop(trials)

# "for thisTrial in trials" runs the indented block once per trial.
# thisTrial holds this trial's row of conditions.csv.
for thisTrial in trials:
    targetSide = thisTrial['targetSide']   # 'left' or 'right'
    targetX = thisTrial['targetX']         # -1 (left) or 1 (right)
    corrAns = str(thisTrial['corrAns'])    # '7' or '2'

    # =================================================================
    # 16a. Before the trial: Host PC drawing and start recording
    #      (Builder: HostDrawing and StartRecord)
    # =================================================================
    el_tracker = pylink.getEYELINK()

    # ---- HostDrawing: landmarks on the Host PC screen ------------------
    # The experimenter sees the participant's gaze on the Host PC, drawn
    # over simple boxes that show where the stimuli are.
    el_tracker.setOfflineMode()
    el_tracker.sendCommand('clear_screen 0')
    # A box around the fixation cross (colour 4 on the Host PC palette).
    (x, y), (w, h) = eyelink_pos_size(fixation)
    el_tracker.sendCommand('draw_box = %i %i %i %i %i' % (
        x - w / 2, y - h / 2, x + w / 2, y + h / 2, 4))
    # Boxes where the left and right targets can appear (colour 2).
    el_tracker.sendCommand('draw_box %d %d %d %d 2' % (
        scn_width / 2.0 - targetEccPix - targetSizePix / 2.0, scn_height / 2.0 - targetSizePix / 2.0,
        scn_width / 2.0 - targetEccPix + targetSizePix / 2.0, scn_height / 2.0 + targetSizePix / 2.0))
    el_tracker.sendCommand('draw_box %d %d %d %d 2' % (
        scn_width / 2.0 + targetEccPix - targetSizePix / 2.0, scn_height / 2.0 - targetSizePix / 2.0,
        scn_width / 2.0 + targetEccPix + targetSizePix / 2.0, scn_height / 2.0 + targetSizePix / 2.0))
    # A status line shown on the Host PC during recording.
    el_tracker.sendCommand("record_status_message '%s'"
                           % ('Trial %d/%d' % (trials.thisN + 1, trials.nTotal)))

    # ---- StartRecord ----------------------------------------------------
    # TRIALID marks the start of a trial for Data Viewer.
    el_tracker.sendMessage('TRIALID %d' % trial_index)
    el_tracker.setOfflineMode()
    # Record samples and events to the EDF, and send both over the link
    # (1 = yes for each of the four).
    try:
        el_tracker.startRecording(1, 1, 1, 1)
    except RuntimeError as error:
        print('ERROR:', error)
        abort_trial()
    # Give the tracker 100 ms to start recording before the trial begins.
    pylink.pumpDelay(100)
    # Which eye is being tracked? 0 = left, 1 = right, 2 = both.
    eye_used = el_tracker.eyeAvailable()
    if eye_used == 1:
        el_tracker.sendMessage('EYE_USED 1 RIGHT')
    elif eye_used == 0 or eye_used == 2:
        el_tracker.sendMessage('EYE_USED 0 LEFT')
        eye_used = 0
    else:
        print('ERROR: Could not get eye information!')

    # =================================================================
    # 16b. Prepare the trial (Builder: "Begin Routine" of the trial)
    # =================================================================
    # ---- trialSetup: the random foreperiod ------------------------------
    # A random wait between the cross and the target, so the participant
    # can't predict when the target will come: 0.8 to 1.5 s.
    foreperiod = np.random.uniform(foreperiodMin, foreperiodMax)
    thisExp.addData('foreperiod', foreperiod)

    # When the target starts, in seconds from the start of the trial.
    targetOnset = fixationOnset + foreperiod

    # Put the target on the correct side: -315 px (left) or +315 px (right).
    target.pos = (targetX * targetEccPix, 0)

    # ---- MarkEvents: trial variables and Data Viewer files --------------
    # "!V TRIAL_VAR name value" lines become trial variables in Data Viewer.
    for i, (name, value) in enumerate([('targetSide', targetSide), ('targetX', targetX),
                                       ('corrAns', corrAns), ('foreperiod', foreperiod)]):
        el_tracker.sendMessage('!V TRIAL_VAR %s %s' % (name, value))
        if i % 5 == 0:
            time.sleep(0.001)    # a short pause so no message is lost
    dv_start_trial(trial_index)
    el_tracker.sendMessage('!V CLEAR %d %d %d' % eyelink_color())

    # Every stimulus starts the trial "not started". We use .status the
    # same way Builder does: NOT_STARTED -> STARTED -> FINISHED.
    fixation.status = NOT_STARTED
    target.status = NOT_STARTED
    respStatus = NOT_STARTED
    respKey = None           # the key pressed, once there is one
    respRT = None            # its reaction time (s from target onset)
    respDuration = None      # how long the key was held (if known)
    trackerLost = False

    kb.clearEvents()

    # Start the trial clock at the moment of the next flip, and note the
    # trial's start time in the data file.
    thisExp.timestampOnFlip(win, 'trial.started')
    win.callOnFlip(trialClock.reset)
    win.flip()

    # =================================================================
    # 16c. Run the trial: one pass of this loop per frame
    # =================================================================
    # On every pass we:
    #   1. ask when the NEXT flip will happen (tThisFlip)
    #   2. switch stimuli on if their time has come, and queue their EDF
    #      messages for that flip
    #   3. read the keyboard
    #   4. check the tracker and Ctrl-C
    #   5. flip
    while True:
        # Time of the coming flip on the trial clock and on the global
        # clock. Comparing THIS time (not "now") with the start times
        # means each stimulus appears on the first frame that is due.
        tThisFlip = win.getFutureFlipTime(clock=trialClock)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)

        # ---- fixation cross: on at fixationOnset, until the trial ends ----
        if fixation.status == NOT_STARTED and tThisFlip >= fixationOnset - frameTolerance:
            fixation.setAutoDraw(True)       # draw it on every flip from now on
            fixation.status = STARTED
            # tStartRefresh = when the cross appears, on the global clock.
            # tThisFlipGlobal is our best guess now; timestampOnFlip and
            # timeOnFlip replace it with the ACTUAL flip time once the
            # flip has happened.
            fixation.tStartRefresh = tThisFlipGlobal
            thisExp.timestampOnFlip(win, 'fixation.started')
            win.timeOnFlip(fixation, 'tStartRefresh')
            # EDF: "<ms> fixation_ONSET", right after that flip.
            win.callOnFlip(mark_onset, fixation, 1)

        # ---- target: on at targetOnset, for respDeadline seconds --------
        respJustStarted = False
        if target.status == NOT_STARTED and tThisFlip >= targetOnset - frameTolerance:
            target.setAutoDraw(True)
            target.status = STARTED
            target.tStartRefresh = tThisFlipGlobal
            thisExp.timestampOnFlip(win, 'target.started')
            win.timeOnFlip(target, 'tStartRefresh')

            # ---- targetOnsetMsg -------------------------------------------
            # TARGET_ONSET_LEFT or TARGET_ONSET_RIGHT, sent straight after
            # the flip that shows the target. .upper() turns 'left' into
            # 'LEFT'. win.callOnFlip(f, x) means "run f(x) after the next
            # flip".
            win.callOnFlip(el_tracker.sendMessage, 'TARGET_ONSET_' + targetSide.upper())
            # EDF: "<ms> target_ONSET" (MarkEvents).
            win.callOnFlip(mark_onset, target, 2)

            # The response window opens on the same flip. At that flip
            # the keyboard clock is reset to 0 (so RTs are measured from
            # target onset) and any earlier key presses are thrown away.
            respStatus = STARTED
            thisExp.timestampOnFlip(win, 'resp.started')
            win.callOnFlip(kb.clock.reset)
            win.callOnFlip(kb.clearEvents, eventType='keyboard')
            respJustStarted = True    # don't read keys until after that flip

        # ---- the response --------------------------------------------
        if respStatus == STARTED and not respJustStarted:
            keys = kb.getKeys(keyList=respKeys, waitRelease=False)
            if keys:
                respKey = keys[0].name         # the first key pressed
                respRT = keys[0].rt            # seconds since target onset
                respDuration = keys[0].duration
                break                          # a response ends the trial

        # ---- the deadline --------------------------------------------
        # If no key was pressed, the trial ends respDeadline seconds after
        # the target actually appeared (target.tStartRefresh).
        if (target.status == STARTED
                and tThisFlipGlobal > target.tStartRefresh + respDeadline - frameTolerance):
            thisExp.addData('target.stopped', tThisFlipGlobal)
            thisExp.addData('resp.stopped', tThisFlipGlobal)
            break

        # ---- is the tracker still recording? -------------------------
        if not dummyMode and not trackerLost and el_tracker.isRecording() != pylink.TRIAL_OK:
            el_tracker.sendMessage('tracker_disconnected')
            abort_trial()
            trackerLost = True

        check_for_ctrl_c()
        win.flip()

    # =================================================================
    # 16d. End of the trial (Builder: "End Routine" of the trial)
    # =================================================================
    fixation.setAutoDraw(False)
    target.setAutoDraw(False)
    fixation.status = FINISHED
    target.status = FINISHED
    thisExp.addData('trial.stopped', globalClock.getTime())

    # ---- trialSetup: what happened on this trial? -----------------------
    if respKey is None:
        timeout = 1          # 1 = no response before the 1.5 s deadline
        respKeyText = 'NA'   # NA = "not available" (nothing was pressed)
        respRTText = 'NA'
        respCorr = 0
    else:
        timeout = 0          # 0 = a button was pressed in time
        respKeyText = respKey               # the button pressed: '7' or '2'
        respRTText = round(respRT, 4)       # reaction time in seconds, timed
                                            # from target onset, to 4 decimals
        respCorr = int(respKey == corrAns)  # 1 = correct button, 0 = wrong one

    # Save the response the way Builder's Keyboard component does
    # (resp.keys, resp.corr, resp.rt), plus the timeout flag.
    thisExp.addData('resp.timeout', timeout)
    thisExp.addData('resp.keys', respKey)
    thisExp.addData('resp.corr', respCorr)
    if respKey is not None:
        thisExp.addData('resp.rt', respRT)
        thisExp.addData('resp.duration', respDuration)

    # One EDF line summarising the trial. In the text below, each %d is
    # replaced by a whole number and each %s by text, in the order listed
    # after the "%" sign. trials.thisN counts trials from 0, so add 1.
    el_tracker.sendMessage('TRIAL_SUMMARY trial=%d side=%s key=%s rt=%s corr=%d timeout=%d'
                           % (trials.thisN + 1, targetSide, respKeyText, respRTText,
                              respCorr, timeout))
    el_tracker.sendMessage('!V TRIAL_VAR timeout %d' % timeout)

    # ---- trialLog: one row for this trial --------------------------------
    rowValues = [
        expInfo['participant'],
        expInfo['session'],
        expInfo['date'],
        sessionIdentifier + '.EDF',           # the eye-tracking file
        trials.thisN + 1,                     # trial number, counting from 1
        trial_index,                          # TRIALID in the EDF
        targetSide,                           # 'left' or 'right'
        targetX * targetEccPix,               # -315 = left, 315 = right
        corrAns,                              # the correct button
        round(foreperiod, 4),                 # waiting time before target (s)
        round(fixation.tStartRefresh, 4),     # when the cross appeared (s)
        round(target.tStartRefresh, 4),       # when the target appeared (s)
        respKeyText,                          # button pressed, or NA
        respRTText,                           # reaction time (s), or NA
        respCorr,                             # 1 = correct, 0 = wrong or none
        timeout,                              # 1 = no response in time
    ]
    # Turn every value into text, put tabs between them, and write the row.
    trialLog.write('\t'.join(str(value) for value in rowValues) + '\n')
    # flush() saves the row to disk straight away, so the log is complete
    # even if the experiment is stopped early with Ctrl-C.
    trialLog.flush()

    # ---- MarkEvents: offsets, response and interest areas ---------------
    dv_end_trial()
    mark_response(target.tStartRefresh, respKey, respRT, respCorr)

    # ---- StopRecord -------------------------------------------------------
    el_tracker.stopRecording()
    el_tracker.sendMessage('TRIAL_RESULT %d' % 0)    # 0 = trial OK
    trial_index = trial_index + 1

    # Finish this trial's row of the data file and start a new one.
    thisExp.nextEntry()


# =====================================================================
# 17. THANK-YOU SCREEN (Builder routine "thanks")
# =====================================================================
# taskEndMsg: TASK_END marks the end of the task in the EDF.
el_tracker = pylink.getEYELINK()
el_tracker.sendMessage('TASK_END')

endScreen.setAutoDraw(True)
thisExp.timestampOnFlip(win, 'endScreen.started')
win.callOnFlip(trialClock.reset)
win.flip()
while trialClock.getTime() < thanksDuration:
    win.flip()
endScreen.setAutoDraw(False)
thisExp.nextEntry()

# Close the EDF, copy it to this computer, save the data and quit.
terminate_task()
