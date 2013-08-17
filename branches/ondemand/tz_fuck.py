from datetime import tzinfo, timedelta, datetime

class UTC(tzinfo):
    def utcoffset(self, dt):
        return timedelta(0)
    def tzname(self, dt):
        return "UTC"
    def dst(self, dt):
        return timedelta(0)

class ConstantOffsetTimeZone(tzinfo):
    def __init__(self, utc_offset):
        super(ConstantOffsetTimeZone, self).__init__()
        self.utc_offset = utc_offset
    def utcoffset(self, dt):
        return self.utc_offset
    def tzname(self, dt):
        assert False, 'tzname could not be defined, do not use formatting %%Z'
    def dst(self, dt):
        return timedelta(0)

def clone_naive_local_datetime_with_timezone_info(dt):
    assert dt.tzinfo is None
    utc_offset = datetime.now() - datetime.utcnow()
    aware = dt.replace(tzinfo=ConstantOffsetTimeZone(utc_offset))
    return aware

FMT_PARSE = '%Y-%m-%d %H:%M:%S'
FMT_PRINT = '%Y-%m-%d %H:%M:%S %z'
FMT_PRINT_UTC = '%Y-%m-%d %H:%M:%S %z %Z'

s_date = '2012-01-01 12:00:00'
local_naive = datetime.strptime(s_date, '%Y-%m-%d %H:%M:%S')
local_aware = clone_naive_local_datetime_with_timezone_info(local_naive)
utc = local_aware.astimezone(UTC())

print 'original: %s' % s_date
print '   naive: %s' % local_naive.strftime(FMT_PRINT)
print '     msk: %s' % local_aware.strftime(FMT_PRINT)
print '     utc: %s' % utc.strftime(FMT_PRINT_UTC)