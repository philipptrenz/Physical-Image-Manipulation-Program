#! /usr/bin/python3 
#eeeeeeoooo
import sys
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, 
    QLabel, QApplication, QPushButton)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QObject


class FreakingQtImageViewer(QWidget):
    
    def __init__(self, function):
        super().__init__()
        self.function = function
        
        self.initUI(function)
        
    def refresh(self):
        self.function()
        
        pixmap = QPixmap("tmp.jpg")
        pixmap = pixmap.scaledToWidth(800)
        self.lbl.setPixmap(pixmap)
        
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


        
        

