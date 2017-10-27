import music21 as m21
import numpy as np
import sklearn as skl
import sys
from collections import defaultdict
from random import shuffle

# start using debuggers for this code and set up a testing suite

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
            maxPitch (Int): Highest desired pitch threshold
            minPitch (Int): Lowest desired pitch threshold

        Returns:
            new_note (AnalyzedNote): new note analyzed in a different key.
        """

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


# transformation 1
def transpose_to_new_key(measures, key):
    """
    Translates all notes from their current key to the new key

    Args:
        measures (List[List[AnalyzedNotes]]): Song notes grouped by measure
        key (music21.key.Key): The key signature context.

    Returns:
        transposed_measures (List[List[AnalyzedNote]]): List of transposed notes grouped by their
                                                        corresponding measures.
    """
    transposed_measures = []
    for measure in measures:
        m = [note.in_new_key(key) for note in measure]

        transposed_measures.append(m)

    return transposed_measures

# transformation 2
def fill_ostinato(measures, rhythm):
    """
    Takes the rhythm and applies the rhythm over the
    measures in the song. Forms a song structured on a single
    rhythmic idea.

    Args:
        measures (List[List[AnalyzedNote]]) Analyzed notes grouped in measures
        rhythm (List[int]) List, whose length == 4, where each index specifies the quarter-note
                           division being played. Ex: 2 = eighth notes, 3 = eighth note triplets, etc.

    Returns:
        ostinated_measures(List[List[AnalyzedNote]]): list of measures with the repeated rhythm applied
    """
    assert(len(rhythm) == 4)

    # ostinato doesn't currently work on rests, so replace them with notes
    measures = replace_rests(measures)

    ostinated_measures = []
    for measure in measures:
        # dictonary that maps the present notes to the previous quarter note beat
        prev_notes_on_beats = defaultdict(list)

        #return measure
        m = []

        # map each note to its previous strong beat
        for note in measure:
            # previous quarter note beat number
            beat = int(note.beatOffset)

            # place the note to its prev beat.
            prev_notes_on_beats[beat].append(note)

        for i in range(len(rhythm)):
            #current quarter note beat == i + 1
            notes = []
            cur_index = i + 1
            # find notes. if current index beat doesn't have note attacks, look at previous beats
            while len(notes) == 0 and cur_index > 0:
                notes = prev_notes_on_beats[cur_index]
                cur_index -= 1

            # if there are still no notes.
            if len(notes) == 0:
                raise ValueError('This song has no notes...')

            print(notes)


            # 1 = quarter, 2 = eighth, 3 = eighth triplet, 4 = sixteenth notes, etc.
            num_notes_for_rhythm = rhythm[i]
            ql = 1.0/num_notes_for_rhythm

            if num_notes_for_rhythm == len(notes):
                print ("EQUALS")
                for note in notes:
                    p = note.note.nameWithOctave
                    new_note = m21.note.Note(p)

                    new_note.duration = m21.duration.Duration(quarterLength=ql)

                    m.append(note.copy(note=new_note))


            elif num_notes_for_rhythm > len(notes):
                print("HERE")
                # divide the rhythm evenly along notes
                times = [int(num_notes_for_rhythm/len(notes)) for i in range(len(notes))]

                extra = num_notes_for_rhythm % len(notes)

                # if not even, add extra notes from the beginning
                if extra != 0:
                    for i in range(extra):
                        times[i] += 1

                print(times)

                for i in range(len(notes)):
                    note = notes[i]
                    p = note.note.nameWithOctave

                    t = times[i]

                    # t = some integer
                    for repeat in range(t):
                        new_note = m21.note.Note(p)
                        new_note.duration = m21.duration.Duration(quarterLength=ql)

                        m.append(note.copy(note=new_note))

            else:
                first = notes[::2]
                then = notes[1::2]

                seq = first + then
                for i in range(num_notes_for_rhythm):
                    note = seq[i]

                    p = note.note.nameWithOctave

                    new_note = m21.note.Note(p)
                    new_note.duration = m21.duration.Duration(quarterLength=ql)

                    m.append(note.copy(note=new_note))

        ostinated_measures.append(m)

    return ostinated_measures

# transformation 3
def replace_rests(measures):
    """
    Removes all rests from measures, and replaces them with a nearby note

    Args:
        measures (List[List[AnalyzedNote]]) Analyzed notes grouped in measures

    Returns:
        altered_measures(List[List[AnalyzedNote]]): list of measures with replaced rests.
    """
    altered_measures = []

    for measure in measures:
        m = []

        # find all non-rest notes in measure
        notes = list(filter(lambda x: x.is_note(), measure))

        if len(notes) == 0:
            raise ValueError('There are no notes in this measure')

        for i in range(len(measure)):
            note = measure[i]

            if note.is_rest():
                if i == 0:
                    index = i+1
                else:
                    index = i-1

                d = note.note.duration
                p = notes[index%len(notes)].note.nameWithOctave

                new_note = m21.note.Note(p)
                new_note.duration = d

                m.append(note.copy(note=new_note))

            else:
                m.append(note)

        altered_measures.append(m)

    return altered_measures


#TODO: Try catch transformation, in the error condition, if one of them returns an error, add a different functionality, possibly a vamp state.


#
# Main Function
#

#TODO: Start building the bigger structure faster


if __name__ == "__main__":

    """
    Song 1: The Bare Necessities
    """
    converter = m21.converter

    # entire stream.Score of the song
    song = converter.parse('../scores/bare-necessities.xml')
    song1 = converter.parse('../scores/test.xml')
    analyzed_notes = analyze_notes_by_measure(song)

    #TODO: argparse
    tonic = sys.argv[1]
    mode = sys.argv[2]
    r1 = int(sys.argv[3])
    r2 = int(sys.argv[4])
    r3 = int(sys.argv[5])
    r4 = int(sys.argv[6])

    functioning_key = m21.key.Key(tonic, mode)

    transposed = transpose_to_new_key(analyzed_notes, functioning_key)
    s1 = analyze_note_measures_to_stream(replace_rests(transposed))


    ostinated = fill_ostinato(transposed, [r1, r2, r3, r4])

    s2 = analyze_note_measures_to_stream(ostinated)

    s2.show()
