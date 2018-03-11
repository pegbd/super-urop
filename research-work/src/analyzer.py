import music21 as m21
import numpy as np
import sklearn as skl
import sys
from collections import defaultdict
from random import shuffle

PLAYABLE_MODES = ['major', 'minor']
mode_intervals = {}

for mode in PLAYABLE_MODES:

    added_intervals = []
    intervals = [i for i in m21.scale.AbstractDiatonicScale(mode).getIntervals()]

    # add up the intervals
    for i in range(len(intervals)):
        added_intervals.append(m21.interval.add(intervals[:i + 1]))

    mode_intervals[mode] = added_intervals


def analyze(song_file):

    """
    Takes in a song file and parses it into measures of AnalyzedElement objects

    Args:
        song_file (String): the song's file path (currently tested with .xml files)

    Returns:
        measures_of_analyzed_elements (List[List[AnalyzedElement]]): grouped AnalyzedElement objects
        in their measures.
    """

    song = m21.converter.parse(song_file)

    # split into parts
    measures_of_analyzed_elements = analyze_elements_by_measure(song)

    return measures_of_analyzed_elements, song

def generate_rhythmic_frequency_distribution(stream):

    """
    Observes and calculates the probability of observing a note with ql = b based off of the song

    Args:
        stream (m21.stream.Stream) stream of interest

    Returns:
        frequency_dist (defaultdict(float)) distribution dictionary with the frequencies of each beat quarterlength
    """

    frequency_dist = defaultdict(float)
    playable = list(filter(lambda x: is_note_or_chord_or_rest(x), stream.recurse()))

    for el in playable:
        frequency_dist[el.duration.quarterLength] += 1

    for key in frequency_dist.keys():
        frequency_dist[key] = float(frequency_dist[key]) / len(playable)

    return frequency_dist

def generate_rhythmic_transitions_distributions(stream):

    """
    Observes and calculates the conditional probabilities of transitioning to a beat of ql = t+1, given that
    the current beat is ql = t

    Args:
        stream (m21.stream.Stream) stream of interest

    Returns:
        new_dist (defaultdict(float)) distribution dictionary with conditional calculations taken into account
    """

    transition_dist = defaultdict(int)
    playable = list(filter(lambda x: is_note_or_chord_or_rest(x), stream.recurse()))

    for i in range(len(playable) - 1):
        r1 = playable[i].duration.quarterLength
        r2 = playable[i+1].duration.quarterLength

        key = (r1, r2)
        transition_dist[key] += 1

    new_dist = defaultdict(float)
    for key in transition_dist.keys():
        conditional = list(filter(lambda x: x[0] == key[0], transition_dist.keys()))
        denominator = sum([transition_dist[y] for y in conditional])

        print (denominator)

        new_dist[key] = float(transition_dist[key]) / denominator

    return new_dist

def to_stream(measures_of_analyzed_elements):

    """
    Converts a group of measures of AnalyzedElement objects detailing a song, back into a playable stream.
    Args:
        measures (List[List[AnalyzedElement]]) AnalyzedElements grouped in measures

    Returns:
        stream (m21.stream.Stream) playable stream object with the measures
    """

    stream = analyze_element_measures_to_stream(measures_of_analyzed_elements)

    return stream

# Private Internal Methods

def get_note_roman_numeral(element, songKey):

    """
    Return the roman numeral object of the given note relative to
    the given key.

    Args:
        element (music21.note.Note || music21.note.Rest || music21.chord.Chord): The note, rest, or chord of interest.
        key (music21.key.Key): The key signature context.

    Returns:
        roman (music21.roman.RomanNumeral): Roman numeral of the element's degree within the key
                                            signature context
    """

    # a rest has no roman numeral, so return None
    if element.isRest:
        return None

    chordWrapper = element

    if element.isNote:
        # wrap note in a "chord" by itself
        chordWrapper = m21.chord.Chord([element])

    # analyze the element in the song key
    roman = m21.roman.romanNumeralFromChord(chordWrapper, songKey)

    return roman


def analyze_elements_by_measure(song):

    """
    Returns the scale degrees of a list of notes relative to
    the given key, all wrapped within an AnalyzedElement object.

    Args:
        song (m21.stream.Score)

    Returns:
        parts (List[List[List[AnalyzedElement]]]): List of all notes grouped by their
                                                     corresponding measures.
    """

    songKey = song.analyze("key")
    parts = []

    # break the song up into parts
    for part in song.parts:
        measures = part.getElementsByClass(m21.stream.Measure)
        notes_by_measure = []

        #TODO: track last time signature and add to each following measure
        for measure in measures:
            m = measure.number
            t = measure.timeSignature

            # filter out elements != {Note, Chord or Rest}
            playable = list(filter(lambda x: is_note_or_chord_or_rest(x), measure))
            # notes in the measure
            notes = []

            offset = 1
            for el in playable:
                an = AnalyzedElement(songKey, el, m, t, offset)
                notes.append(an)

                offset += el.duration.quarterLength

            # add the measure of notes to the list of measures.
            notes_by_measure.append(notes)

        parts.append(notes_by_measure)

    return parts

def is_note_or_chord_or_rest(element):
    """
    Returns whether the element is a note or a rest object

    Args:
        element (Any) element in question

    Returns:
        (Boolean) whether the element type is of m21 Note or Rest
    """

    note = type(element) is m21.note.Note
    rest = type(element) is m21.note.Rest
    chord = type(element) is m21.chord.Chord

    return note or rest or chord

