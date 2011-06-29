import sys, wave

def get_16(ch1, ch2):
    value16 = ord(ch1) | ord(ch2) << 8
    if value16 & 0x8000 != 0:
        value16 -= 0x10000
    return value16

def frame_pack(frames, out):
    i = 0
    assert len(frames) % 4 == 0
    max_volt = 0
    min_volt = 0
    while i < len(frames):
        #out.write("%c%c" % (frames[i], frames[i+1]))
        volt = get_16(frames[i], frames[i+1])
        if volt > 0:
            if volt > max_volt: max_volt = volt
        else:
            if volt < min_volt: min_volt = volt
        i += 2
        i += 2
    return (max_volt, min_volt)

def read_frames(inn, out, chs, sampw, total_frames):
    frame_cnt = 0
    pack_cnt = 0
    while frame_cnt < total_frames:
        frames = inn.readframes(1024)
        frames_read = len(frames) / (chs*sampw)
        (max_volt, min_volt) = frame_pack(frames, out)
        print pack_cnt, max_volt, min_volt
        frame_cnt += frames_read
        pack_cnt += 1

in_file = ''
try:
    in_file = sys.argv[1]
except:
    in_file = "wav/italiano.wav"
inn = wave.open(in_file, "rb")
try:
    (chs,sampw,hz,nframes,_,_) = inn.getparams()
    read_frames(inn, sys.stdout, chs, sampw, nframes)
finally:
    inn.close()