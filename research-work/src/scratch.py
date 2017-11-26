import music21 as m21
import numpy as np
import sklearn as skl
import sys
from collections import defaultdict
from random import shuffle
import analyzer
import transformer
import looper

key = m21.key.Key('c', 'major')

n = m21.note.Note(nameWithOctave="E5")
c = m21.chord.Chord(["C4", "E4", "G4", "C5"])

print (list(c.pitches))

a = analyzer.AnalyzedElement(key, n)

key2 = m21.key.Key('f', 'dorian')

song1 = '../scores/satb.xml'

parts, s = analyzer.analyze(song1)

print(s.analyze("key"))

print (parts)

# transposed = transformer.transpose_to_new_key(parts, key2)
# s = analyzer.to_stream(transposed)

# s.show('midi')
