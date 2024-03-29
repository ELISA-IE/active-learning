#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'jfrei86'
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
import sys
from bs4 import BeautifulSoup
import multiprocessing as mp
from subprocess import Popen
from itertools import repeat

#GLOBAL VARIABLES (MODIFY MODULE AS NEEDED)

FS = '/'
NUM_PROC = 2
WORKING_DIR = './hau'
PROBS_DIR = os.path.join(WORKING_DIR,'probs')
MODEL_DIR = os.path.join(WORKING_DIR,'model')
LAF_DIR = os.path.join(WORKING_DIR,'laf')
LTF_DIR = os.path.join(WORKING_DIR,'ltf')
OUT_DIR = os.path.join(WORKING_DIR,'output')
TRAIN = './src/name_tagger/train.py'
TAG = './src/name_tagger/tagger.py'

class ActiveLearning(object):


	# Args:
	## working_dir - Working Directory for active learner
	## unlabeled_data - A list of filenames in the LTF_DIR to select and label
	## max_iter - The Maximum numer of iterations
	## init_size - The initial sample size for training
	## max_size - The maximum number of samples used for training
	## batch_size - The numer of samples per iteration
	## select - The selection mode. Default mode entropy
	## verbose - Debugging purposes
	def __init__(self, working_dir=None, unlabeled_data=[], max_iter=50, 
		init_size=50, max_size=100, batch_size=5, select='select_entropy', verbose=False):

		if not working_dir == None:
			WORKING_DIR = working_dir

		if not os.path.exists(WORKING_DIR):
			print "ERROR: Working directory not found."
			exit()

		#UNLABELED DATA (LTF FILES)
		self.train_set = set(unlabeled_data)

		if verbose:
			print "INFO: Unlabeled data: " + str(len(unlabeled_data))

		self.frequency = dict()
		sum = 0.0
		for f in self.train_set:
			try:
				contents = open(os.path.join(LTF_DIR,f)).read()
			except IOError:
				print "ERROR: Skipping training file (not found): " + f
				continue
			soup = BeautifulSoup(contents, 'html.parser')
			for token in soup.find_all('token'):
				tmp = token.string
				if tmp in self.frequency.keys():
					self.frequency[tmp] = self.frequency.get(tmp) + 1
				else:
					self.frequency[tmp] = 1
				sum += 1
		self.frequency.update((k, v / sum) for (k, v) in self.frequency.iteritems())  # get frequency of every word

		f_fre = codecs.open(os.path.join(WORKING_DIR, 'frequency.txt'), 'w', encoding='utf-8')  # take down the frequency to debug
		for key in self.frequency.keys():
			f_fre.write(key+'\t'+str(self.frequency.get(key))+'\n')
		f_fre.close()

		self.max_train_sentences = int(max_size)
		self.max_iter = int(max_iter)
		self.increment = int(batch_size)
		self.verbose = verbose
		self.mode = select
		self.iter_num = 0
		self.init_size = init_size
		self.max_size = max_size

		#COMMANDS FOR MODEL PROCESSING
		self.cmd_del_model = ['rm', '-r', MODEL_DIR]
		self.cmd_del_syslaf = ['rm', '-r', OUT_DIR]
		self.cmd_mk_syslaf = ['mkdir', OUT_DIR]
		self.cmd_del_probs = ['rm', '-r', PROBS_DIR]
		self.cmd_mk_probs = ['mkdir', PROBS_DIR]

		#BEGINNING DATA (LAF FILES)
		self.init_train_set = set()
		self.current_train_set = set()

	def init_set(self):
		return self.select_random(self.init_size, LTF_DIR)

	def select(self, size):
		if self.mode == 'select_entropy':
			return self.select_entropy(size)
		if self.mode == 'select_random':
			return self.select_random(size)
		if self.mode == 'select_sequential':
			return self.select_sequential(size)
		if self.mode == 'select_info_div':
			return self.select_info_div(size)



	def select_entropy(self, size):
		if self.verbose:
			print 'INFO: Selecting', size, 'sentences via entropy'

		all_file = os.listdir(PROBS_DIR)

		prob_mul_list = [[]]
		len_chunk = len(all_file)/NUM_PROC
		for i in range(NUM_PROC):
			prob_mul_list.append(all_file[i*len_chunk:(i+1)*len_chunk])
		if (i+1)*len_chunk < len(all_file):
			prob_mul_list.append(all_file[(i+1)*len_chunk:])
		prob_mul_list.pop(0)

		pool = mp.Pool(processes=NUM_PROC)
		results = pool.map(prob_score, zip(repeat(PROBS_DIR), prob_mul_list))

		pool.close()
		pool.join()
		sum_TK = results[0].copy()
		for item in results[1:]:
			sum_TK.update(item)

		sorted_entropy = sorted(sum_TK.items(), key=operator.itemgetter(1), reverse=True)
		############################################

		training_set_to_add = []
		sample_size = size if len(sorted_entropy) >= size else len(sorted_entropy)

		for item in sorted_entropy[:sample_size]:
			sent_doc = item
			sent_doc_xml = sent_doc.replace('probs', 'laf')
			if sent_doc_xml not in self.current_train_set:
				training_set_to_add.append(sent_doc_xml)

		return training_set_to_add

	def select_random(self, size, dir):
		if self.verbose:
			print 'INFO: Randomly selecting', size, 'sentences'
		training_set_to_add = []
		sub = len(self.train_set) - len(self.current_train_set)

		if sub < size:
			sample_size = sub

		candidates = list(set(os.listdir(dir)) - self.current_train_set)

		while len(training_set_to_add) < size:
			temp = random.randint(0, (len(candidates) - 1))
			training_set_to_add.append(candidates[temp])

		return set(training_set_to_add)

	def select_info_div(self, size):
		pass

	def retrain(self, annotated_files):
		subprocess.call(self.cmd_del_model)
		self.current_train_set.update(annotated_files)
		print annotated_files
		train_list = [os.path.join(LAF_DIR, file) for file in self.current_train_set] # get the name list of training set

		if self.verbose:
			print 'INFO: Beginning Training'

		train_command = [TRAIN, MODEL_DIR, os.path.join(WORKING_DIR, 'frequency.txt'), LTF_DIR] + train_list

		subprocess.call(train_command)
		subprocess.call(self.cmd_del_syslaf)
		subprocess.call(self.cmd_mk_syslaf)
		subprocess.call(self.cmd_del_probs)
		subprocess.call(self.cmd_mk_probs)

		if self.verbose:
			print 'INFO: Training Completed'
			print 'INFO: Beginning Tagging'

		test_set = list(self.train_set - self.current_train_set)
		tag_mul_list = [[]]
		len_chunk = len(test_set)/NUM_PROC
		for i in range(NUM_PROC):
			tag_mul_list.append(test_set[i*len_chunk:(i+1)*len_chunk])
		if (i+1)*len_chunk < len(test_set):
			tag_mul_list.append(test_set[(i+1)*len_chunk:])
		tag_mul_list.pop(0)
		cmds = [[]]
		for item in tag_mul_list:
			cmds.append([TAG, '-L', OUT_DIR, MODEL_DIR] + item)
		cmds.pop(0)
		processes = [Popen(cmd) for cmd in cmds]
		for p in processes: p.wait()

		if self.verbose:
			print 'INFO: Finished Tagging'

	def done(self):
		if self.iter_num >= self.max_iter or len(self.current_train_set) >= self.max_size:
			return True
		return False

	def iterate(self):
		self.iter_num += 1
		selection = self.select(self.increment)
		return selection

