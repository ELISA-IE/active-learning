

#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'jfrei86'
from active import ActiveLearning

import sys
reload(sys)
sys.setdefaultencoding('utf8')
import codecs
import os
import random
import re
import operator
import subprocess
import math
from subprocess import Popen
from itertools import repeat

NUM_PROC = 2
WORKING_DIR = './hau'
LTF_DIR = os.path.join(WORKING_DIR,'ltf')
LAF_DIR = os.path.join(WORKING_DIR,'laf')
LAF_SRC = os.path.join(WORKING_DIR,'laf_src')

def annotate(files):
	ann_files = []
	for file in files:
		subprocess.call(['mv', os.path.join(LAF_SRC, file.replace('ltf','laf')), os.path.join(LAF_DIR, file.replace('ltf','laf'))])
		ann_files.append(file.replace('lft','laf'))
	return ann_files

##################################
# DRIVER FUNCTION EXAMPLE
learner = ActiveLearning(WORKING_DIR, os.listdir(LTF_DIR), 50, 50, 100, 5, 'select_entropy', True)
annotated_files = annotate(learner.init_set())
learner.retrain(annotated_files)
while not learner.done():
	files = learner.iterate() #LTF filename list to annotate
	annotated_files = annotate(files) #LAF filename list from annotator to give to retrainer
	learner.retrain(annotated_files) #A list of LAF filenames to retrain with
