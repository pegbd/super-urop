import music21 as m21
import numpy as np
import sklearn as skl
import sys
from collections import defaultdict
from random import shuffle

def analyze(song_file, tempo):

    """
    Takes in a song file and parses it into measures of AnalyzedNote objects

    Args:
        song_file (String): the song's file path (currently tested with .xml files)
        tempo: the desired tempo for this song to be analyzed at

    Returns:
        measures_of_analyzed_notes (List[List[AnalyzedNote]]): grouped AnalyzedNote objects
        in their measures.
    """

    song = m21.converter.parse(song_file)
    measures_of_analyzed_notes = analyze_notes_by_measure(song)

    return measures_of_analyzed_notes, song

def total_duration_at_tempo(song, tempo):
    #TODO: Doc
    song.insert(0, tempo)
    return song.seconds * 1000

def to_stream(measures_of_analyzed_notes):

    """
    Converts a group of measures of AnalyzedNote objects detailing a song, back into a playable stream.
    Args:
        measures (List[List[AnalyzedNote]]) AnalyzedNotes grouped in measures

    Returns:
        stream (m21.stream.Stream) playable stream object with the measures
    """

    stream = analyze_note_measures_to_stream(measures_of_analyzed_notes)

    return stream

# Private Internal Methods

def get_note_roman_numeral(note, songKey):

    """
    Return the roman numeral object of the given note relative to
    the given key.

    Args:
        note (music21.note.Note || music21.note.Rest): The note of interest. Or a rest.
        key (music21.key.Key): The key signature context.

    Returns:
        roman (music21.roman.RomanNumeral): Roman numeral of the note's degree within the key
                                            signature context
    """

    if note.isNote:
        # wrap note in a "chord" by itself
        noteInChordWrapper = m21.chord.Chord([note])

        # analyze the note in the song key
        roman = m21.roman.romanNumeralFromChord(noteInChordWrapper, songKey)

        return roman

    return None


def analyze_notes_by_measure(song):

    """
    Returns the scale degrees of a list of notes relative to
    the given key, all wrapped within an AnalyzedNote object.

    Args:
        notes (List[music21.note.Note]): Sequence of notes.
        key (music21.key.Key): The key signature context.

    Returns:
        notes_by_measure (List[List[AnalyzedNote]]): List of all notes grouped by their
                                                     corresponding measures.
    """

    songKey = song.analyze("key")

    # song broken up into measures
    measures = song.parts[0].getElementsByClass(m21.stream.Measure)
    notes_by_measure = []

    for measure in measures:

        m = measure.number
        t = measure.timeSignature

        # filter out elements != {Note or Rest}
        playable = list(filter(lambda x: is_note_or_rest(x), measure))

        # notes in the measure
        notes = []

        offset = 1
        for el in playable:
            roman = get_note_roman_numeral(el, songKey)
            an = AnalyzedNote(songKey, el, roman, m, t, offset)
            notes.append(an)

            offset += el.duration.quarterLength

        # add the measure of notes to the list of measures.
        notes_by_measure.append(notes)

    return notes_by_measure

def is_note_or_rest(element):
    """
    Returns whether the element is a note or a rest object

    Args:
        element (Any) element in question

    Returns:
        (Boolean) whether the element type is of m21 Note or Rest
    """

    note = type(element) == m21.note.Note
    rest = type(element) == m21.note.Rest

    return note or rest

def analyze_note_measures_to_stream(measures):
    """
    Returns list of analyzed notes grouped by measure converted into a playable
    Stream object

    Args:
        measures (List[List[AnalyzedNote]]) AnalyzedNotes grouped in measures

    Returns:
        stream (m21.stream.Stream) playable stream object with the measures
    """
    stream = m21.stream.Stream()
    for measure in measures:
        m = m21.stream.Measure()
        m.timeSignature = measure[0].timeSignature

        for note in measure:
            m.append(note.note)

        stream.append(m)

    return stream

class AnalyzedNote:
    def __init__(self, key, note, roman, measureNumber, timeSignature, beatOffset):
        self.key = key
        self.note = note
        self.roman = roman
        self.measureNumber = measureNumber
        self.timeSignature = timeSignature
        self.beatOffset = beatOffset

        #TODO:
        # note offset for position in measure
        # weak reference (to parent object)
        # m21.common.wrapWeakRef, unrwapWeakRef

        # parent has strong reference to child, which has weak reference to parent

    def is_note(self):
        """
        returns whether note is a note object or not
        """
        return self.note.isNote

    def is_rest(self):
        """
        Returns whether note is a rest or not
        """
        return self.note.isRest

    def copy(self, key=None, note=None, roman=None, measureNumber=None, timeSignature=None, beatOffset=None):
        """
        Returns a copy of the note, with specified attributes replaced.
        """
        if key is None:
            key = self.key
        if note is None:
            note = self.key
        if roman is None:
            roman = self.roman
        if measureNumber is None:
            measureNumber = self.measureNumber
        if timeSignature is None:
            timeSignature = self.timeSignature
        if beatOffset is None:
            beatOffset = self.beatOffset

        return AnalyzedNote(key, note, roman, measureNumber, timeSignature, beatOffset)

    def in_new_key(self, newKey):

        """
        Return a new AnalyzedNote with the same scale degree in
        a different key.

        Major key -> Major key: simple transposition.
        Major key -> Minor key (or vice versa):
            - take into account the difference in scale structure and intervals.

        TODO: account for natural/melodic/harmonic minors
        TODO: Map the new note's pitch relative to self.note's octave

        Args:
            self (AnalyzedNote): this note.
            key (music21.key.Key): The new key signature

        Returns:
            new_note (AnalyzedNote): new note analyzed in a different key.
        """

        #TODO: get interval.Interval(Ko_tonic, Kn_tonic), intv.transpose(no)
        #TODO: Start wrapping transformations within a future, non-blocking

        #return itself if its a rest and not a note.
        if self.is_rest():
            return self

        edges = ['b-', 'b', 'b#']
        keyName = newKey.tonic.name.lower()

        threshold = 11

        if keyName in edges:
            threshold += edges.index(keyName) + 1

        # get the scale degree from the roman numeral object, with the accidental
        scaleDegree = self.roman.scaleDegreeWithAlteration
        degree = scaleDegree[0]
        alteration = scaleDegree[1]


        newKeyMode = newKey.mode
        # compute the scale of the new key
        newKeyScale = newKey.getScale(newKeyMode)

        # find the corresponding pitch in the new scale using the degree
        newPitch = newKeyScale.pitchesFromScaleDegrees([degree])[0]

        difference = newPitch.midi - self.note.midi

        if difference >= threshold:
            newPitch = newPitch.transpose(-12.0)
        elif difference <= -threshold:
            newPitch = newPitch.transpose(12.0)

        # apply the accidental if it exists
        if alteration is not None:
            adjust = alteration.alter
            newPitch = newPitch.transpose(adjust)

        # create a new note with the new pitch and the same duration
        new_note = m21.note.Note(newPitch)
        new_note.duration = self.note.duration

        newRoman = get_note_roman_numeral(new_note, newKey)

        return AnalyzedNote(newKey, new_note, newRoman, self.measureNumber, self.timeSignature, self.beatOffset)
