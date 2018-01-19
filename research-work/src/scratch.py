import music21 as m21
import numpy as np
import sklearn as skl
import sys
from collections import defaultdict
from random import shuffle
import analyzer
import transformer
import looper

converter = m21.converter
song = converter.parse('../scores/zelda.xml')

m = analyzer.analyze_elements_by_measure(song)

analyzer.analyze_element_measures_to_stream(transformer.fill_ostinato(m[0], [3, 1, 3, 1])).show('midi')
