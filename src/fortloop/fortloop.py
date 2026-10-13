import logging
import time
from glob import glob
from os.path import join, basename
import multiprocessing as mp
import queue
import numpy as np
import py_fort_hermes as fh
# import py_fort_myrmidon as fm


class _StateManager:
    # managing the way state representations of child classes are
    # named, stored and loaded
    def __init__(self):
        self.dir_log = ''
        
    def latest_state_file(self, filename):
        f_candidates = glob(join(self.dir_log, "*{}".format(filename)))
        epoch_latest = 0
        f_latest = None
        for f in f_candidates:
            fname = basename(f)
            epoch = float(fname.split('_')[0])
            if epoch > epoch_latest:
                epoch_latest = epoch
                f_latest = f
        return f_latest

    def f_store(self, filename):
        return join(self.dir_log, "{}_{}".format(time.time(), filename))


class Hook(_StateManager):
    def __init__(self, p_sample):
        super().__init__()
        self.queue = mp.Queue()
        self.t_prev = 0
        self.p_sample = p_sample
    
    def process_frame(self, frame, collisions):
        pass

    def _run(self):
        self.restore()
        while True:
            tf = self.queue.get()
            while not self.queue.empty():
                tf = self.queue.get()
            if tf is None:
                logging.info("terminate fortloop hook {}".format(self))
                break
            else:
                try:
                    self.process_frame(*tf)
                except Exception as e:
                    self.store()
                    raise e
        self.store()
    
    def store(self, filename=""):
        pass

    def restore(self, filename=""):
        pass


class Process(_StateManager):
    def __init__(self, has_queue=False):
        super().__init__()
        if has_queue:
            self.queue = mp.Queue()
        else:
            self.queue = None
        self.terminate = mp.Event()
        self.terminate.clear()
    
    def loop(self, frame, collisions):
        # Loop can receive None, if queue was empty
        pass

    def _run(self):
        self.restore()
        while not self.terminate.is_set():
            if self.queue is None:
                try:
                    self.loop(None, None)
                except Exception as e:
                    self.store()
                    raise e
            else:
                try:
                    tf = self.queue.get_nowait()
                    while not self.queue.empty():
                        tf = self.queue.get()
                    if tf is None:
                        self.terminate.set()
                    else:
                        try:
                            self.loop(*tf)
                        except Exception as e:
                            self.store()
                            raise e
                except queue.Empty:
                    try:
                        self.loop(None, None)
                    except Exception as e:
                        self.store()
                        raise e
        logging.info("terminate fortloop process {}".format(self))
        self.store()
    
    def store(self, filename=""):
        pass

    def restore(self, filename=""):
        pass


def readout_to_dict(ro, space_id):
    t_epoch = ro.time.seconds + ro.time.nanos / 1e9
    positions = np.empty((len(ro.tags), 5))
    for i, tag in enumerate(ro.tags):
        positions[i] = [tag.ID, tag.x, tag.y, tag.theta, space_id]
    return {"timestamp": t_epoch, "positions": positions, "xmax": ro.width, "ymax": ro.height}


def identifiedframe_to_dict(frame):
    t_epoch = frame.FrameTime.ToTimestamp()
    return {"timestamp": t_epoch, "positions": frame.Positions, "xmax": frame.Width, "ymax": frame.Height}


def process_readout(ro, space_id, tracking_solver=None):
    d_collisions = {"IDs": [], "types": [], "zone": space_id}
    if tracking_solver is not None:
        frame = tracking_solver.IdentifyFrame(ro, space_id)
        c_frame = tracking_solver.CollideFrame(frame)
        ids = [c.IDs for c in c_frame.Collisions]
        types = [c.Types.tolist() for c in c_frame.Collisions]
        zone = [c.Zone for c in c_frame.Collisions]
        d_collisions["IDs"] = ids
        d_collisions["types"] = types
        d_collisions["zone"] = zone
        res = identifiedframe_to_dict(frame)
        res["identified"] = True
    else:
        res = readout_to_dict(ro, space_id)
        res["identified"] = False
    return res, d_collisions


