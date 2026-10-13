from fortloop import Loop, Hook
from fortloop.hooks.liveplot import LivePlot
from mecom import MeCom  # Meerstetter TEC controller object
import sys
import logging

"""
IMPORTANT:
The following documents should be studied before extending the program below with hardware actions:

The user manual for Meerstetter TEC controllers can be found on:
    https://www.meerstetter.ch/customer-center/downloads/category/33-latest-user-manuals?download=4:tec-family-tec-controllers-user-manual
The MeCom communication protocol:
    https://www.meerstetter.ch/customer-center/downloads/category/35-latest-communication-protocols?download=6:tec-family-mecom-communication-protocol
The MeCom communication protocol specification:
    https://www.meerstetter.ch/customer-center/downloads/category/35-latest-communication-protocols?download=5:mecom-protocol-specification
"""


xmin, xmax = 1000, 6000
ymin, ymax = 1000, 5000
ystep = (ymax - ymin) / 4

zones = [
    [[xmin, ymin], [xmax, ymin], [xmax, ymin+ystep], [xmin, ymin+ystep]],
    [[xmin, ymin+ystep], [xmax, ymin+ystep], [xmax, ymin+2*ystep], [xmin, ymin+2*ystep]],
    [[xmin, ymin+2*ystep], [xmax, ymin+2*ystep], [xmax, ymin+3*ystep], [xmin, ymin+3*ystep]],
    [[xmin, ymin+3*ystep], [xmax, ymin+3*ystep], [xmax, ymin+4*ystep], [xmin, ymin+4*ystep]]
]


class TBMHook(Hook):
    def __init__(self, com_ports, tec_sn_zone, sample_period_sec=0):
        super().__init__(sample_period_sec)
        self.tec_sn_zone = tec_sn_zone
        self.tec_addr_sn = {}
        self.tec = None
        self.com_ports = com_ports
        self.p_sample = sample_period_sec

    def connect(self):
        if self.tec is None:
            self.tec = {}
            sn_connected = []
            for port in self.com_ports:
                try:
                    tec = MeCom(port)
                    address = tec.identify()
                    status = tec.status()
                    sn = tec.get_parameter(parameter_name="Device Serial Number", address=address)
                    self.tec_addr_sn[address] = sn
                    if sn not in self.tec_sn_zone:
                        logging.error("TEC decive {}, s/n: {} not in serial number list".format(address, sn))
                    else:
                        sn_connected.append(sn)
                        self.tec[address] = tec
                        logging.info("connected to TEC decive {}, s/n: {}, status: {}".format(address, sn, status))
                except Exception as e:
                    logging.error(e)
                    raise e
            # Check if all requested devices are found
            not_found = list(set(self.tec_sn_zone.keys()).difference(set(sn_connected)))
            for sn in  not_found:
                logging.error("TEC decive with s/n: {} not not found".format(sn))
        
    def process_frame(self, frame):
        if self.tec is None:
            self.connect()
        # Decide what action to take (e.g. increase temperature) based on the frame["positions"] and current temperature
        temp_threshold_celsius = 30.0
        temp_new_celsius = 20.0
        if frame["timestamp"] - self.t_prev > self.p_sample:
            self.t_prev = frame["timestamp"]
            for address in self.tec:
                temp_ch1 = self.tec[address].get_parameter(parameter_name="Object Temperature", address=address, parameter_instance=1)
                temp_ch2 = self.tec[address].get_parameter(parameter_name="Object Temperature", address=address, parameter_instance=2)
                logging.info("TEC {}, object temperature {}: {} C, {}: {} C".format(address,
                                                                                    self.tec_sn_zone[self.tec_addr_sn[address]][1], temp_ch1,
                                                                                    self.tec_sn_zone[self.tec_addr_sn[address]][2], temp_ch2))
                if temp_ch1 > temp_threshold_celsius:
                    # make sure the system is working correctly (cooling!) before
                    # removing the hashtag of the next line and starting to change temparature
                    success = True
                    # success = mc.set_parameter(value=temp_new_celsius, parameter_id=3000)
                    if success:
                        logging.info("TEC temparature set to {}".format(temp_new_celsius))
                    else:
                        logging.info("Failed to set TEC temparature to {}".format(temp_new_celsius))
        
    def store(self):
        if self.tec is not None:
            for address in self.tec:
                self.tec[address].stop()
                logging.info("closed connection to host {}".format(address))

    def restore(self):
        pass


logging.getLogger().setLevel(logging.INFO)

# Assign tec controller serial number and channel to zone
tec_sn_zone = {3368: {1: "zone 1", 2: "zone 2"},
               3371: {1: "zone 3", 2: "zone 4"}}

if len(sys.argv) != len(tec_sn_zone) + 1:
    raise RuntimeError("Must provide {} com ports".format(len(tec_sn_zone)))

f_hermes = "/home/matthias/Documents/experiments/la_manip_spring_2021/la_manip_16_03_2021.0000/tracking.0000.hermes"
liveplot = LivePlot(update_period_sec=1.0, polygons=zones)
tbm = TBMHook(sys.argv[1:], tec_sn_zone, sample_period_sec=5)
fortloop = Loop([tbm, liveplot])

# Simulate fortloop with pre-recorded data
f_hermes = sys.argv[1]
fortloop.simulate(f_hermes, simulate_period=0.2)

# Run retrieving data in realtime fro tracking host
host = sys.argv[1]
fortloop.run(host)
