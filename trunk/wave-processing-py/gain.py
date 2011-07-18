import sys
from math import log10, fabs
import wave

dbsum = 0
dbcnt = 0

MAX = 32767

def handle_sample_bytes(ch1, ch2, out, functor):
    value16 = ord(ch1) | ord(ch2) << 8
    if value16 & 0x8000 != 0:
        value16 -= 0x10000
    value16 = int(functor(value16))
    #value16 = compress(value16)
    value16 &= 0xFFFF
    out.write(chr(value16 & 0xFF))
    out.write(chr(value16 >> 8))

def alter(frames, functor):
    from cStringIO import StringIO
    out = StringIO()
    i = 0
    while i < len(frames):
        handle_sample_bytes(frames[i], frames[i+1], out, functor)
        i += 2
    return out.getvalue()

def read_frames(inn, out, chs, sampw, functor):
    i = 0
    while i < nframes:
        frames = inn.readframes(10*1000)
        frames_read = len(frames) / (chs*sampw)
        conv = alter(frames, functor)
        out.writeframesraw(conv)
        i += frames_read

################ MAIN

gain_value = float(sys.argv[1])
input_fname = sys.argv[2]
output_fname = sys.argv[3]

def gain_func(value16):
    value16 *= gain_value
    if value16 > MAX: value16 = MAX
    elif value16 < -MAX: value16 = -MAX
    return value16

inn = wave.open(input_fname, "rb")

print inn.getparams()
(chs,sampw,hz,nframes,x,x) = inn.getparams()

out = wave.open(output_fname, "wb")
out.setparams(inn.getparams())

read_frames(inn, out, chs, sampw, gain_func)

out.close()