def analyze_element_measures_to_stream(parts):
    """
    Returns list of analyzed notes grouped by measure converted into a playable
    Stream object

    Args:
        parts (List[List[List[AnalyzedElement]]]) AnalyzedElements grouped in measures, separated by parts

    Returns:
        stream (m21.stream.Stream) playable stream object with the measures
    """
    stream = m21.stream.Stream()

    for part in parts:
        p = m21.stream.Part()

        for measure in part:
            m = m21.stream.Measure()
            m.timeSignature = None

            for note in measure:
                if m.timeSignature is None:
                    m.timeSignature = note.timeSignature

                m.append(note.element)

            p.append(m)

        stream.insert(0, p)

    return stream

def get_semitone_difference_for_new_key(oldMode, newMode, degree):
    """
    Calculates the difference in semitones for the scale degree between the modes.
    For example, returns -1 for scale degree 3 where oldMode = Major and newMode = Minor

    Args:
        oldMode (String)
        newMode (String)
        degree (integer)

    Returns:
        The difference in semitones above the tonic for the scale degree, between the old and new modes
    """
    assert(degree >= 2)
    index = degree - 2

    #add up all the intervals up until the scale degree, to get the interval above the tonic
    oldNoteInt = mode_intervals[oldMode][index]
    newNoteInt = mode_intervals[newMode][index]

    difference = newNoteInt.semitones - oldNoteInt.semitones
    return difference

class AnalyzedElement:
    def __init__(self, key, element, measureNumber=None, timeSignature=None, beatOffset=None):
        self.key = key
        self.element = element
        self.roman = get_note_roman_numeral(self.element, self.key)
        self.measureNumber = measureNumber
        self.timeSignature = timeSignature
        self.beatOffset = beatOffset

        #TODO:
        # weak reference (to parent object)
        # m21.common.wrapWeakRef, unrwapWeakRef
        # parent has strong reference to child, which has weak reference to parent

    def get_notes_midi(self):
        if self.is_rest():
            return []
        elif self.is_note():
            return [self.element.pitch.midi]
        else:
            return [p.midi for p in self.element.pitches]

    def is_note(self):
        """
        returns whether element is a note object or not
        """
        return type(self.element) is m21.note.Note

    def is_rest(self):
        """
        Returns whether element is a rest or not
        """
        return type(self.element) is m21.note.Rest

    def is_chord(self):
        """
        Returns whether element is a rest or not
        """
        return type(self.element) is m21.chord.Chord

    def copy(self, key=None, element=None, measureNumber=None, timeSignature=None, beatOffset=None):
        """
        Returns a copy of the element with specified attributes replaced.
        """
        if key is None:
            key = self.key
        if element is None:
            element = self.element
        if measureNumber is None:
            measureNumber = self.measureNumber
        if timeSignature is None:
            timeSignature = self.timeSignature
        if beatOffset is None:
            beatOffset = self.beatOffset

        return AnalyzedElement(key, element, measureNumber, timeSignature, beatOffset)

    def in_new_key(self, newKey):

        """
        Return a new AnalyzedElement with the same scale degree in
        a different key.

        Major key -> Major key: simple transposition.
        Major key -> Minor key (or vice versa):
            - take into account the difference in scale structure and intervals.

        TODO: account for natural/melodic/harmonic minors
        TODO: Map the new note's pitch relative to self.note's octave

        Args:
            self (AnalyzedElement): this note.
            key (music21.key.Key): The new key signature

        Returns:
            new_note (AnalyzedElement): new note analyzed in a different key.
        """

        #TODO: get interval.Interval(Ko_tonic, Kn_tonic), intv.transpose(no)
        #TODO: Start wrapping transformations within a future, non-blocking

        #return itself if its a rest
        if self.is_rest():
            return self

        # get the interval and transpose the element
        interval = m21.interval.Interval(self.key.tonic, newKey.tonic).name
        newElement = self.element.transpose(interval)

        #TODO: Fix the enharmonic naming of this function!!
        # print (self.element.name)
        # print("before alteration")
        # print(newElement.name)

        if self.is_note():
            scaleDegreeData = self.roman.scaleDegreeWithAlteration

            if (scaleDegreeData[0] >= 2) and (self.key.mode != newKey.mode):
                difference = get_semitone_difference_for_new_key(self.key.mode, newKey.mode, scaleDegreeData[0])

                newElement = newElement.transpose(m21.interval.Interval(difference))
        else:
            # the element is a chord, whose overall roman numeral analysis is self.roman

            # initialize new chord list
            newChord = []

            # create temp stream with key context to get the scale degrees of the chord
            tempStream = m21.stream.Stream()
            tempStream.append(self.key)
            tempStream.append(self.element)

            scaleDegreeData = self.element.scaleDegrees

            # for each annotated scale degree in the chord
            for i in range(len(scaleDegreeData)):
                data = scaleDegreeData[i]
                if (data[0] >= 2) and (self.key.mode != newKey.mode):
                    difference = get_semitone_difference_for_new_key(self.key.mode, newKey.mode, data[0])

                    newChord.append(newElement.pitches[i].transpose(difference))
                else:
                    newChord.append(newElement.pitches[i])

            newElement = m21.chord.Chord(newChord)
            newElement.duration = self.element.duration

        return self.copy(key=newKey, element=newElement)
