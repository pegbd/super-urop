import music21 as m21
from collections import defaultdict

PITCHES = ['A-', 'A', 'A#', 'B-', 'B', 'C', 'C#', 'D-', 'D', 'D#', 'E-', 'E', 'F', 'F#', 'G-', 'G', 'G#']

class KeyNode:
    def __init__(self, tonic, mode):
        self.tonic = tonic
        self.mode = mode
        self.edges = {} # commond chord edges

    def insert_edge(self, other_node, chords):
        if chords:
            self.edges[other_node] = chords
            other_node.edges[self] = chords

    def get_adjacent_vertices(self):
        return self.edges.keys()

    def is_connected(self, other):
        return (other in self.get_adjacent_vertices()) or (self in other.get_adjacent_vertices())

    def __eq__(self, other):
        return self.tonic == other.tonic and self.mode == other.mode

    def __hash__(self):
        return hash((self.tonic, self.mode))


major_triad_sets = {}
minor_triad_sets = {}
common_chord_graph = []

# MAJOR TRIADS PRE-PROCESSING
for pitch in PITCHES:
    # generate scale and get pitches froms scale
    scale = m21.scale.MajorScale(pitch)
    scale_pitches = [str(p) for p in scale.getPitches('C4', 'G5')]

    # create set of all triads in that scale
    triads = set()
    for p in range(len(scale_pitches) - 4):
        root = scale_pitches[p]
        third = scale_pitches[p + 2]
        fifth = scale_pitches[p + 4]
        triads.add((root, third, fifth))

    major_triad_sets[pitch] = triads

# MINOR TRIADS PRE-PROCESSING
for pitch in PITCHES:
    # generate scale and get pitches froms scale
    scale = m21.scale.MinorScale(pitch)
    scale_pitches = [str(p) for p in scale.getPitches('C4', 'G5')]

    # create set of all triads in that scale
    triads = set()
    for p in range(len(scale_pitches) - 4):
        root = scale_pitches[p]
        third = scale_pitches[p + 2]
        fifth = scale_pitches[p + 4]
        triads.add((root, third, fifth))

    minor_triad_sets[pitch] = triads

for pitch1 in PITCHES:

    node_1_major = KeyNode(pitch1, 'major')
    node_1_minor = KeyNode(pitch1, 'minor')

    # get the current major node if it already exists
    if node_1_major in common_chord_graph:
        get_index = common_chord_graph.index(node_1_major)
        node_1_major = common_chord_graph[get_index]
    else:
        common_chord_graph.append(node_1_major)

    # get the current minor node if it already exists
    if node_1_minor in common_chord_graph:
        get_index = common_chord_graph.index(node_1_minor)
        node_1_minor = common_chord_graph[get_index]
    else:
        common_chord_graph.append(node_1_minor)

    # get the major and minor triads for this scale
    major_triads1 = major_triad_sets[pitch1]
    minor_triads1 = minor_triad_sets[pitch1]

    for pitch2 in PITCHES:

        node_2_major = KeyNode(pitch2, 'major')
        node_2_minor = KeyNode(pitch2, 'minor')

        # get the current major node if it already exists
        if node_2_major in common_chord_graph:
            get_index = common_chord_graph.index(node_2_major)
            node_2_major = common_chord_graph[get_index]
        else:
            common_chord_graph.append(node_2_major)

        # get the current minor node if it already exists
        if node_2_minor in common_chord_graph:
            get_index = common_chord_graph.index(node_2_minor)
            node_2_minor = common_chord_graph[get_index]
        else:
            common_chord_graph.append(node_2_major)

        major_triads2 = major_triad_sets[pitch2]
        minor_triads2 = minor_triad_sets[pitch2]

        if pitch1[0] != pitch2[0]:
            # Major Key -> Major Key
            if node_2_major not in node_1_major.get_adjacent_vertices():
                major_major = list(major_triads1.intersection(major_triads2))
                node_1_major.insert_edge(node_2_major, major_major)

            # Minor Key -> Minor Key
            if node_2_minor not in node_1_minor.get_adjacent_vertices():
                minor_minor = list(minor_triads1.intersection(minor_triads2))
                node_1_minor.insert_edge(node_2_minor, minor_minor)

        # Major Key -> Minor Key
        if node_2_minor not in node_1_major.get_adjacent_vertices():
            major_minor = major_triads1.intersection(minor_triads2)
            node_1_major.insert_edge(node_2_minor, major_minor)

        # Minor Key -> Major Key
        if node_2_major not in node_1_minor.get_adjacent_vertices():
            minor_major = minor_triads1.intersection(major_triads2)
            node_1_minor.insert_edge(node_2_major, minor_major)

for node in common_chord_graph:
    print (node.tonic + ' ' + node.mode)

    for k, v in node.edges.items():
        print (k.tonic + ' ' + k.mode, v)

    print("-----------------------------------")
