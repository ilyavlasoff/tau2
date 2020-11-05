import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
import numpy as np


class TableModel(QtCore.QAbstractTableModel):

    def __init__(self, data, header):
        super(TableModel, self).__init__()
        self.data_matrix = data
        self.row_count = len(data)
        if len(data) == 0:
            self.column_count = len(header)
        else:
            self.column_count = len(data[0])
        if self.column_count > len(header):
            for i in range(len(header), self.column_count):
                header.append(i)
        self.header = header

    def setData(self, index, value, role: int = ...) -> bool:
        if not index.isValid():
            return False

        if role == QtCore.Qt.EditRole:
            try:
                self.data_matrix[index.row()][index.column()] = float(value)
            except ValueError:
                self.data_matrix[index.row()][index.column()] = 0
            self.dataChanged.emit(
                index, index, (QtCore.Qt.EditRole,)
            )
        else:
            return False
        return True

    def data(self, index, role):
        if role == Qt.DisplayRole:
            r = index.row()
            c = index.column()
            return self.data_matrix[index.row()][index.column()]

    def rowCount(self, index) -> int:
        return self.row_count

    def columnCount(self, index) -> int:
        return self.column_count

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(self.header[section])
        return

    def add_column(self, col=[], header=None):
        if len(col) < self.row_count:
            for i in range(len(col), self.row_count):
                col.append(0)
        elif len(col) > self.row_count:
            self.row_count = len(col)
            for i in range(self.row_count):
                self.data_matrix.append([])
        for i in range(self.row_count):
            try:
                self.data_matrix[i].append(float(col[i]))
            except ValueError:
                self.data_matrix[i].append(col[i])
        if header:
            self.header.append(header)
        else:
            self.header.append(self.columnCount)
        self.column_count += 1
        self.layoutChanged.emit()
        return self

    def add_row(self, row):
        self.add_rows(1, row)

    def add_rows(self, quantity, rows=[]):
        if quantity > len(rows):
            for i in range(quantity - len(rows)):
                row = []
                for j in range(self.column_count):
                    row.append(float(0))
                self.data_matrix.append(row)
        for row in rows:
            if len(row) < self.column_count:
                for i in range(len(row)):
                    try:
                        row[i] = float(row[i])
                    except ValueError:
                        row[i] = float(0)
                for i in range(len(row), self.column_count):
                    row.append(float(0))
            self.data_matrix.append(row)
        self.row_count += quantity
        self.layoutChanged.emit()
        return self

    def remove_last_row(self, quantity=1):
        for i in range(quantity):
            self.remove_row(len(self.data_matrix)-1)

    def remove_row(self, row):
        if row >= len(self.data_matrix) or row < 0:
            raise Exception('No such index')
        del self.data_matrix[row]
        self.row_count -= 1
        self.layoutChanged.emit()

    def remove_row_range(self, starts, ends):
        if starts > ends:
            raise Exception('Start index must be less than end')
        if ends < len(self.data_matrix):
            raise Exception('End index exceeds data matrix length')
        if starts < 0:
            raise Exception('Starts index must go beyond zero')
        self.data_matrix = self.data_matrix[:starts][ends:]
        self.rowCount -= (ends - starts)
        self.layoutChanged.emit()

    def remove_last_column(self):
        self.remove_column(len(self.data_matrix)-1)

    def remove_column(self, col):
        for i in range(len(self.data_matrix)):
            del self.data_matrix[i][col]
        self.column_count -= 1
        self.layoutChanged.emit()

    def flags(self, index: QModelIndex):
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def set_data(self, index, value, role):
        try:
            self.data_matrix[index.row()][index.column()] = float(value)
        except ValueError:
            self.data_matrix[index.row()][index.column()] = value
        return True

    def get_data_matrix(self):
        return np.array(self.data_matrix, dtype=object)