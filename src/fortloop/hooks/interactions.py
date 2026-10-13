import networkx as nx
from fortloop import Hook
import py_fort_myrmidon as fm


class Collisions(Hook):
    def __init__(self, update_period_sec=0):
        super().__init__(update_period_sec)
        self.myrmidon = f_myrmidon
        self.graph = nx.Graph()
        
    def process_frame(self, collision):
        print(collisions)
        
        if frame.FrameTime - self.t_prev > self.p_update:
            self.t_prev = frame["timestamp"]
            # Collisions with a certain requirement are recorded as graph edge
            # Remove collisions from graph that are too old
            
        
    def store(self):
        pass

    def restore(self):
        pass



# class _Interactions(Hook):
#     def __init__(self, update_period_sec=0):
#         super().__init__(update_period_sec)
#         self.myrmidon = f_myrmidon
#         self.graph = nx.Graph()
        
#     def process_frame(self, frame):
#         # Process collisions
#         collisions = fm.
        
#         if frame.FrameTime - self.t_prev > self.p_update:
#             self.t_prev = frame["timestamp"]
#             # Collisions with a certain requirement are recorded as graph edge
#             # Remove collisions from graph that are too old            
        
#     def store(self):
#         pass

#     def restore(self):
#         pass


