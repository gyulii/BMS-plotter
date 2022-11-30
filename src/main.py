import json
import os
import sys
import random
import time
import uuid

import pandas as pd
import numpy as np

from PySide6 import (
    QtCore,
    QtWidgets,
    QtGui,
)  # import PySide6 before matplotlib


from PySide6.QtCore import (
    QObject,
    QRunnable,
    QThreadPool,
    QTimer,
    Signal,
    Slot,
)

from PySide6.QtCore import QAbstractListModel, Qt
from PySide6 import QtGui
from PySide6.QtWidgets import QApplication, QMainWindow

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)




from MainWindow import Ui_MainWindow
from MyWidgets import myPlotWidget
from convolve import convolve_dataframe

class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def flags(self, index):
        return Qt.ItemIsSelectable|Qt.ItemIsEnabled|Qt.ItemIsEditable

    def data(self, index, role):
        if index.isValid():
            if role == Qt.DisplayRole or role == Qt.EditRole:
                value = self._data[index.row(), index.column()]
                return str(value)


    def refresh_table(self, new_table):
        self._data = new_table

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            self._data[index.row(), index.column()] = value
            self.dataChanged.emit(index, index)
            return True
        
    def get_table_data(self):
        return self._data

    def rowCount(self, index):
        return self._data.shape[0]

    def columnCount(self, index):
        return self._data.shape[1]

class GraphSignals(QObject):
    """
    Defines the signals available from a running worker thread.

    data
        tuple data point (worker_id, x, y)
    """

    dataframe = Signal(tuple)  
    label_and_plot = Signal(tuple)

class WorkerKilledException(Exception):
    pass

class GraphThread(QRunnable):
    """
    Worker thread

    Inherits from QRunnable to handle worker thread setup, signals
    and wrap-up.
    """

    def __init__(self , filepath = "" , window_size = 1 , new_file = 0):
        super().__init__()
        self.signals = GraphSignals()
        self.filepath = filepath
        self.window_size = window_size
        
        self.new_file = new_file
        self.label_list = []
        
        self.is_paused = False
        self.is_killed = False


    @Slot()             
    def run(self):
        
        df = pd.read_csv(self.filepath , sep=";" , encoding = 'unicode_escape')
        

        choices_dict = {}
        

        for i in range(len(df.columns)):
            choices_dict[i] = df.columns[i]

        if self.new_file:
            plot_list = np.ones(len(choices_dict))
            self.label_list = list(choices_dict.values())
            print(self.label_list)
            self.signals.label_and_plot.emit((plot_list, self.label_list))
            
        
        if self.window_size < df.shape[0] - self.window_size:
            convolved_df = convolve_dataframe(dataframe=df ,column_list= choices_dict, window=self.window_size)
            self.signals.dataframe.emit((convolved_df , choices_dict))
        else:
            raise WorkerKilledException

          
            

        
        if self.is_killed:
            raise WorkerKilledException
        
        while self.is_paused:
            time.sleep(0)  # <1>   
            if self.is_killed:
                raise WorkerKilledException




    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

    def kill(self):
        self.is_killed = True



        
