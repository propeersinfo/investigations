# -*- coding: utf-8 -*-

from unittest import TestCase

import utils
from utils import pretty_print_json_as_readable_unicode
import common

class SomeTests(TestCase):
    def setUp(self):
        pass

    def test_json_formatter_float(self):
        f1 = 208.87510204081633
        f2 = float(pretty_print_json_as_readable_unicode(f1))
        self.failUnlessEqual(f1, f2)

    def test_json_formatter_long(self):
      self.failUnlessEqual("100", pretty_print_json_as_readable_unicode(100L))

    def test_check_files_continuosity_101_positive(self):
      files = [ '101 a.mp3', '102 a.mp3', '201 a.mp3', '202 a.mp3' ]
      try:
        common.check_files_continuosity('a-dir', files)
      except common.NotAlbumException, e:
        self.fail(e)

    def test_check_files_continuosity_101_negative(self):
      files = [ '101 a.mp3', '102 a.mp3', '201 a.mp3', '204 a.mp3' ]
      with self.assertRaises(common.NotAlbumException):
        common.check_files_continuosity('a-dir', files)

    def test_check_files_continuosity_01_positive(self):
      files = [ '01 a.mp3', '02 a.mp3', '03 a.mp3' ]
      try:
        common.check_files_continuosity('a-dir', files)
      except:
        self.fail()

    def test_check_files_continuosity_A1_positive(self):
      files = [ 'A1 a.mp3', 'A2 a.mp3', 'B1 a.mp3' ]
      try:
        common.check_files_continuosity('a-dir', files)
      except:
        self.fail()

    def test_check_files_continuosity_mixed(self):
      files = [ 'A1 a.mp3', 'A2 a.mp3', '01 a.mp3' ]
      with self.assertRaises(common.NotAlbumException):
        common.check_files_continuosity('a-dir', files)

    def test_normalize_unicode_baltic(self):
      input = u'Žemė'
      golden = u'Zeme'
      actual = utils.normalize_unicode_except_cyrillic(input)
      self.failUnlessEqual(golden, actual)

    def test_normalize_unicode_cyrillic(self):
      input = u'eng рус'
      golden = u'eng рус'
      actual = utils.normalize_unicode_except_cyrillic(input)
      self.failUnlessEqual(golden, actual)