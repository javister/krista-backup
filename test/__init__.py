# -*- encoding: utf-8 -*-

import os

current_filepath = os.path.realpath(__file__)
test_dir = os.path.dirname(current_filepath)

os.chdir(test_dir)
