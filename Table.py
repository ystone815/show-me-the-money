from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QAxContainer import *
import pyqtgraph as pg
from Global import *
from BaseClass import *
from RealData import *

class Table:
    def __init__(self, mother, index):
        self.layout, self.topLayout, self.condLayout = QGridLayout(), QGridLayout(), QGridLayout()
        self.dummyLabel = QLabel('    ')
        self.mother = mother

        #self.labelEditDict = {}
        #for i, key in enumerate(TABLE_LABEL_EDIT_KEY):
        #    self.labelEditDict[key] = LabelEdit(self, '표', key, '0', WIDTH_TABLE_EDIT_BOX)

        self.tableIndex = str(index)

        self.combo = QComboBox()
        self.combo.setMaximumWidth(200)
        self.refLabel = QLabel()
        self.condLayout.addWidget(self.combo, 0, 0)
        self.condLayout.addWidget(self.refLabel, 0, 1)
        self.combo.currentIndexChanged.connect(self.condListToTable)

        self.column_headers = ['기준봉', '포착시각', '등락율', '거래증가', '누적대금', '순대금', 
                               '순파워', '회전율', '순회전율']
        self.column_width = [50, 50, 45, 50, 50, 45, 45,
                             50, 50, 50, 50]

        self.table = QTableWidget()
        self.table.setRowCount(NUM_TABLE_ROW)
        self.table.setColumnCount(len(self.column_headers))
        self.table.verticalHeader().setMinimumWidth(85)
        self.table.verticalHeader().setMaximumWidth(85)
        self.table.clicked.connect(self.updateSelectedCode)

        self.topList = {}   # code, tableRow
        self.rowPtr = 0     # Table 종목 추가 Pointer
        self.조건식명 = ''

        for index, header in enumerate(self.column_headers):
            col_item = QTableWidgetItem(header)
            self.table.setHorizontalHeaderItem(index, col_item)
            self.table.setColumnWidth(index, self.column_width[index])

        for row_num in range(NUM_TABLE_ROW):
            self.updateTable(row_num, RealData('0', '-', 0))
            self.table.setRowHeight(row_num, WIDTH_TABLE_ROW)
        #self.table.resizeRowsToContents()

        self.condLayout.addWidget(self.dummyLabel, 0, 1)
        #self.condLayout.setColumnStretch(1, 1)
        self.layout.addLayout(self.condLayout, 0, 0)
        #self.layout.addLayout(self.topLayout, 1, 0)
        self.layout.addWidget(self.table, 1, 0)

    def condListToTable(self):
        if self.mother.initDone is False:
            return
        self.clearTopList()
        self.조건식명 = self.combo.currentText()
        if self.조건식명 != '':
            codeList = self.mother.조건식_만족_종목들[self.조건식명]
            for val in codeList:
                code = val[0]
                self.appendCode(self.mother.datas[code])

            # 기준봉 조건들 프린트
            labelStr = ''
            if "기준봉" in self.mother.조건식[self.조건식명].keys():
                for 기준봉_조건, 기준봉_값 in self.mother.조건식[self.조건식명]["기준봉"].items():
                    labelStr = f"{labelStr} {기준봉_조건} {기준봉_값} | "
            self.refLabel.setText(labelStr)

    def updateSelectedCode(self):
        inputText = self.table.verticalHeaderItem(self.table.currentRow()).text()
        if inputText not in  ['-','']:
            self.mother.updateSelectedCodeEdit(inputText)

    def isCodeInTopList(self, code):
        if code in list(self.topList.keys()):
            return True
        else:
            return False

    def appendCode(self, realData):
        if self.isCodeInTopList(realData.code) is False and self.rowPtr < NUM_TABLE_ROW:
            self.topList[realData.code] = self.rowPtr
            self.updateTable(self.rowPtr, realData)
            self.rowPtr += 1

    def clearTopList(self):
        #for i in range(self.rowPtr):
        #    self.updateTable(i, RealData('0', '-', 0))
        self.clearTable()
        self.topList.clear()
        self.rowPtr = 0

    def clearTable(self):
        items = ['', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        for row in range(self.rowPtr):
            for col, val in enumerate(items):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)
                row_item = QTableWidgetItem('')
                self.table.setVerticalHeaderItem(row, row_item)

    def updateTable(self, tableRow, data: RealData):
        if tableRow == -1:
            return

        포착시각 = ''
        기준봉시각 = ''

        if self.조건식명 != '':
            포착시각 = data.조건식_만족시각[self.조건식명]
            if "기준봉" in data.mother.조건식[self.조건식명].keys():
                기준봉시각 = data.기준봉_만족시각[self.조건식명]

        items = [기준봉시각, 포착시각, data.등락율, int(data.거래량증가),
                 int(data.누적거래대금), int(data.순대금), round(data.순매수파워,2),
                 data.회전율, data.순회전율]
        for col, val in enumerate(items):
            item = QTableWidgetItem(str(val))
            item.setTextAlignment(Qt.AlignCenter)
            red = QColor(255, 0, 0)
            red2 = QColor(255, 0, 0)
            pastel = QColor(255, 200, 200)
            green = QColor(0,255,0)
            yellow = QColor(255,255,0)
            if self.column_headers[col] == '등락율':
                item.setBackground(QBrush(getBackgroundColor(val, 30)))
            elif self.column_headers[col] == '회전율':
                item.setBackground(QBrush(getBackgroundColor(val, 100)))
            elif self.column_headers[col] == '순회전율':
                item.setBackground(QBrush(getBackgroundColor(val, 5)))
            elif self.column_headers[col] == '누적대금':
                item.setBackground(QBrush(getBackgroundColor(val, 2000)))
            elif self.column_headers[col] == '순대금':
                item.setBackground(QBrush(getBackgroundColor(val, 300)))
            elif self.column_headers[col] == '순장악':
                item.setBackground(QBrush(getBackgroundColor(val, 30)))
            elif self.column_headers[col] == '순파워':
                item.setBackground(QBrush(getBackgroundColor(val, 10)))
            elif self.column_headers[col] == '거래증가':
                item.setBackground(QBrush(getBackgroundColor(val, 500)))            

            self.table.setItem(tableRow, col, item)
            row_item = QTableWidgetItem(data.name)
            if data.종목타입 == "대형주":
                red.setAlpha(100)
                row_item.setBackground(QBrush(red))
            elif data.종목타입 == "중형주":
                pastel.setAlpha(200)
                row_item.setBackground(QBrush(pastel))
            #elif data.종목타입 == "소형주":
            #    yellow.setAlphaF(0.5)
            #    row_item.setBackground(QBrush(yellow))
            self.table.setVerticalHeaderItem(tableRow, row_item)

