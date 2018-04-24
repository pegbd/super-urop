import pygame, sys
import music21 as m21
import pygame.locals
from io import BytesIO
import shutil
from cachetools import TTLCache
import time
import analyzer
import transformer
import copy
import modulation
# import concurrent.futures as fut

converter = m21.converter

# entire stream.Score of the song
song = converter.parse('../scores/bare-necessities.xml')

#TODO: When loading in the song, get all of the information from the stream and load them in.
class SongLooper:
    def __init__(self, song_file, tempo):
        super(SongLooper, self).__init__()

        self.song_file = song_file

        self.tempo = m21.tempo.MetronomeMark(number = tempo)
        self.original_parts, self.song = analyzer.analyze(song_file)
        self.time_signature = self.original_parts[0][0][0].timeSignature

        # get the key of the song
        self.initial_key = str(self.song.analyze("key")).lower()

        self.length = len(self.original_parts[0])

        self.parts = copy.deepcopy(self.original_parts)

        self.transformation_cache = transformation_cache = TTLCache(maxsize=50, ttl=600)

        # Keep track of the current measure of music, and index, for all the parts
        self.current_measure_in_parts = [part[0] for part in self.parts]
        self.measure_index = 0

        self.last_measure_beat = 0

        # Keep track of current rhythms and key for each individual part
        self.current_rhythms = ['ORIGINAL' for i in range(len(self.parts))]
        self.current_key = self.initial_key

        # all the logic for modulating the music
        self.modulating = False
        self.key_modulator = modulation.KeyModulator()
        self.modulation_progression = None
        self.modulation_progression_index = 0
        self.modulation_complete = True

        self.target_rhythm = None

        # temporary

    def initialize(self):
        # cache the measures of each individual part
        for i in range(len(self.original_parts)):
            cache_key = self.get_cache_key(i, self.current_key, self.current_rhythms[i])
            self.transformation_cache[cache_key] = copy.deepcopy(self.original_parts[i])

        self.reset()

    def set_tempo(self, tempo):
        self.tempo = m21.tempo.MetronomeMark(number = tempo)

    def reset(self):
        self.current_measure_in_parts = [part[0] for part in self.parts]
        self.measure_index = 0

    def step(self, beat):
        if not self.modulating:
            print("not modulating at all")
            self.measure_index = (self.measure_index + 1) % self.length
            self.current_measure_in_parts = [part[self.measure_index] for part in self.parts]

        else:
            if self.modulation_progression:
                self.modulation_progression_index = (self.modulation_progression_index + 1) % len(self.modulation_progression)

                # check to see if modulation has completed at least once
                if self.modulation_progression_index == len(self.modulation_progression) - 1:
                    self.modulation_complete = True

                self.current_measure_in_parts = [self.modulation_progression[self.modulation_progression_index]]

        self.last_measure_beat = beat

    def _transform_key(self, measures, tonic, mode):
        functioning_key = m21.key.Key(tonic, mode)

        # call the transpose_to_new_key function on the analayzed measures
        transposed_measures = transformer.transpose_to_new_key(measures, functioning_key)

        return transposed_measures

    def _transform_rhythm(self, measures, rhythm):

        rhythm_id = self.rhythm_to_string(rhythm)

        # call the fill_ostinato function on the measures
        ostinated_measures = transformer.fill_ostinato(measures, rhythm)

        # place in cache
        self.transformation_cache[rhythm_id] = ostinated_measures

        # set measures equal to the new measures
        # self.parts = ostinated_measures
        # self.current_measure_in_parts = self.parts[self.measure_index]

        return ostinated_measures

    def transform(self, part_indexes=None, key=None, rhythm=None):

        key_change = False
        rhythm_change = False

        # check both key and rhythms changing
        if key is not None:

            # separate tonic and mode from keys
            k = self.current_key.split(' ')
            nk = key.split(' ')

            # set the modulation progression from old key to new key
            self.set_modulation_progression((k[0], k[1]), (nk[0], nk[1]), rhythm)

            # indicating that we're modulating and that it is not yet complete
            self.modulating = True
            self.modulation_complete = False
            self.modulation_progression_index = 0

            key_change = True

        if rhythm is not None:
            rhythm_change = True

        if part_indexes is None:
            part_indexes = [i for i in range(len(self.parts))]

        ## ITERATION STEP ##
        return_parts = []
        for i in range(len(self.parts)):

            if i not in part_indexes:
                return_parts.append(self.parts[i])
            else:

                # check both key and rhythms
                if key == None:
                    key = self.current_key

                if rhythm == None:
                    rhythm = copy.deepcopy(self.current_rhythms[i])

                # generate the cache key for this part
                cache_key = self.get_cache_key(i, key, rhythm)

                # check to see if this combination is already cached
                return_measures = self.transformation_cache.get(cache_key)

                # if not, generate the transformation
                if return_measures == None:
                    if rhythm_change and key_change:
                        rhythm_id = self.rhythm_to_string(rhythm)
                        base_rhythm_measures = self.transformation_cache.get(self.get_cache_key(i, self.initial_key, rhythm_id))

                        if base_rhythm_measures == None:
                            base_rhythm_measures = self._transform_rhythm(self.original_parts[i], rhythm)

                        k = key.split(" ")
                        tonic = k[0]
                        mode = k[1]

                        return_measures = self._transform_key(base_rhythm_measures, tonic, mode)

                        #set current key and current rhythm for this part
                        self.current_key = key # TODO: Currently setting key multiple times
                        self.current_rhythms[i] = rhythm

                    elif rhythm_change and not key_change:
                        return_measures = self._transform_rhythm(self.parts[i], rhythm)
                    elif key_change and not rhythm_change:
                        return_measures = self._transform_key(self.parts[i], tonic, mode)

                    #cache results
                    print(len(return_measures))
                    self.transformation_cache[cache_key] = return_measures

                return_parts.append(return_measures)

        # wait for the full modulation to complete:
        while not self.modulation_complete:
            pass

        #set measures equal to the new measures
        self.parts = return_parts
        self.modulating = False

        #get current measure
        self.current_measure_in_parts = [part[self.measure_index] for part in self.parts]

        # TODO: Decide if we want to reset to the beginning of the song after each key change
        self.reset()

    def get_current_measure(self):
        return self.current_measure_in_parts

    def get_all_parts(self):
        return self.parts

    def get_measure_index(self):
        return self.get_measure_index

    def get_last_measure_beat(self):
        return self.last_measure_beat

    def rhythm_to_string(self, rhythm):
        return "".join([str(beat) for beat in rhythm])

    def get_cache_key(self, part, key, rhythm):
        return "part " + str(part) + ": " + key + " " + self.rhythm_to_string(rhythm)

    def set_modulation_progression(self, start_key, end_key, rhythm=None):
        progression = self.key_modulator.find_chord_path(start_key, end_key)
        progression_measures = self.key_modulator.get_modulation_measures(self.time_signature.numerator, progression)
        self.modulation_progression = progression_measures[-2:]
        self.modulation_progression_index = 0
        if rhythm:
            self.modulation_progression = transformer.fill_ostinato(progression_measures, rhythm)
