from Utils import *
from GraphUtils import *
from Global import *
from BaseClass import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QAxContainer import *


class DayTable:
    #def __init__(self, mother, name, columnHeaders, columnWidth):
    def __init__(self, mother, name):
        self.layout, self.topLayout = QGridLayout(), QGridLayout()
        self.titleLabel = QLabel(name)
        self.mother = mother

        self.dummyLabel = QLabel('   ')
        self.latestDateLabel = QLabel(' | :')
        self.latestDateEdit = QLineEdit(str(10))
        self.latestDateEdit.setMaximumWidth(WIDTH_EDIT_BOX)

        #self.columnHeaders = columnHeaders
        self.columnHeaders = ["등락율","거래증가","누적대금","순대금",'회전율',"순회전율","파바박","순파워"]
        self.columnWidth = [45, 55, 55, 50, 50, 50, 50, 55, 55, 55]

        self.combo = QComboBox()
        self.combo.setMaximumWidth(200)
        for k in self.columnHeaders:
            self.combo.addItem(k)
        self.combo.setCurrentIndex(0)
        self.combo.currentIndexChanged.connect(self.refreshTable)

        self.table = QTableWidget()
        self.table.setRowCount(NUM_TABLE_ROW)
        self.table.setColumnCount(len(self.columnHeaders))
        self.table.verticalHeader().setMinimumWidth(80)
        self.table.verticalHeader().setMaximumWidth(80)

        self.table.clicked.connect(self.updateSelectedCode)

        self.rowPtr = 0  # Table 종목 추가 Pointer

        for index, header in enumerate(self.columnHeaders):
            col_item = QTableWidgetItem(header)
            self.table.setHorizontalHeaderItem(index, col_item)
            self.table.setColumnWidth(index, self.columnWidth[index])

        self.clearTables()
        for i in range(NUM_TABLE_ROW):
            self.table.setRowHeight(i, WIDTH_TABLE_ROW)
        #self.table.resizeRowsToContents()

        self.topLayout.addWidget(self.titleLabel, 0, 0)
        #self.topLayout.addWidget(self.latestDateLabel, 0, 1)
        #self.topLayout.addWidget(self.latestDateEdit, 0, 2)
        self.topLayout.addWidget(self.dummyLabel, 0, 1)
        self.topLayout.addWidget(self.combo, 0, 2)
        self.topLayout.setColumnStretch(1, 1)
        self.layout.addLayout(self.topLayout, 0, 0)
        self.layout.addWidget(self.table, 1, 0)

    #def appendList(self, dataList):
#        if len(dataList) > 0:
#        tempList = sorted(dataList, key=lambda x: (x[1]), reverse=True)
#        #tempList = sorted(tempList, key=lambda x: (x[0]), reverse=False)
#        for iList in tempList:
#            self.appendLine(iList[0], iList[1:])
    def refreshTable(self):
        self.clearTables()
        dataList = []
        for data in self.mother.datas.values():
            #"등락율","거래증가","누적대금","순대금","P대금",'회전율',"순회전율","P회전율"
            dataList.append([data.name, data.종목타입, round(data.등락율,2), round(data.거래량증가), int(data.누적거래대금), int(data.순대금), 
                             round(data.회전율,1), data.순회전율, int(data.파바박대금),
                             round(data.순매수파워,2), 
                             ])

        sort_index = self.combo.currentIndex() + 2
        tempList = sorted(dataList, key=lambda x: (x[sort_index]), reverse=True)
        #tempList = sorted(dataList, key=lambda x: (x[1]), reverse=True)
        #tempList = sorted(tempList, key=lambda x: (x[0]), reverse=False)
        for iList in tempList:
            self.appendLine(iList[0], iList[1], iList[2:])

    def appendLine(self, name, type, datas):
        if self.rowPtr >= NUM_TABLE_ROW:
            return
        for col, val in enumerate(datas):
            item = QTableWidgetItem(str(val))
            item.setTextAlignment(Qt.AlignCenter)
            red = QColor(255, 0, 0)
            pastel = QColor(255, 200, 200)
            green = QColor(0,255,0)
            if self.columnHeaders[col] == '등락율':
                item.setBackground(QBrush(getBackgroundColor(val, 30)))
            elif self.columnHeaders[col] == '누적대금':
                item.setBackground(QBrush(getBackgroundColor(val, 1000)))
            elif self.columnHeaders[col] == '거래증가':
                item.setBackground(QBrush(getBackgroundColor(val, 500)))                
            elif self.columnHeaders[col] == '회전율':
                item.setBackground(QBrush(getBackgroundColor(val, 100)))
            elif self.columnHeaders[col] == '순회전율':
                item.setBackground(QBrush(getBackgroundColor(val, 5)))
            elif self.columnHeaders[col] == '순파워':
                item.setBackground(QBrush(getBackgroundColor(val, 10)))
            elif self.columnHeaders[col] == '순대금':
                item.setBackground(QBrush(getBackgroundColor(val, 100)))
            elif self.columnHeaders[col] == '파바박':
                item.setBackground(QBrush(getBackgroundColor(val, 100)))
            self.table.setItem(self.rowPtr, col, item)

            row_item = QTableWidgetItem(name)
            if type == "대형주":
                red.setAlphaF(0.5)
                row_item.setBackground(QBrush(red))
            elif type == "중형주":
                pastel.setAlphaF(0.5)
                row_item.setBackground(QBrush(pastel))
            self.table.setVerticalHeaderItem(self.rowPtr, row_item)
        self.rowPtr += 1

    def clearTables(self):
        for i in range(NUM_TABLE_ROW):
            self.clearTable(i)
        self.rowPtr = 0

    def clearTable(self, tableRow):
        if tableRow == -1:
            return
        for col in range(len(self.columnHeaders)):
            self.table.setItem(tableRow, col, QTableWidgetItem(str('-')))
            self.table.setVerticalHeaderItem(tableRow, QTableWidgetItem(str('-')))

    def setTitle(self, name):
        self.titleLabel.setText(name)

    def updateSelectedCode(self):
        inputText = self.table.verticalHeaderItem(self.table.currentRow()).text()
        if inputText != '-':
            self.mother.updateSelectedCodeEdit(inputText)

