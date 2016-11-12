#! /usr/bin/python3 

import sys
import time
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, 
    QLabel, QApplication, QPushButton)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QObject


class FreakingQtImageViewer(QWidget):
    
    def __init__(self, function):
        super().__init__()
        self.function = function
        self.initUI(function)
        self.refresh = False
    
      
    def refresh(self):
        if not self.refresh:
            self.refresh = True
            while self.refresh:
                self.function()
                
                pixmap = QPixmap("tmp.png")
                pixmap = pixmap.scaledToWidth(800)
                self.lbl.setPixmap(pixmap)
                time.sleep(0.5)
        else: 
            self.refresh = False
        
    def initUI(self, function):      

        hbox = QHBoxLayout(self)
        
        self.lbl = QLabel(self)
        self.refresh()
        
        btn = QPushButton(self)
        btn.setText('Drück mich')
        btn.clicked.connect(self.refresh)
        
        hbox.addWidget(self.lbl)
        hbox.addWidget(btn)
        self.setLayout(hbox)
        
        self.move(300, 200)
        self.setWindowTitle('Freaking Qt Image Viewer')
        self.show()


        
        

