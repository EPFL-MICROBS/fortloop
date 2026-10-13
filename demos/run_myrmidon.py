from fortloop import Loop, Hook
import py_fort_myrmidon as fm
import numpy as np
import logging
import sys


class MyrmidonHook(Hook):
    def __init__(self, sample_period_sec=0, log_filename=''):
        super().__init__(sample_period_sec)
        # Initialize container to aggregate tracking data if needed
        self.aggregated = None

    def process_frame(self, frame, collisions):
        # Aggregate, filter frames here if needed. This part of the function runs at full speed, i.e. at the tracking frequency
        self.aggregated = frame["positions"]
        # The following code is executed only at a frequency of approximately 1/sample_period_sec Hz.
        # Code taking action on hardware should be placed in here. Code placed before should not access hardware in order to run fast
        # to make sure that the tracking frame queue can be fully consumed to avoid that actions are taken based on updated data.
        if frame["timestamp"] - self.t_prev > self.p_sample:
            self.t_prev = frame["timestamp"]
            # Access hardware here
            logging.info("Processing frame at time {}".format(frame["timestamp"]))
        
    def store(self):
        # Terminate hardware connections here if neede.
        # The user can decide in what form the aggregated data or internal state of the hook will be saved.
        # <self.f_store()> should be used as filname as it is a full path to the timestamped file called <log_filename>
        np.save(self.f_store("empty_hook_state.npy"), self.aggregated)

    def restore(self):
        # If <self.f_store()> is used to save the file, <self.get_latest()> is picks the latest stored state automatically.
        f_latest = self.latest_state_file("empty_hook_state.npy")
        if f_latest is None:
            self.aggregated = None
        else:
            self.aggregated = np.load(f_latest)


logging.getLogger().setLevel(logging.INFO)

file_myrmidon = 'testdata/testdata.myrmidon'
example_hook = MyrmidonHook(sample_period_sec=2)
fortloop = Loop([example_hook], log_folder='', f_myrmidon=file_myrmidon)

# Simulate fortloop with pre-recorded data
f_hermes = sys.argv[1]
fortloop.simulate(f_hermes, simulate_period=0.2)

# Run retrieving data in realtime fro tracking host
host = sys.argv[1]
fortloop.run(host)
