#!/usr/bin/env python2.5
#
# Copyright 2008 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Common utilities. """

import binascii
import hashlib
import struct


bin2hex = Bin2Hex = binascii.hexlify

def GetHash256(expr):
  return hashlib.sha256(expr).digest()

def GetHash256Hex(expr):
  return hashlib.sha256(expr).hexdigest()

def IsFullHash(expr):
  return len(expr) == 32

def network2int(str):
    """Convert network order bytes to a php int

    @param $str string binary string of exactly 4 bytes
    @return int unsigned integer
    """
    if len(str) != 4:
        raise GSB_Exception("trying to convert to binary failed")

    hexparts = struct.unpack("N", str)
    return hexparts[1]

def range2list(str):
    """Converts a GSB range to a list of intervals
    1-3,5-6,9,11 -> [[1,3], [5,6], [9,9], [11,11]]
    """
    r = []
    parts = str.split(',')
    for part in parts:
        minmax = part.split('-', 2)
        if len(minmax) == 1:
            val = int(part[0])
            r.append((val, val))
        else:
            r.append((int(minmax[0]), int(minmax[1])))

    return r

def list2range(values):
    """ List to range
    Takes a *sorted* list of integers and turns them into GSB style ranges
    e.g. array(1,2,3,5,6,9,11) --> "1-3,5-6,9,11"
    """
    ranges = []
    i = 0
    start = 0
    previous = 0

    for chunk in values:
        if i == 0:
            start = chunk
            previous = chunk
        else:
            expected = previous + 1
            if chunk != expected:
                if start == previous:
                    ranges.append(start)
                else:
                    ranges.append(start + '-' + previous)
                start = chunk
            previous = chunk
        i += 1

    if start > 0 and previous > 0:
        if start == previous:
            ranges.append(start)
        else:
            ranges.append(start + '-' + previous)

    return ','.join(ranges)

def formattedRequest(listname, adds, subs):
    """"Format a full request body for a desired list
    including name and full ranges for add and sub
    """
    buildpart = ''

    if len(adds) > 0:
        buildpart += 'a:' + list2range(adds)
    if len(adds) > 0 and len(subs) > 0:
        buildpart += ':'
    if len(subs) > 0:
        buildpart += 's:' + list2range(subs)

    return listname + ';' + buildpart + "\n"
