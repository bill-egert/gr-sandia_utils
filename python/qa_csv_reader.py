#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 gr-sandia_utils author.
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#

from gnuradio import gr, gr_unittest
from gnuradio import blocks
import numpy as np
import os
import pmt
import time
from csv_reader import csv_reader

class qa_csv_reader (gr_unittest.TestCase):

    def setUp (self):
        self.tb = gr.top_block ()
        self.debug = blocks.message_debug()

    def tearDown (self):
        self.tb = None

        # remove temporary file
        os.remove('/tmp/file.csv')

    def test_001_all_header_fields (self):
      with open('/tmp/file.csv', 'w') as f:
        # write header
        f.write('field0(string), , field1(bool), field2(float),' + \
                'field3(long), field4(uint64), field5(double),' + \
                'field6(complex),field7\n');

        # add some data
        f.write('field0, empty, True, 1.0,1234567890,987654321, 2.5,1+2j,string,1,2,3,4,5\n')

      # start reader/
      reader = csv_reader(fname = '/tmp/file.csv', has_header = True,
                          period=10, start_delay = 0, repeat = False)

      # expected pdu
      metadata = pmt.dict_add(pmt.make_dict(),pmt.intern('field0'),pmt.intern('field0'))
      metadata = pmt.dict_add(metadata,pmt.intern('field1'),pmt.from_bool(True))
      metadata = pmt.dict_add(metadata,pmt.intern('field2'),pmt.from_float(1.0))
      metadata = pmt.dict_add(metadata,pmt.intern('field3'),pmt.from_long(1234567890))
      metadata = pmt.dict_add(metadata,pmt.intern('field4'),pmt.from_uint64(987654321))
      metadata = pmt.dict_add(metadata,pmt.intern('field5'),pmt.from_double(2.5))
      metadata = pmt.dict_add(metadata,pmt.intern('field6'),pmt.from_complex(1.0+2j))
      metadata = pmt.dict_add(metadata,pmt.intern('field7'),pmt.intern('string'))

      data = pmt.init_u8vector(5,[1,2,3,4,5])
      expected = pmt.cons(metadata,data)

      # run
      self.tb.msg_connect((reader,'out'),(self.debug,'store'))
      self.tb.start()
      time.sleep(.5)
      self.tb.stop()
      self.tb.wait()

      got = self.debug.get_message(0)

      self.assertTrue(pmt.equal(expected,got))

    def test_002_no_header (self):
      with open('/tmp/file.csv', 'w') as f:
        # add some data
        f.write('1,2,3,4,5\n')

      # start reader/
      reader = csv_reader(fname = '/tmp/file.csv', has_header = False,
                          period=10, start_delay = 0, repeat = False)

      # expected pdu
      data = pmt.init_u8vector(5,[1,2,3,4,5])
      expected = pmt.cons(pmt.PMT_NIL,data)

      # run
      self.tb.msg_connect((reader,'out'),(self.debug,'store'))
      self.tb.start()
      time.sleep(.5)
      self.tb.stop()
      self.tb.wait()

      got = self.debug.get_message(0)
      self.assertTrue(pmt.equal(expected,got))

    def test_003_data_types (self):
      with open('/tmp/file.csv', 'w') as f:
        # add some data
        f.write('1,2,3,4,5\n')

      # data types and their constructors
      data_types = { 'uint8': pmt.init_u8vector,
                     'int8': pmt.init_s8vector,
                     'uint16': pmt.init_u16vector,
                     'int16': pmt.init_s16vector,
                     'uint32': pmt.init_u32vector,
                     'int32': pmt.init_s32vector,
                     'float': pmt.init_f32vector,
                     'complex float': pmt.init_c32vector,
                     'double': pmt.init_f64vector,
                     'complex double': pmt.init_c64vector
                     }

      passed = True
      for data_type,init_func in data_types.iteritems():
        # start reader/
        reader = csv_reader(fname = '/tmp/file.csv', data_type=data_type,
                            has_header = False, start_delay = 0, period=10,
                            repeat = False)

        # expected pdu
        data = init_func(5,[1,2,3,4,5])
        expected = pmt.cons(pmt.PMT_NIL,data)

        # run
        tb = gr.top_block ()
        debug = blocks.message_debug()
        tb.msg_connect((reader,'out'),(debug,'store'))
        tb.start()
        time.sleep(.25)
        tb.stop()
        tb.wait()

        got = debug.get_message(0)
        passed &= pmt.equal(expected, got)

      self.assertTrue(passed)

if __name__ == '__main__':
    gr_unittest.run(qa_csv_reader, "qa_csv_reader.xml")