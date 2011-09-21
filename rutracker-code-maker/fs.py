import os

from utils import short_names_to_long, is_supported_audio_file
import media_info

class RegFile():
    def __init__(self, path):
        self.path = path
    def get_size(self):
        return os.path.getsize(self.path)
    def __str__(self):
        return "File(%s)" % self.path
    def get_last_name(self):
        return os.path.split(self.path)[1]
    def get_extension(self):
        return os.path.splitext(self.path)[1][1:]

class Dir():
    def __init__(self, path):
        self.path = path
        self.dirs = []
        self.reg_files = []
    def collect_sub_files(self):
        for file in short_names_to_long(self.path, sorted(os.listdir(self.path))):
            if os.path.isdir(file):
                sub_dir = Dir(file)
                self.dirs.append(sub_dir)
                sub_dir.collect_sub_files()
            else:
                reg_file = RegFile(file)
                self.reg_files.append(reg_file)
        return self
    def get_size(self):
        size = 0
        for f in self.reg_files: size += f.get_size()
        for f in self.dirs: size += f.get_size()
        return size
    def __str__(self):
        return "Dir(%s)" % self.path
    def get_last_name(self):
        return os.path.split(self.path)[1]
    def contains_audio_recursively(self):
        """
        Return True if this or subsequent directories contains any audio files.
        """
        for f in self.reg_files:
            if is_supported_audio_file(f.path):
                return True
        for dir in self.dirs:
            if dir.contains_audio_recursively():
                return True
        return False
    def collect_audio_info(self, collector = None):
        class Collector():
            def __init__(self):
                self.bitrate_sum = 0
                self.bitrate_cnt = 0
                self.length = 0
            def collect(self, track):
                len, brt = media_info.get_single_audio_info(track)
                if len and brt:
                    self.bitrate_cnt += 1
                    self.bitrate_sum += brt
                    self.length += len
            def get_length(self):
                return self.length
            def get_average_bitrate(self):
                return (self.bitrate_sum / 1000 / self.bitrate_cnt) if (self.bitrate_cnt > 0) else 0
        if collector is None:
            collector = Collector()
        for track in self.reg_files:
            collector.collect(track)
        for dir in self.dirs:
            dir.collect_audio_info(collector)
        return collector
