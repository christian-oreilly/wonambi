from . import *

from os import makedirs
from os.path import join, dirname
from shutil import copyfile
from tempfile import mkdtemp

from phypno.attr import Annotations

tempdir = mkdtemp()

old_scores_file = join(data_dir, 'MGXX/doc/scores',
                       'MGXX_eeg_xltek_sessA_d03_06_38_05_scores_v3.xml')
toupdate_scores_file = join(tempdir,
                            'MGXX_eeg_xltek_sessA_d03_06_38_05_scores_v3.xml')
copyfile(old_scores_file, toupdate_scores_file)

scores_file = join(data_dir, 'MGXX/doc/scores',
                   'MGXX_eeg_xltek_sessA_d03_06_38_05_scores.xml')
temp_scores_file = join(tempdir, 'MGXX/doc/scores',
                        'MGXX_eeg_xltek_sessA_d03_06_38_05_scores.xml')

annot = Annotations(scores_file)


def test_update_version():
    lg.info('---\nfunction: ' + stack()[0][3])

    annot_old = Annotations(toupdate_scores_file)
    assert annot_old.root.get('version') == '5'


def test_get_epochs():
    lg.info('---\nfunction: ' + stack()[0][3])

    annot.set_stage_for_epoch(30, 'NREM1')

    # implementation details
    assert sum(1 for x in annot.epochs) == 159

    epochs = sorted(annot.epochs, key=lambda x: x['start'])
    assert epochs[1]['stage'] == 'NREM1'


def test_scores_01():
    lg.info('---\nfunction: ' + stack()[0][3])

    assert annot.current_rater == 'gio'
    annot.set_stage_for_epoch(30, 'NREM2')
    assert annot.get_stage_for_epoch(30) == 'NREM2'


@raises(KeyError)
def test_scores_02():
    lg.info('---\nfunction: ' + stack()[0][3])

    annot.set_stage_for_epoch(999, 'NREM2')
