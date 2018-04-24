import av_grid
import matplotlib.pyplot as plt
import analyzer
import music21 as m21
import random
import os
import timeit

# tempo_grid = av_grid.TempoGrid()
# tempo_grid.parse_point_file('./av-grid-points/tempo.txt')
#
# points = tempo_grid.get_points()
# p, d = tempo_grid.sample_parameter_point(0.75, 0.75)
# print (p.arousal)
#
# print ([(pt.arousal, pt.valence) for pt in points])
#
#
# x = [pt.valence for pt in points]
# y = [pt.arousal for pt in points]
#
# plt.plot(y, x, 'ro')
# plt.show()

# print (analyzer.mode_intervals['major'])
# print(analyzer.mode_intervals['minor'])

# k = m21.key.Key('C')
# nk = m21.key.Key('b')
#
# n = m21.note.Note('E4')
#
# an = analyzer.AnalyzedElement(k, n)
#
# print(an.in_new_key(nk).element.nameWithOctave)

# scale1 = m21.scale.MajorScale('a')
# pitches1 = [str(p) for p in scale1.getPitches('C4', 'G5')]
#
# print (pitches1[:-4])

# f = open('./av-grid-points/rhythm.txt', 'w')
#
# for i in range(1,5):
#     for j in range(1,5):
#         for k in range(1,5):
#             for l in range(1,5):
#                 line = str(i) + ' ' + str(j) + ' ' + str(k) + ' ' + str(l)
#                 random_arousal = random.random() - 0.5
#                 random_arousal /= 0.5
#
#                 random_valence = random.random() - 0.5
#                 random_valence /= 0.5
#
#                 line += '\t' + str(random_arousal) + '\t' + str(random_valence) + '\n'
#
#                 print(line)
#                 f.write(line)
#                 f.flush()
#                 os.fsync(f.fileno())
#
# f.close()

self.file = open('./data/av.txt', 'r')


timeit.timeit()
