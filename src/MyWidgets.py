


from PySide6.QtWidgets import ( QVBoxLayout, QSizePolicy, QWidget,)

import random

import matplotlib
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


matplotlib.use("QtAgg")

from matplotlib.backends.backend_qtagg import (
    NavigationToolbar2QT as NavigationToolbar,
)




class myPlotWidget(QWidget):
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        self.setLayout(QVBoxLayout())
        self.canvas = PlotCanvas(self, width=10, height=8)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(self.canvas)

class PlotCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=10, height=8, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)
        FigureCanvasQTAgg.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvasQTAgg.updateGeometry(self)
        
"""        self.plot()
        
    def plot(self):
        data = [random.randint(0,10) for i in range(250)]
        ax = self.fig.add_subplot(111)
        ax.plot(data, 'r-', linewidth = 0.5)
        ax.set_title('PyQt Matplotlib Example')
        self.draw()"""