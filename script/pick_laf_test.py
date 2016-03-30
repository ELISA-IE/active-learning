import io
import os
import shutil
import sys


def pick_laf_test(workspace):
    test_file_ids = [item.replace('.ltf.xml', '') for item in open(os.path.join(workspace, 'test_filelist')).read().splitlines()]

    ltf_sent_path = os.listdir(os.path.join(workspace, 'ltf_sent'))
    for fn in ltf_sent_path:
        fn_full_path = os.path.join(workspace, 'ltf_sent', fn)
        ltf_test_fn = os.path.join(workspace, 'ltf_test', fn)
        ltf_train_fn = os.path.join(workspace, 'ltf_train', fn)
        if any(item in fn for item in test_file_ids):
            shutil.copyfile(fn_full_path, ltf_test_fn)
        else:
            shutil.copyfile(fn_full_path, ltf_train_fn)

    laf_sent_path = os.listdir(os.path.join(workspace, 'laf_sent'))
    for fn in laf_sent_path:
        fn_full_path = os.path.join(workspace, 'laf_sent', fn)
        laf_test_fn = os.path.join(workspace, 'laf_test', fn)
        laf_train_fn = os.path.join(workspace, 'laf_train', fn)
        if any(item in fn for item in test_file_ids):
            shutil.copyfile(fn_full_path, laf_test_fn)
        else:
            shutil.copyfile(fn_full_path, laf_train_fn)




if __name__ == "__main__":
    if len(sys.argv) != 2:
        print 'USAGE: python pick_laf_test.py <workspace>'
    else:
        workspace = sys.argv[1]
        pick_laf_test(workspace)
