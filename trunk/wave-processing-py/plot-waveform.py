# plot given audio into waveform image
# gnuplot is used for actual drawing currently

import sys, array

class ExtremumFinder:
    def __init__(self):
        self.max = 0
        self.min = 0
    def pass_value(self, value):
        if value > 0:
            if value > self.max: self.max = value
        else:
            if value < self.min: self.min = value
    def get_extremums(self):
        return self.max, self.min

def get_16(ch1, ch2):
    value16 = ord(ch1) | ord(ch2) << 8
    if value16 & 0x8000 != 0:
        value16 -= 0x10000
    return value16

def frame_pack(frames):
    i = 0
    assert len(frames) % 4 == 0
    left_channel = ExtremumFinder()
    rite_channel = ExtremumFinder()
    while i < len(frames):
        # left channel
        volt = get_16(frames[i], frames[i+1])
        left_channel.pass_value(volt)
        i += 2
        # right channel
        volt = get_16(frames[i], frames[i+1])
        rite_channel.pass_value(volt)
        i += 2
    return left_channel.get_extremums(), rite_channel.get_extremums()

def read_frames(inn, out, chs, sampw, hz, total_frames, frames_in_pack):
    frame_cnt = 0
    pack_cnt = 0
    while frame_cnt < total_frames:
        frames = inn.read(frames_in_pack)
        frames_read = len(frames) / (chs*sampw)
        frame_cnt += frames_read

        (left, rite) = frame_pack(frames)
        time_in_seconds = float(frame_cnt) / hz
        print "%f %d %d %d %d" % (time_in_seconds, left[0], left[1], rite[0], rite[1])

        pack_cnt += 1

def get_cmd_arg(argn, default):
    try:
        return sys.argv[argn]
    except IndexError:
        if default:
            return default
        else:
            raise Exception("No command line argument %d" % argn)

def set_stdin_binary():
    if sys.platform == "win32":
        import os, msvcrt
        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)

set_stdin_binary()
inn = sys.stdin

arr = array.array("L")
arr.fromfile(inn, 4)
(chs,sampw,hz,nframes) = arr
print "; channels: ", chs
print "; sample width: ", sampw
print "; frequency: ", hz
print "; frames: ", nframes

frames_in_pack = nframes / 608 * 4 # 608 is default width of a gnuplot produced image
frames_in_pack += frames_in_pack % 4

read_frames(inn, sys.stdout, chs, sampw, hz, nframes, frames_in_pack)

if inn != sys.stdin: inn.close()