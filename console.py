# -*- coding: utf-8 -*-
"""
Created on Tue Jul  2 15:55:50 2019

@author: bpanneti
"""

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtOpenGL import *
from PyQt5.QtWidgets import *


class Console(QWidget):

    def __init__(self, parent=None):
    
        super(Console, self).__init__()
        
        self.textEdit = QTextEdit()
        p = QPalette()
        p.setColor(QPalette.Text, QColor('green')); 
        p.setColor(QPalette.Base, QColor('black')); 
        self.textEdit.setPalette(p)
        
        font = QFont()
        font.setFamily('Lucida')
        font.setFixedPitch(True)
        font.setPointSize(10)
        font.setBold(True)
        self.textEdit.setFont(font)
        self.textEdit.setReadOnly(True)
         
        '''
        but1 = QPushButton('write')
        but1.clicked.connect(self.but_write)

        but2 = QPushButton('read')
        but2.clicked.connect(self.but_read)
        ''' 
 

        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        vbox.addWidget(self.textEdit)
        self.write('GIS message! Welcome!')

        

    
        self.setLayout(vbox)
        self.show
  
    def write(self,text):
        self.textEdit.append('--> ' + text )