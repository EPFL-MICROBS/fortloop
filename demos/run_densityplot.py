import sys
import logging
from fortloop import Loop
from fortloop.hooks.liveplot import DensityPlot

logging.getLogger().setLevel(logging.INFO)

# f_hermes = "/home/matthias/Documents/experiments/la_manip_spring_2021/la_manip_16_03_2021.0000/tracking.0000.hermes"

liveplot = DensityPlot(update_period_sec=1.0, memory_sec=10, highlight_ids=["0x07b"], mask_ids=["0x07b"], window_size=14)
fortloop = Loop([liveplot])

# Simulate fortloop with pre-recorded data
f_hermes = sys.argv[1]
fortloop.simulate(f_hermes, simulate_period=0.2)

# Run retrieving data in realtime fro tracking host
host = sys.argv[1]
fortloop.run(host)
