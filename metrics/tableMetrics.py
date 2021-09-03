from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import numpy as np

class metricsWidget(QWidget):

    def __init__(self, parent = None):

        QWidget.__init__( self, parent )
        self.static_canvas = FigureCanvas(Figure(figsize=(5, 4)))
        self.navi_toolbar = NavigationToolbar(self.static_canvas, self)

        self.vlayout = QVBoxLayout()

        self.vlayout.addWidget(self.navi_toolbar)
        
        self.vlayout.addWidget(self.static_canvas, Qt.AlignHCenter | Qt.AlignVCenter)

    def setResults(self,results):
        
        names = ["GOSPA","OSPA","Ground Truth vs Estimated Cardinal","Average Mean Squared Error"]
        for i in range(results.shape[0]):
            if i <= 2:
                _static_ax = self.static_canvas.figure.add_subplot(2,2,i+1,title=names[i])

            elif i>3:
                _static_ax = self.static_canvas.figure.add_subplot(2,2,i,title=names[i-1])

            t = np.linspace(0, 1, results.shape[1])
            _static_ax.plot(t, results[i,:], ".")

    def getLayout(self):
        return self.vlayout