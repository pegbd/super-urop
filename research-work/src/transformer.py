import music21 as m21
import numpy as np
import sklearn as skl
import sys
from collections import defaultdict
from random import shuffle


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

            # 1 = quarter, 2 = eighth, 3 = eighth triplet, 4 = sixteenth notes, etc.
            num_notes_for_rhythm = rhythm[i]
            ql = 1.0/num_notes_for_rhythm

            # if there are equal notes as required for the new rhythm
            if num_notes_for_rhythm == len(notes):
                for note in notes:
                    p = note.note.nameWithOctave
                    new_note = m21.note.Note(p)

                    new_note.duration = m21.duration.Duration(quarterLength=ql)
                    m.append(note.copy(note=new_note))

            elif num_notes_for_rhythm > len(notes):
                # divide the rhythm evenly along notes
                times = [int(num_notes_for_rhythm/len(notes)) for n in range(len(notes))]

                extra = num_notes_for_rhythm % len(notes)

                # if not even, add extra notes from the beginning
                if extra != 0:
                    for x in range(extra):
                        times[x] += 1

                internal_offset = 0
                for j in range(len(notes)):
                    note = notes[j]
                    p = note.note.nameWithOctave

                    t = times[j]

                    # t = some integer
                    for repeat in range(t):
                        new_note = m21.note.Note(p)
                        new_note.duration = m21.duration.Duration(quarterLength=ql)
                        offset = (i + 1) + (internal_offset)*ql
                        m.append(note.copy(note=new_note, beatOffset=offset))
                        internal_offset += 1

            else:
                first = notes[::2]
                then = notes[1::2]

                seq = first + then
                for j in range(num_notes_for_rhythm):
                    note = seq[j]

                    p = note.note.nameWithOctave

                    new_note = m21.note.Note(p)
                    new_note.duration = m21.duration.Duration(quarterLength=ql)

                    offset = (i + 1) + j*ql
                    m.append(note.copy(note=new_note, beatOffset=offset))

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
