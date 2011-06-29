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
    max_volt = 0
    min_volt = 0
    while i < len(frames):
        volt = get_16(frames[i], frames[i+1])
        if volt > 0:
            if volt > max_volt: max_volt = volt
        else:
            if volt < min_volt: min_volt = volt
        i += 2
        i += 2
    return max_volt, min_volt

def read_frames(inn, out, chs, sampw, hz, total_frames, frames_in_pack):
    frame_cnt = 0
    pack_cnt = 0
    while frame_cnt < total_frames:
        frames = inn.read(frames_in_pack)
        frames_read = len(frames) / (chs*sampw)
        frame_cnt += frames_read

        (max_volt, min_volt) = frame_pack(frames)
        time_in_seconds = float(frame_cnt) / hz
        print "%f %d %d" % (time_in_seconds, max_volt, min_volt)

        pack_cnt += 1

in_file = None
try:
    in_file = sys.argv[1]
except IndexError:
    in_file = "wav/italiano.wav"
inn = open(in_file, "rb")

arr = array.array("L")
arr.fromfile(inn, 4)
(chs,sampw,hz,nframes) = arr
print "; channels: ", chs
print "; sample width: ", sampw
print "; frequency: ", hz
print "; frames: ", nframes

frames_in_pack = nframes / 608 * 4 # 608 is standard width of a gnuplot produced image
frames_in_pack += frames_in_pack % 4
read_frames(inn, sys.stdout, chs, sampw, hz, nframes, frames_in_pack)
inn.close()
