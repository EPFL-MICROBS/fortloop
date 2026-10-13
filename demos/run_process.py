import sys
from os.path import join, expanduser
import logging
import time
from fortloop import Loop, Process
from fortloop.hooks.liveplot import LivePlot


class SimpleProcess(Process):
    def __init__(self, f_loop):
        super().__init__(has_queue=True)
        self.t = time.perf_counter()
        self.p_loop = 1.0/f_loop

    def loop(self, frame, collisions):
        t = time.perf_counter()
        dt = t - self.t
        if frame is None:
            if dt >= self.p_loop:
                self.t = t
                logging.info("no frame received by process 1: dt={}".format(dt))
        else:
            logging.info("process 1 received frame: dt={}, frame ts={}".format(dt, frame['timestamp']))


class SimpleProcessNoFrames(Process):
    def __init__(self, f_loop):
        super().__init__(has_queue=False)
        self.t = time.perf_counter()
        self.p_loop = 1.0/f_loop

    def loop(self, frame, collisions):
        t = time.perf_counter()
        dt = t - self.t
        if frame is None:
            if dt >= self.p_loop:
                self.t = t
                logging.info("no frame received by process 2: dt={}".format(dt))
        else:
            logging.info("process 2 received frame: dt={}, frame ts={}".format(dt, frame['timestamp']))


logging.getLogger().setLevel(logging.INFO)

HOME = expanduser("~")
f_hermes = join(HOME, "Documents/experiments/la_manip_spring_2021/la_manip_15_02_2021.0001/tracking.0000.hermes")
f_myrmidon = join(HOME, "Documents/la_manip_analysis/la_manip_15_02_2021.myrmidon")

liveplot = LivePlot(update_period_sec=1.0)
simple_process_wf = SimpleProcess(f_loop=20)
simple_process_wof = SimpleProcessNoFrames(f_loop=20)
fortloop = Loop(hooks=[liveplot], processes=[simple_process_wf, simple_process_wof], f_myrmidon=f_myrmidon)

# Simulate fortloop with pre-recorded data
fortloop.simulate(f_hermes, simulate_period=1.0/8, zone_id=1)

# Simulate fortloop with pre-recorded data
# f_hermes = sys.argv[1]
# fortloop.dryrun(host, f_hermes, zone_id=1)

# Run retrieving data in realtime fro tracking host
# host = sys.argv[1]
# fortloop.run(host, zone_id=0)
