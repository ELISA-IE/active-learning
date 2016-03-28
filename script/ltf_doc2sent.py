#-*- coding: utf-8 -*-
import sys
import os
import io
import xml.etree.ElementTree as ET


def doc2sent(ltf_xml, laf_xml):
    # process ltf
    ltf_result = []
    ltf_root = ET.parse(ltf_xml)
    docid = ltf_root.find('DOC').get('id')
    ltf_head = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE LCTL_TEXT SYSTEM "ltf.v1.5.dtd">
<LCTL_TEXT>
<DOC id="%s">
<TEXT>
''' % docid
    ltf_tail = '''</TEXT>
</DOC>
</LCTL_TEXT>'''
    all_seg_ids = []
    for seg in ltf_root.find('DOC').find('TEXT').findall('SEG',):  # tag name should be lowercase
        seg_id = seg.get('id')
        offset_start = seg.get('start_char')
        offset_end = seg.get('end_char')
        sent_docid = '_'.join([docid, seg_id])
        ltf_result.append((ltf_head +
                           ET.tostring(seg, encoding='UTF-8').replace("<?xml version='1.0' encoding='UTF-8'?>\n", '') +
                           ltf_tail, sent_docid))
        all_seg_ids.append((sent_docid, offset_start, offset_end))

    # process laf
    laf_result = []
    laf_root = ET.parse(laf_xml)
    laf_empty = '''<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE LCTL_ANNOTATIONS SYSTEM "laf.v1.2.dtd">
<LCTL_ANNOTATIONS>
<DOC id="%s"/>
</LCTL_ANNOTATIONS>
'''
    laf_head = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE LCTL_ANNOTATIONS SYSTEM "laf.v1.2.dtd">
<LCTL_ANNOTATIONS>
<DOC id="%s">
'''
    laf_tail = '''</DOC>
</LCTL_ANNOTATIONS>'''
    for seg_id in all_seg_ids:
        anns = []
        offset_start = int(seg_id[1])
        offset_end = int(seg_id[2])
        for ann in laf_root.find('DOC').findall('ANNOTATION'):
            ann_start = int(ann.find('EXTENT').get('start_char'))
            ann_end = int(ann.find('EXTENT').get('end_char'))
            if ann_start >= offset_start and ann_end <= offset_end:
                anns.append(ann)
        if not anns:
            laf_result.append((laf_empty % seg_id[0], seg_id[0]))
        else:

            laf_result.append((laf_head % seg_id[0] +
                               ''.join([ET.tostring(a, encoding='UTF-8').replace("<?xml version='1.0' encoding='UTF-8'?>\n", '') for a in anns]) +
                               laf_tail, seg_id[0]))

    return ltf_result, laf_result

if __name__ == '__main__':
    # if len(sys.argv) != 5:
    #     print 'USAGE: python laf2tab.py <ltf_doc_dir> <ltf_output_dir> <laf_doc_dir> <laf_output_dir>'
    # else:
    #     ltf_indir = sys.argv[1]
    #     ltf_outdir = sys.argv[2]
    #     laf_indir = sys.argv[3]
    #     laf_outdir = sys.argv[4]

    ltf_indir = '../hau/ltf_doc'
    ltf_outdir = '../hau/ltf_sent'
    laf_indir = '../hau/laf_doc'
    laf_outdir = '../hau/laf_sent'

    for fn in os.listdir(ltf_indir):
        ltf_path = os.path.join(ltf_indir, fn)
        laf_path = os.path.join(laf_indir, fn.replace('ltf', 'laf'))
        ltf_sents, laf_sents = doc2sent(ltf_path, laf_path)
        for item in ltf_sents:
            f = io.open(os.path.join(ltf_outdir, item[1]+'.ltf.xml'), 'w', -1, 'utf-8')
            f.write(unicode(item[0], encoding='utf-8'))
            f.close()

        for item in laf_sents:
            f = io.open(os.path.join(laf_outdir, item[1]+'.laf.xml'), 'w', -1, 'utf-8')
            f.write(unicode(item[0], encoding='utf-8'))
            f.close()


