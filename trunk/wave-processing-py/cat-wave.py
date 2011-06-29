# concatenate given *.wav file into stdout
# as a raw stream of samples without any meta data

import sys, wave, array

def write_ulong(out, values):
    arr = array.array('L', values) # 'L' means unsigned long
    arr.tofile(out)

def get_16(ch1, ch2):
    value16 = ord(ch1) | ord(ch2) << 8
    if value16 & 0x8000 != 0:
        value16 -= 0x10000
    return value16

FRAME_COUNT = 0

def frame_pack(frames, out, out2):
    i = 0
    while i < len(frames):
        out.write("%c%c" % (frames[i], frames[i+1]))
        v16 = get_16(frames[i], frames[i+1])
        out2.write("%d\n" % v16)
        global FRAME_COUNT
        FRAME_COUNT += 1
        i += 2

def read_frames(inn, out, out2, chs, sampw, nframes):
    i = 0
    while i < nframes:
        frames = inn.readframes(10*1024)
        frames_read = len(frames) / (chs*sampw)
        frame_pack(frames, out, out2)
        i += frames_read

out2 = open("values-from-internal.dat", "w")

in_file = ''
try:
    in_file = sys.argv[1]
except IndexError:
    in_file = "wav/italiano.wav"

inn = wave.open(in_file, "rb")
(chs,sampw,hz,nframes,_,_) = inn.getparams()

if sys.platform == "win32":
    import os, msvcrt
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

out = sys.stdout

write_ulong(out, [chs,sampw,hz,nframes])
read_frames(inn, out, out2, chs, sampw, nframes)
#out.close()
inn.close()

#out2.write("FRAME_COUNT = %d" % FRAME_COUNT)
out2.close()
