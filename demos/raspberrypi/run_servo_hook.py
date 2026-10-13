import sys
import logging
import socket
import numpy as np
from shapely.geometry import Polygon, Point
from fortloop import Loop, Hook
from fortloop.hooks.liveplot import LivePlot


PORT = 4017

# Basic example for a Raspberry Pi communication accorid to a condition detected
# in a tracking frame
class RPiServoHook(Hook):
    def __init__(self, rpi_ip, red_zone, focal_antid, sample_period_sec=0):
        super().__init__(sample_period_sec)
        self.host = rpi_ip
        self.s = None
        self.red_zone = Polygon(red_zone)
        self.focal_antid = int(focal_antid, 16)
        self.door_open = True

    def connect(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.host, PORT))
        logging.info("connected to host " + self.host)
        
    def process_frame(self, frame):
        # close the door if an ant goes inside the red zone and open it if it leaves it again
        if frame["timestamp"] - self.t_prev > self.p_sample:
            self.t_prev = frame["timestamp"]
            crds = frame["positions"][frame["positions"][:, 0] == self.focal_antid]
            if len(crds) > 0:
                if self.red_zone.contains(Point(crds[0, 1:3])) and self.door_open:
                    self.s.send("rotate positive".encode('utf-8'))
                    self.door_open = False
                elif not self.red_zone.contains(Point(crds[0, 1:3])) and not self.door_open:
                    self.s.send("rotate negative".encode('utf-8'))
                    self.door_open = True
        
    def store(self):
        self.s.send("shutdown".encode('utf-8'))
        rep = self.s.recv(1024)
        self.s.close()
        logging.info("closed connection to host " + self.host)

    def restore(self):
        pass


nest = [[100, 1000],
        [6000, 1000],
        [6000, 5000],
        [100, 5000]]
zone = [[5500, 4500],
        [6000, 4500],
        [6000, 5000],
        [5500, 5000]]

liveplot = LivePlot(update_period_sec=1.0, polygons=[nest, zone], highlite_tags=['0x09b'])
rpiservo = RPiServoHook("130.223.51.229", zone, '0x9b', 1.0)
rpiservo.connect()
fortloop = Loop([rpiservo, liveplot])

# Simulate fortloop with pre-recorded data
f_hermes = sys.argv[1]
fortloop.simulate(f_hermes, simulate_period=0.2)

# Run retrieving data in realtime fro tracking host
host = sys.argv[1]
fortloop.run(host)
