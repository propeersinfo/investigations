# converts given WAVE sample value into dB

import sys
from math import log10, fabs

MAX = 32767.0

value = int(sys.argv[1])

#print log10(value / MAX) * 20
print log10((value / MAX) ** 2) * 10
