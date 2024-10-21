from PySide6.QtCore import Qt, QModelIndex, QAbstractItemModel
from typing import List

class TreeItem(object):
    def __init__(self, props={}):
        self.props:dict = props
        self.checkState:dict = {key:None for key in self.props.keys()}
        self.parentItem = None
        self.children:List[TreeItem] = []

    def data(self, key):
        return self.props.get(key, None)
    
    def getCheckState(self, key):
        return self.checkState.get(key, None)

    def child(self, row):
        return self.children[row]

    def parent(self):
        return self.parentItem

    def childCount(self):
        return len(self.children)

    def appendChild(self, item):
        self.children.append(item)
        item.parentItem = self

    def removeChild(self, row):
        del self.children[row]

    def row(self):
        if self.parentItem is not None:
            return self.parentItem.children.index(self)
        return 0
    
    def setData(self, key, value):
        if key in self.props:
            self.props[key] = value
        else:
            self.props[key] = value
            self.checkState[key] = None
    
    def setCheckState(self, key, checkState):
        if key in self.props:
            self.checkState[key] = checkState

class TreeModel(QAbstractItemModel):
    def __init__(self, parent=None, root=TreeItem()):
        super(TreeModel, self).__init__(parent)
        self._root = root
        self.columns = []
    
    def addColumns(self, columns, parent=QModelIndex()):
        self.beginInsertColumns(parent, self.columnCount(), self.columnCount() + len(columns) - 1)
        self.columns.extend(columns)
        self.endInsertColumns()
    
    def column(self, key):
        return self.columns[key]

    def data(self, index: QModelIndex, role:int):
        if not index.isValid():
            return None
        item = index.internalPointer()
        key = self.column(index.column())
        value =  item.data(key)
        checkState = item.getCheckState(key)
        if role == Qt.EditRole:
            return value
        elif role == Qt.DisplayRole:
            return value
        elif role == Qt.CheckStateRole:
            if checkState is not None:
                return (Qt.Checked if checkState else Qt.Unchecked)
            else:
                return None
        return None
    
    def setData(self, index: QModelIndex, value, role:int):
        if not index.isValid():
            return False
        item:TreeItem = index.internalPointer()
        key = self.column(index.column())
        if role in [Qt.EditRole, Qt.DisplayRole]:
            item.setData(key, value)
            self.dataChanged.emit(index, index)
        elif role == Qt.CheckStateRole:
            if Qt.CheckState(value) == Qt.Checked:
                item.setCheckState(key, True)
            else:
                item.setCheckState(key, False)
            self.dataChanged.emit(index, index)
        return True

    def index(self, row, column, parent:QModelIndex=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        if not parent.isValid():
            parentItem = self._root
        else:
            parentItem = parent.internalPointer()
        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        return QModelIndex()

    def parent(self, index:QModelIndex):
        if index.isValid():
            parentItem = index.internalPointer().parent()
            if parentItem is not None:
                return self.createIndex(parentItem.row(), 0, parentItem)
        return QModelIndex()

    def rowCount(self, parent:QModelIndex):
        if parent.isValid():
            parentItem:TreeItem = parent.internalPointer()
        else:
            parentItem:TreeItem = self._root
        return parentItem.childCount()

    def columnCount(self, parent=QModelIndex()):
        return len(self.columns)
    
    def headerData(self, section:int, orientation:Qt.Orientation, role:int):
        if (orientation == Qt.Horizontal) and (role == Qt.DisplayRole):
            return self.column(section)
        return None

    def appendChild(self, item:TreeItem, parent_index:QModelIndex):
        if (parent_index is None) or (not parent_index.isValid()):
            parent = self._root
        else:
            parent = parent_index.internalPointer()
        parent.appendChild(item)
    
    def flags(self, index:QModelIndex):
        if not index.isValid():
            return Qt.NoItemFlags
        flag = Qt.ItemIsEnabled
        checkState = index.data(Qt.CheckStateRole)
        if checkState is not None:
            flag |= Qt.ItemIsUserCheckable
        return flag