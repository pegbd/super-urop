import av_grid
import matplotlib.pyplot as plt

tempo_grid = av_grid.TempoGrid()
tempo_grid.parse_point_file('./av-grid-points/tempo.txt')

points = tempo_grid.get_points()
p, d = tempo_grid.sample_parameter_point(0.75, 0.75)
print (p.arousal)

print ([(pt.arousal, pt.valence) for pt in points])


x = [pt.valence for pt in points]
y = [pt.arousal for pt in points]

plt.plot(y, x, 'ro')
plt.show()
