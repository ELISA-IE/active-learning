import io
import os
import shutil

test_file_ids = [item.replace('.ltf.xml', '') for item in open('test_filelist').read().splitlines()]

for fn in os.listdir('laf_sent'):
	if any(item in fn for item in test_file_ids):
		shutil.copyfile('laf_sent/'+fn, 'laf_test/'+fn)
	else:
		shutil.copyfile('laf_sent/'+fn, 'laf_train/'+fn)

for fn in os.listdir('ltf_sent'):
	if any(item in fn for item in test_file_ids):
		shutil.copyfile('ltf_sent/'+fn, 'ltf_test/'+fn)
	else:
		shutil.copyfile('ltf_sent/'+fn, 'ltf_train/'+fn)