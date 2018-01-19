import numpy
import music21 as m21
import random

class AVGrid:

    """
    A 2D grid with valence on the X-axis and arousal on the Y-axis. Contains a collection
    of objects of type ParemeterRegion, plotted along coordinates.
    """

    def __init__(self):
        super(AVGrid, self).__init__()

        # valence (X-axis) and arousal (Y-axis) bounds
        self.min_valence = -1.0
        self.max_valence = 1.0
        self.min_arousal = -1.0
        self.max_arousal = 1.0

        # all rectangular parameter regions
        self.regions = []

        # current region
        self.last_region = None

    def insert(self, value, valence_left, valence_right, arousal_bottom, arousal_top):

        """
        Slow implementation: if this creates a bottleneck, will optimize
        """

        # crop the region if it doesn't fit within the grid bounds
        valence_left = max(valence_left, self.min_valence)
        valence_right = min(valence_right, self.max_valence)
        arousal_bottom = max(arousal_bottom, self.min_arousal)
        arousal_top = min(arousal_top, self.max_arousal)

        # create region
        region = ParameterRegion(value, valence_left, valence_right, arousal_bottom, arousal_top)
        self.regions.append(region)

        # sort the regions
        self.regions = sorted(self.regions, key=lambda r : [r.valence_left, r.arousal_bottom])

    def get_region(self, arousal, valence):

        """
        Find the region within the AVgrid that contains the point (arousal, valence), and return
        its parameter value.
        """

        selected_regions = [region for region in self.regions if region.check_av_point(arousal, valence)]

        if selected_regions:
            selected = random.choice(selected_regions)
            self.last_region = selected
            return selected

        return None

    def get_last_region(self):
        return self.last_region


class TempoGrid(AVGrid):

    """
    A type of AVGrid whose regions map arousal-valence regions to song tempo
    """

    def __init__(self):
        super(TempoGrid, self).__init__()

        self.min_tempo = 60
        self.max_tempo = 240

    def insert(self, value, valence_left, valence_right, arousal_bottom, arousal_top):

        # use minimum and maximum tempo bounds
        value = max(value, self.min_tempo)
        value = min(value, self.max_tempo)

        # use ancestor's insert method with new value
        super(TempoGrid, self).insert(value, valence_left, valence_right, arousal_bottom, arousal_top)

    def parse_region_file(self, filepath):
        pass


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

    def insert(self, value, valence_left, valence_right, arousal_bottom, arousal_top):

        # use minimum and maximum tempo bounds
        value = max(value, 0)
        value = min(value, len(self.instruments) - 1)

        # use ancestor's insert method with new value
        super(InstrumentGrid, self).insert(value, valence_left, valence_right, arousal_bottom, arousal_top)

    def parse_region_file(self, filepath):
        pass


class KeySignatureGrid(AVGrid):

    """
    A type of AVGrid whose regions map arousal-valence regions to the key and mode of a song
    """

    def __init__(self):
        super(KeySignatureGrid, self).__init__()

        self.tonics = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        self.accidentals = ['', '-', '#']
        self.modes = ['major', 'minor']

    def insert(self, value, valence_left, valence_right, arousal_bottom, arousal_top):

        # verify key signature values
        key = value[0] if value[0] in self.tonics else 'c'
        accidental = value[1] if value[1] in self.accidentals else ''
        mode = value[2] if value[2] in self.modes else 'major'

        value = (key, accidental, mode)

        # use ancestor's insert method with new value
        super(KeySignatureGrid, self).insert(value, valence_left, valence_right, arousal_bottom, arousal_top)

    def parse_region_file(self, filepath):

		# open text file
        f = open(filepath, 'r')

        # read all regions
        for line in f.readlines():
            line = line.strip().split('\t')

            value = tuple(line[0].split(' '))
            print(line[1].split(' '))
            region = [float(i) for i in line[1].split(' ')]

            self.insert(value, region[0], region[1], region[2], region[3])


class RhythmGrid(AVGrid):

    """
    A type of AVGrid whose regions map arousal-valence regions to a certain ostinated rhythm
    """

    def __init__(self):
        super(RhythmGrid, self).__init__()

    def insert(self):
        pass

    def parse_region_file(self, filepath):
        pass

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
        return (valence >= valence_left and valence <= valence_right) and (arousal >= arousal_bottom and arousal <= arousal_top)

    def get_value(self):
        return self.parameter_value