class Loop:
    def __init__(self, hooks=[], processes=[], log_folder='', f_myrmidon=None, f_myrmidon_f=None, detection_memory_sec=0):
        # hooks are looped when fort data is available
        # loops are independent processes (e.g. for the controller)
        # f_myrmidon_f: secondary myrmidon for file stream if both streams are read
        self.l_hooks = hooks
        self.l_process = processes
        self.dir_log = log_folder
        self.memory_sec = detection_memory_sec
        self.frame_m = np.empty((0, 6))  # [id, x, y, theta, space, timestamp]
        if f_myrmidon is not None:
            exp = fm.Experiment.OpenDataLess(f_myrmidon)
            self.tracking_solver = exp.CompileTrackingSolver()
            logging.info("reading data from experiment: {} ({})".format(exp.Name, f_myrmidon))
        else:
            self.tracking_solver = None
        if f_myrmidon_f is not None:
            exp = fm.Experiment.OpenDataLess(f_myrmidon_f)
            self.tracking_solver_f = exp.CompileTrackingSolver()
            logging.info("reading secondary data from experiment: {} ({})".format(exp.Name, f_myrmidon_f))
        else:
            self.tracking_solver_f = None
        for h in self.l_hooks + self.l_process:
            h.dir_log = self.dir_log

    def _time_filter_frame(self, frame):
        # Overwrite known detections and append first detections
        # to keep a detection memory over the time horizon self.memory_sec
        frame_ts = np.hstack([frame["positions"],
                              frame["timestamp"] * np.ones((frame["positions"].shape[0], 1))])
        if self.frame_m.shape[0] == 0:
            self.frame_m = np.sort(frame_ts, axis=0)
        else:
            idx = np.searchsorted(self.frame_m[:, 0], frame_ts[:, 0])
            self.frame_m[idx[idx<self.frame_m.shape[0]]] = frame_ts[idx<self.frame_m.shape[0]]
            self.frame_m = np.concatenate([self.frame_m, frame_ts[idx==self.frame_m.shape[0]]])
        frame["positions"] = self.frame_m[self.frame_m[:, -1] >= frame["timestamp"] - self.memory_sec, :-1]
        return frame

    def _broadcast_readout(self, stream, space_id, terminate, period=0, xshift=0, yshift=0, scaling=1.0):
        for ro in stream:
            if terminate.is_set():
                for proc in self.l_hooks + self.l_process:
                    if proc.queue is not None:
                        proc.queue.put(None)
                break
            else:
                frame, collisions = process_readout(ro, space_id, self.tracking_solver)
                frame = self._time_filter_frame(frame)
                frame["positions"][:, 1] += xshift
                frame["positions"][:, 2] += yshift
                frame["positions"][:, 1:3] *= scaling
                for proc in self.l_hooks + self.l_process:
                    if proc.queue is not None:
                        proc.queue.put((frame, collisions))
            if period >= 0:
                time.sleep(period)

    def _read_network_stream(self, hostname, space_id, terminate):
        with fh.network.connect(hostname + '.local') as stream:
            logging.info("connected to host {}".format(hostname))
            self._broadcast_readout(stream, space_id, terminate)
        logging.info("connection on {} terminated".format(hostname))

    def _read_file_stream(self, filename, space_id, period_sec, xshift, yshift, scaling, terminate):
        with fh.file.open(filename) as stream:
            logging.info("reading stream from file {}".format(filename))
            self._broadcast_readout(stream, space_id, terminate, period=period_sec, xshift=xshift, yshift=yshift, scaling=scaling)
        logging.info("file stream from {} terminated".format(filename))

    def _read_both_streams(self, hostname, filename, space_id, xshift, yshift, scaling, terminate):
        f_stream = fh.file.open(filename)
        with fh.network.connect(hostname + '.local') as stream:
            logging.info("connected to host {} and opened file stream {}".format(hostname, filename))
            for nw_ro in stream:
                f_ro = next(f_stream)
                if terminate.is_set():
                    for proc in self.l_hooks + self.l_process:
                        if proc.queue is not None:
                            proc.queue.put(None)
                    break
                else:
                    # Collisions from network stream are ignored
                    frame, _ = process_readout(nw_ro, space_id, self.tracking_solver)
                    frame_f, collisions_f = process_readout(f_ro, space_id, self.tracking_solver_f)
                    frame_f = self._time_filter_frame(frame_f)
                    frame_f['positions'][:, 1] += xshift
                    frame_f['positions'][:, 2] += yshift
                    frame_f['positions'][:, 1:3] *= scaling
                    frame['positions'] = np.concatenate((frame_f['positions'], frame['positions']))
                    frame['positions'][frame_f['positions'].shape[0]:, 0] *= 1000  # Network ant or tag ids are distinguished to avoid amiguities
                    frame['timestamp_file'] = frame_f['timestamp']
                    if frame_f["identified"]:
                        frame["identified"] = True
                    for proc in self.l_hooks + self.l_process:
                        if proc.queue is not None:
                            proc.queue.put((frame, collisions_f))
                    
        f_stream.close()
        logging.info("connection on {} and file stream {} terminated".format(hostname, filename))

    def _run(self, data_stream_proc, *data_stream_args):
        with mp.Manager() as manager:
            terminate = mp.Event()
            terminate.clear()
            p_sr = mp.Process(target=data_stream_proc, args=data_stream_args + (terminate,))
            l_proc = [mp.Process(target=proc._run, args=()) for proc in self.l_hooks + self.l_process]
            p_sr.start()
            for p in l_proc:
                p.start()
            input("ready, press <q> + <Enter> to end program\n")
            terminate.set()
            for proc in self.l_process:
                proc.terminate.set()
            p_sr.join()
            for p in l_proc:
                p.join()
        logging.info("fortlive terminated")

    def run(self, hostname, zone_id=1):
        self._run(self._read_network_stream, hostname, zone_id)

    def dryrun(self, hostname, f_hermes, zone_id=1, xshift=0, yshift=0, scaling=1.0):
        self._run(self._read_both_streams, hostname, f_hermes, zone_id, xshift, yshift, scaling)

    def simulate(self, f_hermes, simulate_period=1.0, zone_id=1, xshift=0, yshift=0, scaling=1.0):
        self._run(self._read_file_stream, f_hermes, zone_id, simulate_period, xshift, yshift, scaling)
