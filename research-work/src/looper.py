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

        # get the key of the song
        self.initial_key = str(self.song.analyze("key")).lower()

        self.length = len(self.original_parts[0])

        self.parts = copy.deepcopy(self.original_parts)

        self.transformation_cache = transformation_cache = TTLCache(maxsize=50, ttl=600)

        self.current_measure_in_parts = [part[0] for part in self.parts]
        self.measure_index = 0

        self.last_measure_beat = 0

        self.current_rhythms = ['ORIGINAL' for i in range(len(self.parts))]
        self.current_keys = [self.initial_key for i in range(len(self.parts))]

    def initialize(self):
        # cache the measures of each individual part
        for i in range(len(self.original_parts)):
            cache_key = self.get_cache_key(i, self.current_keys[i], self.current_rhythms[i])
            self.transformation_cache[cache_key] = copy.deepcopy(self.original_parts[i])

        self.reset()

    def set_tempo(self, tempo):
        self.tempo = m21.tempo.MetronomeMark(number = tempo)

    def reset(self):
        self.current_measure_in_parts = [part[0] for part in self.parts]
        self.measure_index = 0
        self.last_measure_beat = 0

    def step(self, beat):
        self.measure_index = (self.measure_index + 1) % self.length
        self.current_measure_in_parts = [part[self.measure_index] for part in self.parts]
        self.last_measure_beat = beat

    def _transform_key(self, measures, tonic, mode):
        functioning_key = m21.key.Key(tonic, mode)

        # call the transpose_to_new_key function on the analayzed measures
        transposed_measures = transformer.transpose_to_new_key(measures, functioning_key)

        return transposed_measures

    def _transform_rhythm(self, measures, rhythm):

        rhythm_id = self.rhythm_to_string(rhythm)
        # call the fill_ostinato function on the measures
        ostinated_measures =  transformer.fill_ostinato(measures, rhythm)

        # place in cache
        self.transformation_cache[rhythm_id] = ostinated_measures

        # set measures equal to the new measures
        # self.parts = ostinated_measures
        # self.current_measure_in_parts = self.parts[self.measure_index]

        return ostinated_measures

    def transform(self, part_indexes=None, key=None, rhythm=None):
        if part_indexes == None:
            part_indexes = [i for i in range(len(self.parts))]

        return_parts = []
        for i in range(len(self.parts)):

            if i not in part_indexes:
                return_parts.append(self.parts[i])
            else:

                # check both key and rhythms
                if key == None:
                    key = self.current_keys[i]

                if rhythm == None:
                    rhythm = copy.deepcopy(self.current_rhythms[i])

                # generate the cache key for this part
                cache_key = self.get_cache_key(i, key, rhythm)

                # check to see if this combination is already cached
                return_measures = self.transformation_cache.get(cache_key)

                # if not, generate the transformation
                if return_measures == None:
                    rhythm_id = self.rhythm_to_string(rhythm)
                    base_rhythm_measures = self.transformation_cache.get(self.get_cache_key(i, self.initial_key, rhythm_id))

                    if base_rhythm_measures == None:
                        base_rhythm_measures = self._transform_rhythm(self.original_parts[i], rhythm)

                    k = key.split(" ")
                    tonic = k[0]
                    mode = k[1]

                    return_measures = self._transform_key(base_rhythm_measures, tonic, mode)

                    #set current key and current rhythm for this part
                    self.current_keys[i] = key
                    self.current_rhythms[i] = rhythm

                    #cache results
                    self.transformation_cache[cache_key] = return_measures

                return_parts.append(return_measures)

        #set measures equal to the new measures
        self.parts = return_parts

        #get current measure
        self.current_measure_in_parts = [part[self.measure_index] for part in self.parts]

    # def transform_async(self, part_indexes=None, key=None, rhythm=None):
    #     with fut.ThreadPoolExecutor(max_workers=5) as executor:
    #         executor.submit(self.transform, part_indexes, key, rhythm)

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
