import sys
sys.path.append('..')
from common.core import *
from common.audio import *
from common.synth import *
from common.gfxutil import *
from common.clock import *
from common.metro import *
import music21 as m21
import analyzer
import transformer
import looper
import av_grid
import concurrent.futures as fut

#TODO A sequence of Rhythmic transformation that will increase tension
#TODO Start with 2D Emotion mapping between valence and arousal, such that you map numerical values to emotions, start mapping different musical concepts to arousal/valence
#TODO think about video game -> valence/arousal -> music transformation

#TODO supermario hard-coded demo
#TODO manipulating of the order of the measures, repeats, increase tension

class MainWidget(BaseWidget) :
    def __init__(self):
        super(MainWidget, self).__init__()

        self.audio = Audio(2) # set up audio
        self.song_path = '../scores/cowboy-overture.xml' # set song path

        # create TempoMap, AudioScheduler
        self.tempo = 120 #TODO: grab tempo from file
        self.tempo_map  = SimpleTempoMap(self.tempo)
        self.sched = AudioScheduler(self.tempo_map)

        # Add a looper
        self.looper = looper.SongLooper(self.song_path, self.tempo)
        self.looper.initialize()

        # Set up FluidSynth
        self.synth = Synth('./synth_data/FluidR3_GM.sf2')

        # set up a midi channel for each part
        for i in range(len(self.looper.parts)):
            self.synth.program(i, 0, 0)

        # connect scheduler into audio system
        self.audio.set_generator(self.sched)
        self.sched.set_generator(self.synth)

        # and text to display our status
        self.label = topleft_label()
        self.add_widget(self.label)

        # as the loop continues, these values will be updated to the current transformation
        key_info = self.looper.initial_key.split(" ")
        self.note_letter = key_info[0][0]
        self.accidental_letter = key_info[0][1] if len(key_info[0]) == 2 else ''
        self.mode = key_info[1]

        # concurrent processing of transformations
        self.executor = fut.ThreadPoolExecutor(max_workers=10)

    def on_cmd(self,tick, pitch, channel):
        self.synth.noteon(channel, pitch, 100)

    def off_cmd(self,tick, pitch, channel):
        self.synth.noteoff(channel, pitch)

    def on_update(self) :
        self.audio.on_update()

        # current time
        now_beat = self.sched.get_current_beat()
        now_tick = self.sched.get_tick()

        #time of last measure
        previous_beat = self.looper.get_last_measure_beat()

        # take the difference, and see if it falls within the buffer-zone
        diff = now_beat - previous_beat
        mb = 4

        if (diff == mb):
            # next step in the loop
            self.looper.step(now_beat)

            # schedule each element that appears within the measure
            for i in range(len(self.looper.current_measure_in_parts)):
                part = self.looper.current_measure_in_parts[i]
                for j in range(len(part)):

                    #retrieve the specific element in the measure
                    element = part[j]
                    dur = element.element.duration.quarterLength
                    # ge millisecond timestamps that the element will be scheduled on
                    on_tick = now_tick + element.beatOffset*kTicksPerQuarter
                    off_tick = on_tick + kTicksPerQuarter*dur

                    # if the element is a note
                    if element.is_note():
                        pitch = element.element.pitch.midi

                        # schedule note on
                        self.sched.post_at_tick(on_tick, self.on_cmd, pitch, i)

                        # schedule note off
                        self.sched.post_at_tick(off_tick, self.off_cmd, pitch, i)

                    # else if the element is a chord
                    elif element.is_chord():
                        pitches = [pitch.midi for pitch in list(element.element.pitches)]

                        # schedule off and on events for each pitch in the chord
                        for pitch in pitches:
                            self.sched.post_at_tick(on_tick, self.on_cmd, pitch, i)
                            self.sched.post_at_tick(off_tick, self.off_cmd, pitch, i)


        self.label.text = self.sched.now_str() + '\n'
        self.label.text += 'key = ' + self.note_letter + self.accidental_letter + ' ' + self.mode + '\n'
        self.label.text += 'tempo = ' + str(self.tempo) + '\n'

class TransformationWidget(MainWidget):
    def __init__(self):
        super(TransformationWidget, self).__init__()

    #### TEMPO ###
    def tempoChanged(self):
        cur_time = self.tempo_map.tick_to_time(self.sched.get_tick())
        self.tempo_map.set_tempo(self.tempo, cur_time)
        self.looper.set_tempo(self.tempo)

    def tempoUp(self):
        self.tempo += 8
        self.tempoChanged()

    def tempoDown(self):
        self.tempo -= 8
        self.tempoChanged()

    def setTempo(self, tempo):
        self.tempo = tempo
        self.tempoChanged()

    #TODO: Add controls for all transformations (instrument, rhythm, etc)

    #### Key and Mode ####
    def keyChanged(self):
        new_key = self.note_letter + self.accidental_letter + ' ' + self.mode
        self.executor.submit(self.looper.transform, None, new_key, None)

    def checkKeyChange(self, note, accidental, mode):

        # if this results in a key change, then calculate the new transformation
        if not (self.note_letter == note and self.accidental_letter == accidental and self.mode == mode):
            self.note_letter = note
            self.accidental_letter = accidental
            self.mode = mode

            self.keyChanged()

    def switchInstruments(self, patch):
        for i in range(len(self.looper.parts)):
            self.synth.program(i, 0, patch)


