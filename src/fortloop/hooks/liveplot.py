from tkinter import Tk, Canvas
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.pyplot import cm
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import json
from scipy.stats import kde
from fortloop import Hook


class LivePlot(Hook):
    def __init__(self, update_period_sec=0, polygons=[], highlight_ids=[], mask_ids=[], window_size=6):
        super().__init__(update_period_sec)
        self.root = None
        self.figure = None
        self.ax = None
        self.canvas = None
        self.polygons = polygons
        self.colors = np.random.rand(len(polygons), 3)
        self.h_ids = [int(idhex, 16) if isinstance(idhex, str) else idhex for idhex in highlight_ids]
        self.m_ids = [int(idhex, 16) if isinstance(idhex, str) else idhex for idhex in mask_ids]
        self.t_prev = 0
        self.win_sz = window_size

    def set_window(self):
        self.root = Tk()
        self.root.title("FORTloop live plot")
        self.root.protocol("WM_DELETE_WINDOW", exit)  # Disable close button
        self.figure = Figure(figsize=(self.win_sz, self.win_sz), dpi=100)
        self.ax = self.figure.add_subplot()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvas.get_tk_widget().pack()
        
    def process_frame(self, frame, collisions):
        if self.root is None:
            self.set_window()
        self.ax.clear()
        if frame["timestamp"] - self.t_prev > self.p_sample:
            self.t_prev = frame["timestamp"]
            for p, poly in enumerate(self.polygons):
                for i in range(len(poly)):
                    j = (i+1) % len(poly)
                    self.ax.plot([poly[i][0], poly[j][0]],
                                 [poly[i][1], poly[j][1]],
                                 linestyle='--', color=self.colors[p])
            for i, pos in enumerate(frame["positions"]):
                if pos[0] in self.h_ids:
                    self.ax.plot(pos[1], pos[2], color='g', marker='.')
                elif pos[0] not in self.m_ids:
                    self.ax.plot(pos[1], pos[2], color='k', marker='.')
                len_arrow = 100
                self.ax.arrow(pos[1], pos[2], len_arrow*np.cos(pos[3]), len_arrow*np.sin(pos[3]), color='r')
                if frame["identified"]:
                    self.ax.text(pos[1], pos[2], str(int(pos[0])), fontdict=dict(color='k'))
                else:
                    self.ax.text(pos[1], pos[2], str(hex(int(pos[0]))), fontdict=dict(color='k'))
            self.custom_plot(self.ax, frame)
            self.ax.set_xlim([0, frame["xmax"]])
            self.ax.set_ylim([0, frame["ymax"]])
            self.ax.set_title("timestamp: {0:.2f} sec".format(frame["timestamp"]))
            self.ax.invert_yaxis()  # camera coordinates
            self.ax.set_aspect('equal')
            self.canvas.draw()
            self.canvas.get_tk_widget().pack()
            self.root.update()

    def custom_plot(self, ax, frame):
        # Put customized plotting code here
        pass

    def custom_store(self):
        pass
            
    def store(self):
        self.root.destroy()
        self.custom_store()

    def restore(self):
        pass


class DensityPlot(Hook):
    def __init__(self, update_period_sec=0, polygons=[], highlight_ids=[], mask_ids=[], memory_sec=np.inf, window_size=6):
        super().__init__(update_period_sec)
        self.root = None
        self.figure = None
        self.ax = None
        self.canvas = None
        self.polygons = polygons
        self.colors = np.random.rand(len(polygons), 3)
        self.h_ids = [int(idhex, 16) if isinstance(idhex, str) else idhex for idhex in highlight_ids]
        self.m_ids = [int(idhex, 16) if isinstance(idhex, str) else idhex for idhex in mask_ids]
        self.t_prev = 0
        self.pos_memory = {}
        self.memory_sec = memory_sec
        self.win_sz = window_size

    def set_window(self):
        self.root = Tk()
        self.root.title("FORTloop live density plot")
        self.root.protocol("WM_DELETE_WINDOW", exit)  # Disable close button
        self.figure = Figure(figsize=(self.win_sz, self.win_sz), dpi=100)
        self.ax = self.figure.add_subplot()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvas.get_tk_widget().pack()
        
    def process_frame(self, frame, collisions):
        if self.root is None:
            self.set_window()
        for pos in frame["positions"]:
            self.pos_memory[pos[0]] = {"x": pos[1],
                                       "y": pos[2],
                                       "t": frame["timestamp"]}
        if frame["timestamp"] - self.t_prev > self.p_sample:
            self.ax.clear()
            self.t_prev = frame["timestamp"]
            xc, yc = [], []
            xc_m, yc_m = [], []
            for tag in self.pos_memory:
                if tag in self.m_ids:
                    xc_m.append(self.pos_memory[tag]["x"])
                    yc_m.append(self.pos_memory[tag]["y"])
                if frame["timestamp"] - self.pos_memory[tag]["t"] < self.memory_sec:
                    xc.append(self.pos_memory[tag]["x"])
                    yc.append(self.pos_memory[tag]["y"])
            xc = np.asarray(xc)
            yc = np.asarray(yc)
            data = np.asarray([xc, yc])
            if data.shape[1] > 3:
                nbins = 100
                k = kde.gaussian_kde(data)
                xi, yi = np.mgrid[xc.min():xc.max():nbins*1j, yc.min():yc.max():nbins*1j]
                zi = k(np.vstack([xi.flatten(), yi.flatten()]))
                self.ax.pcolormesh(xi, yi, zi.reshape(xi.shape), shading='gouraud', cmap=cm.magma)
                cont = self.ax.contour(xi, yi, zi.reshape(xi.shape), 2, colors='pink')
                self.ax.plot(xc_m, yc_m, 'p', markersize=12, color='lime')
            # standard plotting
            for p, poly in enumerate(self.polygons):
                for i in range(len(poly)):
                    j = (i+1) % len(poly)
                    self.ax.plot([poly[i][0], poly[j][0]],
                                 [poly[i][1], poly[j][1]],
                                 linestyle='--', color=self.colors[p])

            for i, tag in enumerate(frame["positions"]):
                if tag[0] in self.h_ids:
                    self.ax.plot(tag[1], tag[2], color='g', marker='.')
                else:
                    self.ax.plot(tag[1], tag[2], color='k', marker='.')
                self.ax.text(tag[1], tag[2], str(hex(int(tag[0]))), fontdict=dict(color='cyan'))
            self.ax.set_xlim([0, frame["xmax"]])
            self.ax.set_ylim([0, frame["ymax"]])
            self.ax.invert_yaxis()  # camera coordinates
            self.ax.set_aspect('equal')
            self.ax.set_title("timestamp: {0:.2f} sec".format(frame["timestamp"]))
            # DEBUG
            # if frame["timestamp"] >= 1613496583 and frame["timestamp"] <= 1613496585:
            #     self.figure.savefig("snapshot_{}.png".format(frame["timestamp"]))
            self.canvas.draw()
            self.canvas.get_tk_widget().pack()
            self.root.update()

    def store(self):
        self.root.destroy()
        with open(self.f_store("pos_memo.json"), 'w') as f:
            json.dump(self.pos_memory, f)

    def restore(self):
        f_cm = self.latest_state_file("pos_memo.json")
        if f_cm is not None:
            with open(f_cm, 'r') as f:
                self.pos_memory = json.load(f)

