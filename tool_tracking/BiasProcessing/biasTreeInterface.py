from abc import ABCMeta, abstractmethod
from PyQt5.QtCore import pyqtSignal, Qt, QObject, QPoint
from PyQt5.QtWidgets import QTreeWidget, QMenu, QAction, QTreeWidgetItem
from PyQt5.QtGui import QPixmap, QIcon, QCursor
from itertools import count
from tool_tracking.BiasProcessing.corrector.biasCorrector import BiasCorrector, BIAS_CORRECTORS_TYPE
from tool_tracking.BiasProcessing.interface.biasCorrectorInterface import BiasCorrectorInterface
from tool_tracking.BiasProcessing.data.dictionary import Dictionary, ELEMENT
from functools import partial
from Managers.dataManager import DataManager

class BiasTreeInterface(QObject):
    # __metaclass__ = ABCMeta

    def __init__(self, dictionary, treeWidgets , message = pyqtSignal('QString')):
        super(BiasTreeInterface, self).__init__()
        self.message = message                              # Message controler
        self.treeWidgets = treeWidgets                      # Widgets trees from the main menu
        self.name = "Bias corrector"                        # Name to display
        self.dictionary = dictionary                        # Dictionary of actual bias Corrector
        self.header = [self.name, 'name', 'type']           # Header to display
        self.flags = Qt.ItemIsUserCheckable
        
        self.biasCorrectorInterface = BiasCorrectorInterface

    def edit(self):
        item = self.treeWidgets.currentItem().parent().parent()
        if item:
            dictionary = Dictionary.get()
            parentId = int(item.text(0))
            self.biasCorrectorInterface = dictionary[self.dictionary[parentId].type.value][ELEMENT.INTERFACE.value](self.dictionary[parentId].parent, self)
            self.biasCorrectorInterface.initWindow()
                        
    def remove(self):
        widget = self.treeWidgets.currentItem().parent()
            
        if widget :
            parentId = int(widget.parent().text(0))

            self.dictionary[parentId].parent.biasCorrector = None

            self.dictionary.pop(parentId, None)
            
            widget.removeChild(widget)
            self.message.emit("request to remove {} {}".format(self.name, parentId))

    def initializeItem(self, parent):
        print("create item {}".format(self.name))
        
        item  = QTreeWidgetItem(self.header)
        parent.addChild(item)

        return item

    def receiveItems(self, items):
        if items == None:
            return

        for item in items:
            self.receiveItem(item)

    def receiveDictionary(self, dictionary):
        if dictionary == None:
            return

        self.dictionary.update(dictionary)

        for key in self.dictionary:
            print('receive {} in GIS'.format(self.name))


            texts = [str(dictionary[key].id), str(dictionary[key].name), dictionary[key].type.name]
            
            listitemsNode = self.treeWidgets.findItems(str(dictionary[key].parentId), Qt.MatchExactly | Qt.MatchRecursive, 0)
            
            parent = None

            for node in listitemsNode :
                if node.parent().text(0) == "Nodes":
                    parent = node
                    break

            newItem = None
            
            for ind in range(0, parent.childCount()):
                if parent.child(ind).text(0) == self.name:
                    newItem = parent.child(ind)
                    break

            if newItem == None:
                newItem = self.initializeItem(parent)

            subItem =  QTreeWidgetItem([str(dictionary[key].id), str(dictionary[key].name), dictionary[key].type.name])
            newItem.addChild(subItem)

            subItem.setFlags(subItem.flags() | self.flags)
            subItem.setCheckState(0, Qt.Checked)

    def receiveItem(self, item):
        print('receive {} in GIS'.format(self.name))

        texts = [str(item.id), str(item.name), item.type.name]
            
        listitemsNode = self.treeWidgets.findItems(str(item.parentId), Qt.MatchExactly | Qt.MatchRecursive, 0)
        
        parent = None

        for node in listitemsNode :
            if node.parent().text(0) == "Nodes":
                parent = node
                break

        newItem = None
        
        for ind in range(0, parent.childCount()):
            if parent.child(ind).text(0) == self.name:
                newItem = parent.child(ind)
                break

        if newItem == None:
            newItem = self.initializeItem(parent)

        if item.parentId in self.dictionary:
            self.dictionary.pop(item.parentId)
            self.dictionary[item.parentId] = item
            

            for i in range (len(texts)):
                newItem.child(0).setText(i, texts[i])
        else :
            subItem =  QTreeWidgetItem([str(item.id), str(item.name), item.type.name])
            newItem.addChild(subItem)

            subItem.setFlags(subItem.flags() | self.flags)
            subItem.setCheckState(0, Qt.Checked)
            self.dictionary[item.parentId] = item

        print('ok receive {}'.format(self.name))

    def addItem(self, handleBiasCorrector):
        item = self.treeWidgets.currentItem()
        if item :
            idNode = int(item.text(0))

            for node in DataManager.instance():
                if int(node.id) == idNode: 
                    if node.biasCorrector!=None:
                        print('biasCorrector exists already!')
                        return
                    
                    newItem = handleBiasCorrector(node)
                    node.biasCorrector = newItem
                    self.receiveItem(newItem)

    def addAction(self, menu, handle, name = "", behavior = "", icon = ""):
        imageEdit = QPixmap(icon)
        icon = QIcon(imageEdit)
        action = menu.addAction("{} {} {}".format(behavior, self.name, name))
        action.setStatusTip("{} {}".format(behavior, self.name))
        action.setIcon(icon)
        action.triggered.connect(handle)

    def addBiasCorrector(self, mainMenu, name = "", behavior = ""):
        menu = mainMenu.addMenu('{} {} {}'.format(behavior, self.name, name))
        dictionary = Dictionary.get()

        for key in dictionary:
            action = menu.addAction("{} {}".format(behavior, BIAS_CORRECTORS_TYPE(key).name))
            action.triggered.connect(lambda checked, biasCorrector = dictionary[key][ELEMENT.CORRECTOR.value] : self.onBiasCorrector(biasCorrector))

    def rightClick(self, name):
        menu = QMenu()

        self.addAction(menu, self.edit, name, "edit", "icones/edit.png")
        self.addAction(menu, self.remove, name, "remove", "icones/delete.png")

        menu.exec_(QCursor.pos())

    def onBiasCorrector(self, biasCorrector):
        self.addItem(biasCorrector)
