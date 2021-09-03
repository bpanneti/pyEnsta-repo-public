# -*- coding: utf-8 -*-
"""
Created on Tue Jul  9 18:40:37 2019

@author: bpanneti
"""
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtOpenGL import *
from PyQt5.QtWidgets import *

import sys, csv

class tablePlots(QWidget):

    def __init__(self, parent=None):
    
        super(tablePlots, self).__init__()
    
        layout = QHBoxLayout()
        # button d'action
        pixmap = QPixmap("icones/send.png")
        self.push_buttonCsv = QPushButton()   
        self.push_buttonCsv.setToolTip("export in csv")
        self.push_buttonCsv.setIcon(QIcon(pixmap))
        layout.addWidget(self.push_buttonCsv)
        pixmap = QPixmap("icones/copy.png")
        self.push_buttonCopy = QPushButton()   
        self.push_buttonCopy.setToolTip("copy")
        self.push_buttonCopy.setIcon(QIcon(pixmap))
        layout.addWidget(self.push_buttonCopy)
        pixmap = QPixmap("icones/paste.png")
        self.push_buttonPaste = QPushButton()   
        self.push_buttonPaste.setToolTip("paste")
        self.push_buttonPaste.setIcon(QIcon(pixmap))
        layout.addWidget(self.push_buttonPaste)
        
 
        
        self.editCategorie = QLineEdit()
        layout.addWidget(self.editCategorie)
        
        #tableau
        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(6)
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.setHorizontalHeaderLabels(['id plots', 'date', 'longitude', 'latitude','altitude','categorie'])
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.setSelectionMode(QAbstractItemView.MultiSelection)
        #self.tableWidget.setEditTriggers(QTableWidget.NoEditTriggers)
        
        header = self.tableWidget.horizontalHeader() 
        
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(QHeaderView.Stretch)
        #connect
        
        
        self.push_buttonCopy.clicked.connect(self.copyCategorie)
        self.push_buttonPaste.clicked.connect(self.pasteCategorie)
        self.push_buttonCsv.clicked.connect(self.exoprtCSV)
        
        
        hBox = QVBoxLayout()
        hBox.addWidget(self.tableWidget)
        vbox = QVBoxLayout()
        vbox.addLayout(layout)
        hBox.addWidget(self.tableWidget)
        vbox.addLayout(hBox)
        self.setLayout(vbox)
        self.show()
        
        
         
    def receiveDetections(self,_detections):
        
        #print(["recieve selected _detections", len(_detections)])
        for _det in _detections:
            numrows = self.tableWidget.rowCount()           
            self.tableWidget.insertRow(numrows) 
            item = QTableWidgetItem(str(_det.id))
            item.setFlags(  Qt.ItemIsEnabled) 
            self.tableWidget.setItem(numrows ,0,item)
            item = QTableWidgetItem(_det.dateTime.toString("dd-MM-yyyy HH:mm:ss.z"))
            item.setFlags(  Qt.ItemIsEnabled) 
            self.tableWidget.setItem(numrows ,1,item)
            item = QTableWidgetItem(str(_det.Position.longitude))
            item.setFlags(  Qt.ItemIsEnabled) 
            self.tableWidget.setItem(numrows ,2,item)
            item = QTableWidgetItem(str(_det.Position.latitude))
            item.setFlags(  Qt.ItemIsEnabled) 
            self.tableWidget.setItem(numrows ,3,item)
            item = QTableWidgetItem(str(_det.Position.altitude))
            item.setFlags(  Qt.ItemIsEnabled) 
            self.tableWidget.setItem(numrows ,4,item)
            item = QTableWidgetItem("no cat")
            item.setBackground(QColor(100,100,150))
            item.setFlags( Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable) 
            self.tableWidget.setItem(numrows ,5,item)
        self.tableWidget.update()
        #print("end")
        
    def    copyCategorie(self):
        
        _itm = self.tableWidget.currentItem()
        if _itm:
           self.editCategorie.setText( _itm.text())
            
    def    pasteCategorie(self):  
   
        for row in range(self.tableWidget.rowCount()):
            item = self.tableWidget.item(row, 5)

            if item.isSelected():
                
                item.setText(self.editCategorie.text())
                
                
        self.tableWidget.update()        
    def     exoprtCSV(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _  = QFileDialog.getSaveFileName(self,"export in csv file","","csv (*.csv)", options=options)
        if fileName:
             print(fileName)
             with open(fileName, 'w') as stream:
 
                writer = csv.writer(stream)
          
                for row in range(self.tableWidget.rowCount()):
                    rowdata = []
                    for column in range(self.tableWidget.columnCount()):
                        item = self.tableWidget.item(row, column)
                        if item is not None:
                            rowdata.append(item.text())
                        else:
                            rowdata.append('')
                    
                    writer.writerow(rowdata)
     