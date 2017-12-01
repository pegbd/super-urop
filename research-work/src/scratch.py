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
mammoth_paths = m21.corpus.getComposer('ryansMammoth')

for song in mammoth_paths[:5]:
    m21.converter.parse(song).show('midi')