class MainWindow(QMainWindow, Ui_MainWindow):
    
    table_signal = Signal(list)
    
    
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        
        """ self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.recurring_timer)
        self.timer.start()"""
        
        self.threadpool = QThreadPool() # Threading 
        
        self.table_data = np.array([[] , []])
        self.table_model = TableModel(self.table_data)
        self.table_model.dataChanged.connect(self.table_data_changed)   
        self.myTable.setModel(self.table_model)   
        self.table_labels = np.array([[0],[0]])
        self.is_new_file = 0
        self.df = pd.DataFrame()
        self.choices_dict = {}
        self.plotlist = []

        
        """        selection = self.myTable.selectionModel()
        selection.selectionChanged.connect(self.handleSelectionChanged)"""
        
    # File load start #########################
        
    
        self.myButtonFileLoad.clicked.connect(self.load_new_file)
        self.path_to_file =""
        
    # File load end #########################

    # Ploting start  ######################
     
        self.mygraph = myPlotWidget(self)
        self.myGraphLayout.addWidget(self.mygraph)
        
        
        n_data = 50
        self.xdata = list(range(n_data))
        self.ydata = [random.randint(0, 10) for i in range(n_data)]


        self.mygraph.canvas.axes.plot(self.xdata, self.ydata, "r")
        self.twin_graph = self.mygraph.canvas.axes.twinx()
        #self.mygraph.canvas.axes.set_ylabel('y1_axis', color="r") 
        
        
    # Plotting end  ######################
        
        
        self.lineEdit.returnPressed.connect(self.set_new_window_size)

        

        
    # Slider start ###############
        
        self.slider_value = 1
        
        self.horizontalSlider.sliderReleased.connect(self.slider_released)
        
        
    def slider_released(self):
        self.slider_value = self.horizontalSlider.value()
        self.label.setText(f"Convolution window size: {self.slider_value}")
        if self.slider_value:
            self.GraphWorker = GraphThread(filepath=self.path_to_file , window_size=self.slider_value , new_file=self.is_new_file)
        
        self.GraphWorker.signals.label_and_plot.connect(self.set_label_on_new_file)  
        self.GraphWorker.signals.dataframe.connect(self.plot_receive_data)        
        self.threadpool.start(self.GraphWorker)
        
        
    def set_label_on_new_file(self, label_and_plot):
        plotlist,  self.table_labels = label_and_plot
        self.plotlist = plotlist
        self.is_new_file = 0
        self.table_model.refresh_table( (np.array([self.table_labels , plotlist])).T )
        self.table_model.layoutChanged.emit()
                        
    def plot_receive_data(self, dataframe):

        self.df , self.choices_dict  = dataframe
        self.table_data = self.table_model.get_table_data()
        self.plotlist = self.table_data[0: , 1]
        
        
        #self.table_model.refresh_table( (np.array([list(choices_dict.values()) , plot_list])).T )
        #self.table_model.layoutChanged.emit()

        
        self.mygraph.canvas.axes.cla()  
        self.twin_graph.cla()
        
        
        for i in range(1,len(self.df.columns)):
            if(self.plotlist[i]):
                if(float(self.plotlist[i]) == 1):
                    self.mygraph.canvas.axes.plot(self.df[self.choices_dict[0]], self.df[self.choices_dict[i]], "r" , label = str(self.table_data[i][0]))
                if(float(self.plotlist[i]) == 2):
                    
                    color = 'tab:blue'
 
                    self.twin_graph.plot(self.df[self.choices_dict[0]], self.df[self.choices_dict[i]], color =color , label = self.table_data[i][0])
                    self.mygraph.canvas.axes.plot(np.nan, color =color , label = self.table_data[i][0])  
            
        self.mygraph.canvas.axes.legend(loc=0)
      
        # Trigger the canvas to update and redraw.
        self.mygraph.canvas.draw()

    # Slider end ###############
    

    def table_data_changed(self):
        self.table_data = self.table_model.get_table_data()
        self.plotlist = self.table_data[0: , 1]
        print(self.table_data)
        print(f"Plotlist {self.plotlist}")
        
        self.mygraph.canvas.axes.cla()  
        
        
        for i in range(1,len(self.df.columns)):
            if(float(self.plotlist[i]) == 1):
                self.mygraph.canvas.axes.plot(self.df[self.choices_dict[0]], self.df[self.choices_dict[i]], "r" , label = self.table_data[i][0])
            if(float(self.plotlist[i]) == 2):
                color = 'tab:blue'
                self.twin_graph.plot(self.df[self.choices_dict[0]], self.df[self.choices_dict[i]], color =color , label = self.table_data[i][0])
                self.mygraph.canvas.axes.plot(np.nan, color =color , label = self.table_data[i][0])  
                

        
        self.mygraph.canvas.axes.legend(loc=0)

        # Trigger the canvas to update and redraw.
        self.mygraph.canvas.draw()  
             
    
        
        
    
    
    
    def load_new_file(self):
        filename, filter = QFileDialog.getOpenFileName(parent=self, caption='Open exported BMS data', dir='.', filter='Exported csv files (*.csv)')
    
        if filename:
            self.myLabelFileLoad.setText(f"Loaded: {filename}")
            self.path_to_file = filename
            self.is_new_file = 1
        return self.slider_released()

    def set_new_window_size(self):
        self.horizontalSlider.setValue( int(self.lineEdit.text())) 
        return self.slider_released()

    def closeEvent(self, *args, **kwargs):
        super(QMainWindow, self).closeEvent(*args, **kwargs)
        print("\nProgram closed, killing all threads!\n\n")
       # self.GraphWorker.kill() # ToBe fixed with thread manager
        sys.exit()

        
        
  




app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()