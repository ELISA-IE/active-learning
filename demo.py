#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'jfrei86'
from active import ActiveLearning

import sys
reload(sys)
sys.setdefaultencoding('utf8')
import codecs
import os
import io
from poster.encode import multipart_encode
import urllib2
import random
import re
import operator
import subprocess
import math
from subprocess import Popen
from itertools import repeat
import shutil
import json

from collections import OrderedDict
from multiprocessing import cpu_count


NUM_PROC = cpu_count() / 2 if cpu_count() / 2 < 10 else 10  # use half of the cpus, maximum is 10.
WORKING_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'data/workspace/hau')
LTF_TRAIN_DIR = os.path.join(WORKING_DIR,'ltf_train')
LTF_TEST_DIR = os.path.join(WORKING_DIR,'ltf_test')
LAF_TRAIN_DIR = os.path.join(WORKING_DIR,'laf_train')
LAF_TEST_DIR = os.path.join(WORKING_DIR,'laf_test')
LAF_CURRENT_TRAIN_DIR = os.path.join(WORKING_DIR,'laf_current_train')
OUT_DIR = os.path.join(WORKING_DIR,'output_current_train')
OUT_TEST_DIR = os.path.join(WORKING_DIR, 'output_test')
EVAL_DIR = os.path.join(WORKING_DIR, 'eval')

TAG = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   'tagger.py')
MODEL_DIR = os.path.join(WORKING_DIR,'model')


def annotate(files):
    ann_files = []
    for file in files:
        subprocess.call(['cp', os.path.join(LAF_TRAIN_DIR, file.replace('ltf','laf')), os.path.join(LAF_CURRENT_TRAIN_DIR, file.replace('ltf','laf'))])
        ann_files.append(file.replace('ltf','laf'))
    return ann_files

# clear ltf directory for annotation
if os.path.exists(LAF_CURRENT_TRAIN_DIR):
    shutil.rmtree(LAF_CURRENT_TRAIN_DIR)
os.mkdir(LAF_CURRENT_TRAIN_DIR)

##################################
# DRIVER FUNCTION EXAMPLE
learner = ActiveLearning(WORKING_DIR, os.listdir(LTF_TRAIN_DIR), max_iter=5, init_size=20, max_size=100, batch_size=5,
                         select='select_entropy', verbose=True)

iteration_index = 0
while not learner.done():
    print '################## Current Iteration %d ##################' % iteration_index
    if not learner.current_train_set:
        annotated_files = annotate(learner.init_set())
        learner.retrain(annotated_files)
    else:
        files = learner.iterate() #LTF filename list to annotate
        print 'INFO: ITERATION COMPLETED'
        annotated_files = annotate(files) #LAF filename list from annotator to give to retrainer
        learner.retrain(annotated_files) #A list of LAF filenames to retrain with

    # evaluate on test set
    test_set = os.listdir(LTF_TEST_DIR)
    print 'INFO: Beginning Evaluating (%d sents)' % len(test_set)

    # *********** multiprocessing for evaluation *********** #
    n = int(math.ceil(len(test_set) / float(NUM_PROC)))
    args = [test_set[i:i+n] for i in xrange(0, len(test_set), n)]
    cmds = []
    for item in args:
        cmds.append([TAG, '-L', OUT_TEST_DIR, MODEL_DIR] +
                    [os.path.join(LTF_TEST_DIR, laf.replace('laf', 'ltf')) for laf in item])
    processes = [Popen(cmd) for cmd in cmds]
    for p in processes: p.wait()

    tab_fp = os.path.join(EVAL_DIR, 'eval_%d.tab' % iteration_index)
    cmd = ['python', 'script/laf2tab.py', OUT_TEST_DIR, tab_fp]
    subprocess.call(cmd)

    # correct tab file format
    corrected_result = []
    for line in io.open(tab_fp, 'r', -1, 'utf-8').read().splitlines():
        tmp = line.split('\t')[3].split(':')[0]
        doc_id = tmp.split('-')[0].replace('_segment', '')
        line = line.replace(tmp, doc_id)
        corrected_result.append(line)
    f = io.open(tab_fp, 'w', -1, 'utf-8')
    f.write('\n'.join(corrected_result))
    f.close()

    url = 'http://0.0.0.0:3300/elisa_ie/supported_language/hau/scorer?eval_docs=%s&eval_string=%s' \
          % ('|'.join([item.replace('.ltf.xml', '').split('_segment')[0] for item in test_set]),
             urllib2.quote('\n'.join(corrected_result).encode('utf-8')))
    eval_result = json.loads(urllib2.urlopen(url).read(), object_pairs_hook=OrderedDict)

    print '==> iteration %d performance' % iteration_index
    print '\n'.join(['\t'.join((item[0], str(item[1]))) for item in eval_result.items()])

    iteration_index += 1

    pass









