"""
tracker_test.py

utility to test real-time tracking with py_fort_hermes

Travis Allen
EPFL STI IGM MICROBS
10.2026
"""
import logging
from fortloop import Loop, Hook

logging.getLogger().setLevel(logging.INFO)

class CoordinateExtractor(Hook):
    def __init__(self, sample_period_sec=0):
        super().__init__(sample_period_sec)

    def process_frame(self, frame, collisions):
        timestamp = frame["timestamp"]

        for pos in frame["positions"]:
            tag_id = pos[0]
            x = pos[1]
            y = pos[2]
            theta = pos[3]

            print(f'Time: {timestamp:.2f} | ID: {tag_id} | X: {x:.2f} | Y: {y:.2f} | angle: {theta:.2f}')

def main():
    hook = CoordinateExtractor(sample_period_sec=0)
    fortloop = Loop(hooks=[hook])
    host = 'esterhase'
    fortloop.run(host)

if __name__ == "__main__":
    main()