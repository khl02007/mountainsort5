import os
import time
from tempfile import TemporaryDirectory
import numpy as np
import spikeinterface.extractors as se
import spikeinterface.preprocessing as spre
import spikeinterface.comparison as sc
import mountainsort5 as ms5
from mountainsort5.util import create_cached_recording
from generate_visualization_output import generate_visualization_output
from spikeforest.load_spikeforest_recordings.SFRecording import SFRecording
import spikeinterface as si

def main():
    recording, sorting_true = se.toy_example(duration=60 * 2, num_channels=8, num_units=16, sampling_frequency=30000, num_segments=1, seed=0) # type: ignore
    recording: si.BaseRecording = recording
    sorting_true: si.BaseSorting = sorting_true

    timer = time.time()

    # lazy preprocessing
    recording_filtered = spre.bandpass_filter(recording, freq_min=300, freq_max=6000, dtype=np.float32)
    recording_preprocessed: si.BaseRecording = spre.whiten(recording_filtered)

    with TemporaryDirectory() as tmpdir:
        # cache the recording to a temporary directory for efficient reading
        recording_cached = create_cached_recording(recording_preprocessed, folder=tmpdir)

        # sorting
        print('Starting MountainSort5')
        sorting = ms5.sorting_scheme1(
            recording_cached,
            sorting_parameters=ms5.Scheme1SortingParameters()
        )

    elapsed_sec = time.time() - timer
    duration_sec = recording.get_total_duration()
    print(f'Elapsed time for sorting: {elapsed_sec:.2f} sec -- x{(duration_sec / elapsed_sec):.2f} speed compared with real time for {recording.get_num_channels()} channels')

    print('Comparing with truth')
    comparison = sc.compare_sorter_to_ground_truth(gt_sorting=sorting_true, tested_sorting=sorting)
    print(comparison.get_performance())

    #######################################################################

    if os.getenv('GENERATE_VISUALIZATION_OUTPUT') == '1':
        rec = SFRecording({
            'name': 'toy_example',
            'studyName': 'toy_example',
            'studySetName': 'toy_example',
            'sampleRateHz': recording_preprocessed.get_sampling_frequency(),
            'numChannels': recording_preprocessed.get_num_channels(),
            'durationSec': recording_preprocessed.get_total_duration(),
            'numTrueUnits': sorting_true.get_num_units(),
            'sortingTrueObject': {},
            'recordingObject': {}
        })
        generate_visualization_output(rec=rec, recording_preprocessed=recording_preprocessed, sorting=sorting, sorting_true=sorting_true)

if __name__ == '__main__':
    main()
