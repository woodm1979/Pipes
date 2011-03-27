#!/usr/bin/env python

import glob
import os
import re
import shutil


nums_re = re.compile(r'_(\d{4})s_\d{4}_(\d{3}).png')

for file_name in glob.glob('_????s_????_???.png'):
    major, minor = (2,3)
    foo = nums_re.search(file_name)
    major = int(foo.group(1))
    minor = int(foo.group(2))
    if minor == 16:
        minor = 0

    print
    print file_name
    print major, minor

    new_majors = []
    if major == 4:
        new_majors = [2, 3]
    elif major == 3:
        new_majors = [5]
    elif major == 5:
        new_majors = [6, 7]

    for major in new_majors:
        new_name = '%03d_%03d.png' % (major, minor)
        print new_name

        shutil.copy(file_name, new_name)