class KeyboardWidget(TransformationWidget):
    """
    Control the music transformer via various keyboard inputs.
    """
    def __init__(self):
        super(KeyboardWidget, self).__init__()

        # Rhythm editting mechanism
        self.held_r = False # Keep track of whether R is being held down
        self.r_log = [] # Log of all numbers pressed
        self.rhythm = [] # Rhythm recorded

        # instrument edditing mechanism
        self.held_s = False
        self.s_log = []

        #parts control
        self.num_parts = len(self.looper.parts)
        self.current_part_index = 0

    def on_key_down(self, keycode, modifiers):

        note = self.note_letter
        accidental = self.accidental_letter
        mode = self.mode

        if keycode[1] in 'abcdefg':
            note = keycode[1]
        elif keycode[1] in '123456789':
            if self.held_r:
                self.r_log.append(int(keycode[1]))
            elif self.held_s:
                self.s_log.append(keycode[1])

        elif keycode[1] == 'r':
            self.held_r = True
            self.r_log = []

        elif keycode[1] == 's':
            self.held_s = True
            self.s_log = []

        elif keycode[1] == 'i':
            accidental = '#'
        elif keycode[1] == 'p':
            accidental = '-'
        elif keycode[1] == 'o':
            accidental = ''
        elif keycode[1] == '-':
            mode = 'major'
        elif keycode[1] == '=':
            mode = 'minor'
        elif keycode[1] == 'right':
            self.tempoUp()
        elif keycode[1] == 'left':
            self.tempo -= 8
            self.tempoChanged()
        elif keycode[1] == 'up':
            self.current_part_index = (self.current_part_index + 1) % self.num_parts
            self.r_log = []
            self.rhythm = []
        elif keycode[1] == 'down':
            self.current_part_index = (self.current_part_index - 1) % self.num_parts
            self.r_log = []
            self.rhythm = []

        self.checkKeyChange(note, accidental, mode)

    def on_key_up(self, keycode):
        if keycode[1] == 'r':
            self.held_r = False
            if len(self.r_log) >= 4:
                self.rhythm = self.r_log[-4:]
                self.executor.submit(self.looper.transform, [self.current_part_index], None, self.rhythm)
        elif keycode[1] == 's':
            self.held_s = False
            if len(self.s_log) == 1:
                self.synth.program(self.current_part_index, 0, int(self.s_log[0]))
            elif len(self.s_log) >= 2:
                self.synth.program(self.current_part_index, 0, int("".join(self.s_log[-2:])))

    def on_update(self):
        self.label.text += 'rhythm = ' + str(self.r_log[-4:]) + '\n'
        self.label.text += 'patch = ' + "".join(self.s_log[-2:]) + '\n'
        self.label.text += 'selected part = ' + str(self.current_part_index + 1) + '\n'


        super(KeyboardWidget, self).on_update()

class ArousalValenceWidget(TransformationWidget):
    """
    Control the music transformer via tuples of Arousal and Valence values that correspond
    to different values of musical attributes (Rhythm, Tempo, Instrument, etc).
    """
    def __init__(self):
        super(ArousalValenceWidget, self).__init__()

        self.arousal = 0
        self.valence = 0
        self.file = open('./data/av.txt', 'r')

        self.tempo_grid = av_grid.TempoGrid()
        self.tempo_grid.parse_region_file('./av-grid-regions/tempo.txt')

        self.rhythm_grid = av_grid.RhythmGrid()
        # self.rhythm_grid.parse_region_file('./av-grid-regions/rhythm.txt')

        self.instrument_grid = av_grid.InstrumentGrid()
        self.instrument_grid.parse_region_file('./av-grid-regions/instruments.txt')

        self.key_grid = av_grid.KeySignatureGrid()
        self.key_grid.parse_region_file('./av-grid-regions/key.txt')

    def transform_arousal_valence(self, arousal, valence):

        print(arousal)
        print(valence)

        # tempo
        tempo_region = self.tempo_grid.get_region(arousal, valence)
        if tempo_region:
            if tempo_region != self.tempo_grid.get_last_region():
                self.setTempo(tempo_region.get_value())

        # rhythm
        rhythm_region = self.rhythm_grid.get_region(arousal, valence)

        # instrument
        instrument_region = self.instrument_grid.get_region(arousal, valence)
        if instrument_region:
            if instrument_region != self.instrument_grid.get_last_region():
                self.switchInstruments(instrument_region.get_value())

        # key
        key_region = self.key_grid.get_region(arousal, valence)
        if key_region:
            if key_region != self.key_grid.get_last_region():

                key_tuple = key_region.get_value()
                self.checkKeyChange(key_tuple[0], key_tuple[1], key_tuple[2])

    def on_update(self):
        where = self.file.tell()
        line = self.file.readline()
        if not line:
            self.file.seek(where)
        else:
            values = line.split(' ')
            self.arousal = float(values[0])
            self.valence = float(values[1])

            self.transform_arousal_valence(self.arousal, self.valence)


        super(ArousalValenceWidget, self).on_update()




run(eval('ArousalValenceWidget'))
