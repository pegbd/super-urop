import numpy
import music21 as m21
import random
import numpy as np
import copy

DISTANCE_EXPONENT = 2.0
DISTANCE_CUTOFF = 0.40

class AVGrid:

    """
    A 2D grid with valence on the X-axis and arousal on the Y-axis. Contains a collection
    of objects of type ParemeterPoint, plotted along coordinates.
    """

    def __init__(self):
        super(AVGrid, self).__init__()

        # valence (X-axis) and arousal (Y-axis) bounds
        self.min_valence = -1.0
        self.max_valence = 1.0
        self.min_arousal = -1.0
        self.max_arousal = 1.0

        # all rectangular parameter regions
        self.points = []

        # current region
        self.current_point = None
        self.last_point = None

    def insert(self, value, arousal, valence):

        """
        Slow implementation: if this creates a bottleneck, will optimize
        """

        # shift point within bounds if it doesn't originally fit
        valence = max(valence, self.min_valence)
        valence = min(valence, self.max_valence)
        arousal = max(arousal, self.min_arousal)
        arousal = min(arousal, self.max_arousal)

        # create point
        point = ParameterPoint(value, arousal, valence)
        self.points.append(point)

        # sort the points
        self.points = sorted(self.points, key=lambda p : [p.valence, p.arousal])

    def sample_parameter_point(self, arousal, valence):

        """
        Create a probability distribution of all points based off of distance to inputted point (valence, arousal), and
		then randomly sample a point.
        """

        distances = []
        points_within = []
        distribution = {}

		# calculate distance of all points to point = (arousal, valence)
        for point in self.points:
            distance = point.distance_between(arousal, valence)
            if distance <= DISTANCE_CUTOFF:
                distances.append(distance)
                points_within.append(point)

		# distance manipulation, denominator construction
        furthest = max(distances)
        inverted = [((furthest - distance) ** DISTANCE_EXPONENT) for distance in distances]
        denominator = sum(inverted)

		# create probability dictionary distribution
        for point, invert in zip(points_within, inverted):
            probability = float(invert) / denominator
            distribution[point] = probability

		# randomly sample from distribution
        selected_point = weighted_random(distribution)

		# update last and current pointers
        self.last_point = self.current_point
        self.current_point = selected_point

        return selected_point, distribution

    def get_last_point(self):
        return self.last_point

    def get_points(self):
        return copy.deepcopy(self.points)


class TempoGrid(AVGrid):

    """
    A type of AVGrid whose regions map arousal-valence regions to song tempo
    """

    def __init__(self):
        super(TempoGrid, self).__init__()

        self.min_tempo = 60
        self.max_tempo = 240

    def insert(self, value, arousal, valence):

        # use minimum and maximum tempo bounds
        value = max(value, self.min_tempo)
        value = min(value, self.max_tempo)

        # use ancestor's insert method with new value
        super(TempoGrid, self).insert(value, arousal, valence)

    def parse_point_file(self, filepath):
        # open text file
        f = open(filepath, 'r')

        # read all regions
        for line in f.readlines():
            line = line.strip().split('\t')

            value = int(line[0])
            # print(line[1].split(' '))
            point = [float(i) for i in line[1:]]

            self.insert(value, point[0], point[1])


class InstrumentGrid(AVGrid):

    """
    A type of AVGrid whose regions map arousal-valence regions to a certain orchestrations
    """

    def __init__(self):
        super(InstrumentGrid, self).__init__()

        self.instruments_file_path = './synth_data/synth_patches.txt'
        self.instruments = []

        # open text file
        f = open(self.instruments_file_path, 'r')

        # index all the instruments
        for line in f.readlines():
            line = line.split()
            self.instruments.append(" ".join(line[1:]))

    def insert(self, value, arousal, valence):

        # use minimum and maximum tempo bounds
        value = max(value, 0)
        value = min(value, len(self.instruments) - 1)

        # use ancestor's insert method with new value
        super(InstrumentGrid, self).insert(value, arousal, valence)

    def parse_point_file(self, filepath):
        # open text file
        f = open(filepath, 'r')

        # read all regions
        for line in f.readlines():
            line = line.strip().split('\t')

            value = int(line[0])
            # print(line[1].split(' '))
            point = [float(i) for i in line[1:]]

            self.insert(value, point[0], point[1])


