import sys
from math import log10, fabs
import wave

class Wave:
    def __init__(self, fname):
        self.in_stream = wave.open(fname, "rb")
        (self.chs, self.sampw, self.hz, self.nframes, _, _) = self.in_stream.getparams()
    def readframes(self, amount):
        return self.in_stream.readframes(amount)
    def close(self):
        return self.in_stream.close()

#def assert_equals(property, wave1, wave2):
#    print "property: ", wave1[property]

def unpack_two_bytes(ch1, ch2):
    value16 = ord(ch1) | ord(ch2) << 8
    if value16 & 0x8000 != 0:
        value16 -= 0x10000
    return value16

def pack_two_bytes(value16):
    value16 &= 0xFFFF
    return chr(value16 & 0xFF), chr(value16 >> 8)

def do_assertion(wave1, wave2):
    assert wave1.chs == wave2.chs
    assert wave1.sampw == wave2.sampw
    assert wave1.hz == wave2.hz
    assert wave1.nframes == wave2.nframes

(volt_sum_1, volt_sum_2) = (0, 0)
diff_sum = 0

def diff_frame_packs(frames1, frames2):
    global volt_sum_1, volt_sum_2, diff_sum
    assert len(frames1) == len(frames2)
    length = len(frames1)
    i = 0
    while i < length:
        volt1 = abs(unpack_two_bytes(frames1[i], frames1[i+1]))
        volt_sum_1 += volt1
        volt2 = abs(unpack_two_bytes(frames2[i], frames2[i+1]))
        volt_sum_2 += volt2
        diff_sum += abs(volt1 - volt2)
        i += 2

def diff(wave1, wave2):
    do_assertion(wave1, wave2)
    i = 0
    nframes = wave1.nframes
    bufsize = 10 * 1024
    assert bufsize % wave1.chs == 0
    while i < nframes:
        frames1 = wave1.readframes(bufsize)
        frames2 = wave2.readframes(bufsize)
        diff_frame_packs(frames1, frames2)
        i += len(frames1)

wave1 = Wave(sys.argv[1])
wave2 = Wave(sys.argv[2])
diff(wave1, wave2)
wave1.close()
wave2.close()

abs_difference = diff_sum
abs_difference_old = abs(volt_sum_1 - volt_sum_2)
relative_difference = float(abs_difference) / float(volt_sum_1)
print "volt_sum_1: ", volt_sum_1
print "volt_sum_2: ", volt_sum_2
print "abs difference: %d (old=%d)" % (abs_difference, abs_difference_old)
print "rel difference: %.5f %%" % (relative_difference*100)
#print "diff_sum: ", diff_sum