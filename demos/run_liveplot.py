import sys
from os.path import join, expanduser
import logging
from fortloop import Loop
from fortloop.hooks.liveplot import LivePlot

logging.getLogger().setLevel(logging.INFO)

HOME = expanduser("~")
f_hermes = join(HOME, "Documents/experiments/la_manip_spring_2021/la_manip_15_02_2021.0001/tracking.0000.hermes")
f_myrmidon = join(HOME, "Documents/myrmidons/la_manip_15_02_2021.myrmidon")

liveplot = LivePlot(update_period_sec=1.0)
# fortloop = Loop([liveplot])
# fortloop = Loop([liveplot], f_myrmidon=f_myrmidon)
fortloop = Loop([liveplot], f_myrmidon_f=f_myrmidon)

# Simulate fortloop with pre-recorded data
# f_hermes = sys.argv[1]
# fortloop.simulate(f_hermes, simulate_period=1.0/8, zone_id=1)

# Simulate fortloop with pre-recorded data
# f_hermes = sys.argv[1]
host = 'highgarden'
fortloop.dryrun(host, f_hermes, zone_id=1)

# Run retrieving data in realtime fro tracking host
# host = sys.argv[1]
# fortloop.run(host, zone_id=0)