class KeySignatureGrid(AVGrid):

    """
    A type of AVGrid whose regions map arousal-valence regions to the key and mode of a song
    """

    def __init__(self):
        super(KeySignatureGrid, self).__init__()

        self.tonics = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        self.accidentals = ['', '-', '#']
        self.modes = ['major', 'minor']

    def insert(self, value, arousal, valence):

        # verify key signature values
        key = value[0] if value[0] in self.tonics else 'c'
        accidental = value[1] if value[1] in self.accidentals else ''
        mode = value[2] if value[2] in self.modes else 'major'

        value = (key, accidental, mode)

        # use ancestor's insert method with new value
        super(KeySignatureGrid, self).insert(value, arousal, valence)

    def parse_point_file(self, filepath):

		# open text file
        f = open(filepath, 'r')

        # read all regions
        for line in f.readlines():
            line = line.strip().split('\t')

            value = tuple(line[0].split(' '))
            # print(line[1].split(' '))
            point = [float(i) for i in line[1:]]

            self.insert(value, point[0], point[1])


class RhythmGrid(AVGrid):

    """
    A type of AVGrid whose regions map arousal-valence regions to a certain ostinated rhythm
    """

    def __init__(self):
        super(RhythmGrid, self).__init__()

    def insert(self):
        pass

    def parse_point_file(self, filepath):
        pass




############################
##### Point and Region #####
############################

class ParameterRegion:

    """
    A rectangular region where its width corresponds to its valence-range, and its height to its arousal range.
    Any (valence, arousal) tuple value that falls within this region on the AVGrid corresponds to music with the parameter
    set to the regions value.
    """

    def __init__(self, parameter_value, valence_left, valence_right, arousal_bottom, arousal_top):
        super(ParameterRegion, self).__init__()

        # assertions
        assert arousal_bottom <= arousal_top
        assert valence_left <= valence_right

        # value
        self.parameter_value = parameter_value

        # arousal range
        self.arousal_bottom = arousal_bottom
        self.arousal_top = arousal_top

        # valence range
        self.valence_left = valence_left
        self.valence_right = valence_right

    def check_av_point(self, arousal, valence):
        return (valence >= self.valence_left and valence <= self.valence_right) and (arousal >= self.arousal_bottom and arousal <= self.arousal_top)

    def get_value(self):
        return self.parameter_value

class ParameterPoint:

    """
    A single point, with an associated value for a musical parameter, on the AV Grid, whose x-coordinate corresponds to
    the valence, and y-coordinate to its arousal.
    """

    def __init__(self, parameter_value, arousal, valence):
        super(ParameterPoint, self).__init__()

        self.parameter_value = parameter_value
        self.arousal = arousal
        self.valence = valence

    def get_value(self):
        return self.parameter_value

    def distance_between(self, arousal, valence):
        a = self.arousal - arousal
        v = self.valence - valence

        return np.sqrt(a*a + v*v)

    def __hash__(self):
        return hash((self.parameter_value, self.arousal, self.valence))

    def __eq__(self, other):
        return (self.parameter_value, self.arousal, self.valence) == (other.parameter_value, other.arousal, other.valence)

    def __ne__(self, other):
        # Not strictly necessary, but to avoid having both x==y and x!=y
        # True at the same time
        return not(self == other)


#################################
####### HELPER FUNCTIONS ########
#################################

def weighted_random(distribution):
    roll = random.random()
    total = 0
    for k, v in distribution.items():
        total += v
        if roll <= total:
            return k
    assert False, 'unreachable'
