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

class AverageVoltage:
    def __init__(self):
        self.sum_voltage = 0
        self.count = 0
    def handle_value(self, relative_voltage_value):
        self.sum_voltage += fabs(relative_voltage_value)
        self.count += 1
    def get_average_voltage(self):
        return float(self.sum_voltage) / self.count
    def clear(self):
        self.sum_voltage = 0
        self.count = 0

class PeakVoltage():
    def __init__(self):
        self.max = 0
    def handle_value(self, relative_voltage_value):
        voltage = fabs(relative_voltage_value)
        if self.max < voltage:
            self.max = voltage
    def get_peak_db(self):
        return log10(self.max) * 20
    def get_peak_voltage(self):
        return self.max
    def clear(self):
        self.max = 0

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

def handle_frames(frames, out, stats):
    #from cStringIO import StringIO
    #out = StringIO()
    i = 0
    while i < len(frames):
        handle_sample_bytes(frames[i], frames[i+1], out, stats)
        i += 2
    #return out.getvalue()


def read_frames(inn, out, max_frames, chs, sampw, gfx, frames_per_pixel):
    i = 0
    while i < max_frames:
        frames = inn.readframes(frames_per_pixel)
        frames_read = len(frames) / (chs * sampw)
        conv = handle_frames(frames, out, gfx.handlers)
        #out.writeframesraw(conv)
        i += frames_read
        if gfx: gfx.frame_pack_has_been_read()

################ MAIN

import sys
import pygame

class Gfx:
    def __init__(self):
        self.average = AverageVoltage()
        self.peak_db = PeakVoltage()
        self.handlers = StatHandlerPack([self.average, self.peak_db])
        self.count = 0
        pygame.init()
        self.window = pygame.display.set_mode((imgw, imgh))

    def frame_pack_has_been_read(self):
        base_x = 0 + self.count
        base_y = int(imgh / 2)
        max_h = int(imgh / 2)

        # zero db line
        #pygame.draw.line(self.window, (200,200,200), (0, base_y + max_h), (imgw, base_y + max_h))

        peak_vt = self.peak_db.get_peak_voltage()
        y1 = floor(base_y - peak_vt * max_h)
        y2 = floor(base_y + peak_vt * max_h)
        color = (100, 200, 100)
        pygame.draw.line(self.window, color, (base_x, base_y), (base_x, y1))
        pygame.draw.line(self.window, color, (base_x, base_y), (base_x, y2))

#        avg_vt = self.average.get_average_voltage()
#        y1 = floor(base_y - avg_vt * max_h)
#        y2 = floor(base_y + avg_vt * max_h)
#        color = (100, 200, 100)
#        pygame.draw.line(self.window, color, (base_x, base_y), (base_x, y1))
#        pygame.draw.line(self.window, color, (base_x, base_y), (base_x, y2))

        self.count += 1
        pygame.display.flip()
        self.handlers.clear()

    def gui_loop(self):
        while True:
           for event in pygame.event.get():
              if event.type == pygame.QUIT:
                  sys.exit(0)
              else:
                  print event


####################

imgw = 1000
imgh = 200

gfx = Gfx()
#gfx = None

#in_filename = "wav/nano.wav"
#in_filename = "wav/italiano.wav"
in_filename = "C:\\Temp\\tour-11-disco-80s.wav"

print "file: %s" % in_filename

inn = wave.open(in_filename, "rb")

#print inn.getparams()
(chs,sampw,hz,nframes,x,x) = inn.getparams()

print "channels: ", chs
print "sampw:    ", sampw
print "max: ", pow(2, sampw*8) / 2
frames_per_pixel = nframes / imgw
print "frames_per_pixel: ", frames_per_pixel

read_frames(inn, None, nframes, chs, sampw, gfx, frames_per_pixel)

print "samples: ", nsamples
print "db avg:  ", (dbsum / nsamples)
#print "db avg: ", log10(dbsum / dbcnt) * 10
print "rms avg: ", log10(sqrt(rmssum / nsamples))*20

######################

if gfx: gfx.gui_loop()