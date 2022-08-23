from dataclasses import dataclass
from MIDIAnimator.data_structures import midi
from MIDIAnimator.src.animation import *
from MIDIAnimator.utils import mapRangeArcSin, mapRangeExp, mapRangeLinear, mapRangeRoot, mapRangeSin
from MIDIAnimator.utils.blender import *
from MIDIAnimator.utils import *
from typing import Callable, List, Tuple, Dict, Optional, Union
from MIDIAnimator.data_structures.midi import MIDIFile, MIDINote
from math import radians 
import bpy

@dataclass
class KeyframeValue:
    seconds: float
    value: float


class Laser(Instrument):
    def __init__(self, midiTrack: MIDITrack, collection: bpy.types.Collection, **kwargs):
        super().__init__(midiTrack, collection, override=True)
        self.rotation_low = kwargs["rotation_low"]
        self.rotation_high = kwargs["rotation_high"]
        self.note_low = kwargs["note_low"]
        self.note_high = kwargs["note_high"]
        self.obj = self.collection.all_objects["Circle"]
        self.laser = self.collection.all_objects["Cylinder"]
        self.preAnimate()
    
    def preAnimate(self):
        bpy.context.scene.frame_set(-10000)
        for obj in self.collection.all_objects:
            cleanKeyframes(obj)

    def animate(self):
        # beginning
        self.obj.rotation_euler.y = 0
        self.obj.keyframe_insert(data_path="rotation_euler", index=1, frame=0)
        nextNote = self.midiTrack.notes[1] if 1 < len(self.midiTrack.notes) else None
        if nextNote is not None:
            # set a key on the next note (- 1)
            self.obj.keyframe_insert(data_path="rotation_euler", index=1, frame=secToFrames(nextNote.timeOn - 1))

        # turn laser off
        showHideObj(self.laser, hide=True, frame=0)



        for i, curNote in enumerate(self.midiTrack.notes):
            # FIX THIS
            nextNote = self.midiTrack.notes[i+1] if i+1 < len(self.midiTrack.notes) else MIDINote(channel=0, noteNumber=60, velocity=1, timeOn=1000000, timeOff=1000001)
            animDuration = nextNote.timeOn - curNote.timeOn

            # this mutatess the data.. not a great idea
            if nextNote.timeOn < curNote.timeOff:
                curNote.timeOff = nextNote.timeOn
            
            # set a timeOn key
            self.obj.rotation_euler.y = radians(mapRangeLinear(curNote.noteNumber, self.note_low, self.note_high, self.rotation_low, self.rotation_high))
            self.obj.keyframe_insert(data_path="rotation_euler", index=1, frame=secToFrames(curNote.timeOn))
    

            if animDuration > 1:
                timeDiff = 1
            else:
                timeDiff = 0.1
            
            if animDuration < 4:
                # not a break
                self.obj.rotation_euler.y = radians(mapRangeLinear(curNote.noteNumber, self.note_low, self.note_high, self.rotation_low, self.rotation_high))
                self.obj.keyframe_insert(data_path="rotation_euler", index=1, frame=secToFrames(nextNote.timeOn - timeDiff))
                
                if timeDiff == 1:
                    self.obj.keyframe_insert(data_path="rotation_euler", index=1, frame=secToFrames(curNote.timeOff))
            else:
                # return to 0
                # insert a note off key before its done
                self.obj.keyframe_insert(data_path="rotation_euler", index=1, frame=secToFrames(curNote.timeOff))
                
                # set key after its done (+ 1)
                self.obj.rotation_euler.y = 0
                self.obj.keyframe_insert(data_path="rotation_euler", index=1, frame=secToFrames(curNote.timeOff + 1))
                
                # set a key on the next note (- 1)
                self.obj.keyframe_insert(data_path="rotation_euler", index=1, frame=secToFrames(nextNote.timeOn - 1))


            showHideObj(self.laser, hide=False, frame=secToFrames(curNote.timeOn))
            showHideObj(self.laser, hide=True, frame=secToFrames(curNote.timeOff))



file = MIDIFile("/Users/james/github/MIDIFiles/testMidi/future_retro_laser.mid")
# file = MIDIFile("/Users/james/github/MIDIFiles/testMidi/AnimDraft3.mid")

tracks = file.getMIDITracks()
laserTrack = tracks[0]
# laserTrack = file.findTrack("Laser")

settings = {
    "rotation_low": -35,
    "rotation_high": 52,
    "note_low": min([note.noteNumber for note in laserTrack.notes]),
    "note_high": max([note.noteNumber for note in laserTrack.notes])
}

animator = MIDIAnimatorNode()
animator.addInstrument(midiTrack=laserTrack, objectCollection=bpy.data.collections['Laser'], custom=Laser, customVars=settings)
animator.animate()