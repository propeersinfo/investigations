from math import log10, fabs
import wave

dbsum = 0
dbcnt = 0

MAX = 32767

#def compress(value16):
#	hilimit = 10*1000
#	if value16 > hilimit: value16 = hilimit
#	if value16 < -hilimit: value16 = -hilimit
#	return value16

# @param val - 16 bit integer
def process_frame(val):
	if val < 0:
		val = int(val * 1.25)
	return val

def stat(value16):
	#db = log10(fabs(value16 / 32767.0)) * 20
	db = fabs(value16 / MAX) ** 2
	global dbsum, dbcnt
	dbsum += db
	dbcnt += 1

def handle_sample_bytes(ch1, ch2, out):
	value16 = ord(ch1) | ord(ch2) << 8
	if value16 & 0x8000 != 0:
		value16 = value16 - 0x10000
	stat(value16)
	value16 = process_frame(value16)
	value16 = value16 & 0xFFFF
	out.write(chr(value16 & 0xFF))
	out.write(chr(value16 >> 8))

def alter(frames):
	from cStringIO import StringIO
	out = StringIO()
	i = 0
	while i < len(frames):
		handle_sample_bytes(frames[i], frames[i+1], out)
		i += 2
	return out.getvalue()

def read_frames(inn, out, chs, sampw):
	i = 0
	while i < nframes:
		frames = inn.readframes(10*1000)
		frames_read = len(frames) / (chs*sampw)
		conv = alter(frames)
		out.writeframesraw(conv)
		i += frames_read

################ MAIN

inn = wave.open("pluton.wav", "rb")

print inn.getparams()
(chs,sampw,hz,nframes,x,x) = inn.getparams()

out = wave.open("out.wav", "wb")
out.setparams(inn.getparams())

read_frames(inn, out, chs, sampw)

out.close()

print "dbcnt: ", dbcnt
#print "db avg: ", (dbsum / dbcnt)
print "db avg: ", log10(dbsum / dbcnt) * 10
