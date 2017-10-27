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

converter = m21.converter

# entire stream.Score of the song
song = converter.parse('../scores/bare-necessities.xml')

C_MAJOR = 'c major'

#TODO: When loading in the song, get all of the information from the stream and load them in.
class SongLooper:
    def __init__(self, song_file, tempo):
        super(SongLooper, self).__init__()

        self.song_file = song_file

        self.tempo = m21.tempo.MetronomeMark(number = tempo)
        self.original_measures, self.song = analyzer.analyze(song_file, self.tempo)

        self.measures = copy.deepcopy(self.original_measures)

        self.transformation_cache = transformation_cache = TTLCache(maxsize=50, ttl=600)

        self.current_measure = self.measures[0]
        self.measure_index = 0

        self.last_measure_beat = 0

        self.current_rhythm = 'ORIGINAL'
        self.current_key = 'c major'

    def initialize(self):
        cache_key = self.get_cache_key(self.current_key, self.current_rhythm)
        self.transformation_cache[cache_key] = copy.deepcopy(self.original_measures)
        self.reset()

    def set_tempo(self, tempo):
        self.tempo = m21.tempo.MetronomeMark(number = tempo)

    def reset(self):
        self.current_measure = self.measures[0]
        self.measure_index = 0
        self.last_measure_beat = 0

    def step(self, beat):
        self.measure_index = (self.measure_index + 1) % len(self.measures)
        self.current_measure = self.measures[self.measure_index]
        self.last_measure_beat = beat

    def _transform_key(self, measures, tonic, mode):
        functioning_key = m21.key.Key(tonic, mode)

        # call the transpose_to_new_key function on the analayzed measures
        transposed_measures = transformer.transpose_to_new_key(measures, functioning_key)

        return transposed_measures

    def _transform_rhythm(self, measures, rhythm):

        rhythm_id = self.rhythm_to_string(rhythm)
        print(rhythm_id)
        # call the fill_ostinato function on the measures
        ostinated_measures =  transformer.fill_ostinato(measures, rhythm)

        # place in cache
        self.transformation_cache[rhythm_id] = ostinated_measures

        # set measures equal to the new measures
        # self.measures = ostinated_measures
        # self.current_measure = self.measures[self.measure_index]

        return ostinated_measures

    def transform(self, key=None, rhythm=None):

        if key == None:
            key = self.current_key

        if rhythm == None:
            rhythm = copy.deepcopy(self.current_rhythm)

        cache_key = self.get_cache_key(key, rhythm)


        return_measures = self.transformation_cache.get(cache_key)

        if return_measures == None:
            print('cache miss!')
            rhythm_id = self.rhythm_to_string(rhythm)
            base_rhythm_measures = self.transformation_cache.get(self.get_cache_key(C_MAJOR, rhythm_id))

            if base_rhythm_measures == None:
                base_rhythm_measures = self._transform_rhythm(self.original_measures, rhythm)

            k = key.split(" ")
            tonic = k[0]
            mode = k[1]

            return_measures = self._transform_key(base_rhythm_measures, tonic, mode)
        else:
            print("cache hit!")

        #set measures equal to the new measures
        self.measures = return_measures

        #get current measure
        self.current_measure = self.measures[self.measure_index]

        #set current key and current rhythm
        self.current_key = key
        self.current_rhythm = rhythm

        #cache results
        self.transformation_cache[cache_key] = return_measures

    def get_current_measure(self):
        return self.current_measure

    def get_all_measures(self):
        return self.measures

    def get_measure_index(self):
        return self.get_measure_index

    def get_last_measure_beat(self):
        return self.last_measure_beat

    def rhythm_to_string(self, rhythm):
        return "".join([str(beat) for beat in rhythm])

    def get_cache_key(self, key, rhythm):
        return key + " " + self.rhythm_to_string(rhythm)
