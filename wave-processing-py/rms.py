from math import log10, fabs, sqrt, floor
import wave

dbsum = 0
nsamples = 0
rmssum = 0

MAX = 32768

class StatHandlerPack:
    def __init__(self, handlers):
        self.handlers = handlers
    def handle_value(self, value):
        for handler in self.handlers:
            handler.handle_value(value)
    def clear(self):
        for handler in self.handlers:
            handler.clear()

class AvgDb:
    def __init__(self):
        self.sum_voltage = 0
        self.count = 0
    def handle_value(self, relative_voltage_value):
        self.sum_voltage += fabs(relative_voltage_value)
        self.count += 1
    def get_avg_db(self):
        avg_volt = self.sum_voltage / self.count
        #print "count: ", self.count
        #print "sum_voltage: ", self.sum_voltage
        db = log10(avg_volt) * 20
        return db
    def clear(self):
        self.sum_voltage = 0
        self.count = 0

class RmsCalc:
    def __init__(self):
        self.sum = 0
        self.nsamples = 0
    def handle_value(self, relative_voltage_value):
        self.sum += fabs(relative_voltage_value) ** 2
        self.nsamples += 1
    def get_rms(self):
        return log10(sqrt(self.sum / self.nsamples)) *20
    def clear(self):
        self.sum = 0
        self.nsamples = 0

# @param val - 16 bit integer
def process_frame(val):
    if val < 0:
        val = int(val * 1.20)
    return val


def handle_stat(value16, stats):
    percent_value = value16 / float(MAX)
    abs = fabs(percent_value)
    if abs != 0.0:
        db = log10(abs) * 20
        #db = fabs(value16 / MAX) ** 2
        global dbsum, nsamples, rmssum
        dbsum += db
    rmssum += abs ** 2
    nsamples += 1
    stats.handle_value(percent_value)


def handle_sample_bytes(ch1, ch2, out, stats):
    value16 = ord(ch1) | ord(ch2) << 8
    if value16 & 0x8000 != 0:
        value16 -= 0x10000
    handle_stat(value16, stats)
    #value16 = process_frame(value16)
    #value16 &= 0xFFFF
    #out.write(chr(value16 & 0xFF))
    #out.write(chr(value16 >> 8))

def handle_frames(frames, stats):
    #from cStringIO import StringIO
    #out = StringIO()
    i = 0
    while i < len(frames):
        handle_sample_bytes(frames[i], frames[i+1], out, stats)
        i += 2
    #return out.getvalue()


def read_frames(inn, out, max_frames, chs, sampw, gfx = None):
    i = 0
    while i < max_frames:
        frames = inn.readframes(4000)
        frames_read = len(frames) / (chs * sampw)
        conv = handle_frames(frames, gfx.handlers)
        #out.writeframesraw(conv)
        i += frames_read
        if gfx: gfx.frame_pack_has_been_read()

################ MAIN

import sys
import pygame

class Gfx:
    def __init__(self):
        self.rms = RmsCalc()
        self.avg_db = AvgDb()
        self.handlers = StatHandlerPack([self.rms, self.avg_db])
        self.count = 0
        pygame.init()
        self.window = pygame.display.set_mode((640, 480))

    def frame_pack_has_been_read(self):
        rms = fabs(self.rms.get_rms())
        db = fabs(self.avg_db.get_avg_db())
        print "rms/avg for a second: %.2f / %.2f" % (rms, db)
        x = 10 + self.count
        y = 10
        koef = 5.0
        dbH = floor(y + db*koef)
        color_db = (100, 255, 100)
        pygame.draw.line(self.window, color_db, (x, y), (x, dbH))

        rmsH = floor(y + rms*koef)
        color_rms = (200, 100, 100)
        pygame.draw.line(self.window, color_rms, (x, y), (x, rmsH))

        self.count += 1
        pygame.display.flip()
        self.handlers.clear()

    def loop(self):
        while True:
           for event in pygame.event.get():
              if event.type == pygame.QUIT:
                  sys.exit(0)
              else:
                  print event


####################

gfx = Gfx()
#gfx = None

#in_filename = "nano.wav"
in_filename = "italiano.wav"

print "file: %s" % in_filename

inn = wave.open(in_filename, "rb")

#print inn.getparams()
(chs,sampw,hz,nframes,x,x) = inn.getparams()

out = None
#out = wave.open("out.wav", "wb")
if out: out.setparams(inn.getparams())

read_frames(inn, out, nframes, chs, sampw, gfx)

if out: out.close()

print "samples: ", nsamples
print "db avg:  ", (dbsum / nsamples)
#print "db avg: ", log10(dbsum / dbcnt) * 10
print "rms avg: ", log10(sqrt(rmssum / nsamples))*20

######################

if gfx: gfx.loop()