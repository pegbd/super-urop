import av_grid
import matplotlib.pyplot as plt
import analyzer
import music21 as m21

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

scale1 = m21.scale.MajorScale('a')
pitches1 = [str(p) for p in scale1.getPitches('C4', 'G5')]

print (pitches1[:-4])