# END ACTIVE LEARNING CLASS


def prob_score((probs_dir, file_list)):
    print 'calculating prob score in every file...'
    print probs_dir
    pattern1 = re.compile(r'(.*):(.*)')
    pattern2 = re.compile(r'\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s')
    sum_score = dict()
    for item in file_list:
        flag_num = 0
        entropy_num = 0
        f = codecs.open(probs_dir +'/'+item, 'r', encoding='utf-8')
        for line in f.readlines():
            m1 = re.match(pattern1, line, flags=0)
            if not m1 is None:
                if len(m1.group(1)) > 2:
                    flag_num += 1
                m2 = re.match(pattern2, m1.group(2), flags=0)
                if m2 is None:
                    print 'something wrong in probs file cause if m1 is not none then m2 is not none'
                entropy = 0
                for i in range(1, 18):
                    tmp = float(m2.group(i))
                    if tmp > 0:
                        entropy += -(tmp * math.log(tmp))
                if entropy > math.pow(1, -21):
                    entropy_num += 1
            else:
                pass
                # print line
        sum_score[item] = entropy_num + flag_num
        f.close()
    print 'finish calculate score'
    return sum_score

##########
# run CRFs training
# select new unlabeled_data


##################################
# DRIVER FUNCTION EXAMPLE
# learner = ActiveLearning(...)
# annotated_files = annotate(learner.init_set())
# learner.retrain(annotated_files)
# while not learner.done():
#	 files = learner.iterate() #LTF filename list to annotate
#	 annotated_files = annotate(files) #LAF filename list from annotator to give to retrainer
#	 learner.retrain(annotated_files) #A list of LAF filenames to retrain with