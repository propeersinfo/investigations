import sys, wave

def frame_pack(frames, out):
    i = 0
    while i < len(frames):
        out.write("%c%c" % (frames[i], frames[i+1]))
        i += 2

def read_frames(inn, out, chs, sampw, nframes):
    i = 0
    while i < nframes:
        frames = inn.readframes(10*1024)
        frames_read = len(frames) / (chs*sampw)
        frame_pack(frames, out)
        i += frames_read

inn = wave.open("wav/italiano.wav", "rb")
try:
    (chs,sampw,hz,nframes,_,_) = inn.getparams()
    read_frames(inn, sys.stdout, chs, sampw, nframes)
finally:
    inn.close()