
from mne_bids import BIDSPath, write_raw_bids
import mne

bids_path = BIDSPath(subject='test', task='mytask', run=1)
print(bids_path)