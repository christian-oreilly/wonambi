from pytest import approx, raises

from wonambi import Dataset
from wonambi.detect.spindle import DetectSpindle

from .paths import psg_file

d = Dataset(psg_file)
data = d.read_data(chan=('EEG Fpz-Cz', 'EEG Pz-Oz'), begtime=35790, endtime=35820)


def test_detect_spindle_Moelle2011():
    detsp = DetectSpindle()
    assert repr(detsp) == 'detsp_Moelle2011_11-18Hz_00.5-02.0s'

    sp = detsp(data)
    assert len(sp.events) == 3


def test_detect_spindle_Nir2011():
    detsp = DetectSpindle(method='Nir2011')

    sp = detsp(data)
    assert len(sp.events) == 2


def test_detect_spindle_Wamsley2012():
    detsp = DetectSpindle(method='Wamsley2012')

    sp = detsp(data)
    assert len(sp.events) == 1


def test_detect_spindle_Ferrarelli2007():
    detsp = DetectSpindle(method='Ferrarelli2007')

    sp = detsp(data)
    assert len(sp.events) == 0


def test_detect_spindle_unknownmethod():
    with raises(ValueError):
        detsp = DetectSpindle(method='xxx')


def test_detect_spindle_to_data():
    detsp = DetectSpindle()
    sp = detsp(data)

    sp_data = sp.to_data('count')
    assert sp_data(0)[0] == 2

    sp_freq = sp.to_data('peak_freq')
    assert approx(sp_freq(0)[0]) == 14.49166667

