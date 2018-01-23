import os
import math

f = open('./data/av.txt', 'w')
while True:
    inp = input('arousal/valence:')
    input_check = inp.split(' ')

    if len(input_check) == 2:
        try:
            a = float(input_check[0])
            v = float(input_check[1])

            if math.fabs(a) <= 1 and math.fabs(v) <= 1:
                print("Arousal and Valence Value to Write = " + inp)
                f.write(inp + "\n")
                f.flush()
                os.fsync(f.fileno())
            else:
                print("Values must be between -1 and 1")

        except ValueError:
            print('invalid input')
    elif inp == 'close':
        print("Closing writer")
        f.close()
        break
