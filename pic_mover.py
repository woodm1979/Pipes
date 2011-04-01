#!/usr/bin/env python

import glob
import re
import shutil


nums_re = re.compile(r'_\d{4}s_(\d{4})s_\d{4}_(\d{2}).png')

for file_name in glob.glob('*.png'):
    foo = nums_re.search(file_name)
    if not foo:
        print 'non-used file: %r' % file_name
        continue

    major = int(foo.group(1))
    minor = int(foo.group(2)) % 16

    print
    print file_name
    print major, minor

    new_majors_dict = {
        0: [0],
        1: [1],
        2: [2, 3],
        3: [2],
        4: [5],
        5: [6, 7],
        6: [6, 7],
        7: [6],
    }

    new_minor_dict = {
        1: 1,
        2: 2,
        3: 3,
        4: 4,
    }

    new_majors = new_majors_dict[major]
    minor = new_minor_dict.get(minor, minor)

    for major in new_majors:
        new_name = '%03d_%03d.png' % (major, minor)
        print new_name

        shutil.copy(file_name, new_name)
