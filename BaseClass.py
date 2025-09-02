from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# 체크박스 객체
class CheckBox:
    def __init__(self, mother, key):
        self.mother = mother        # mother class instance bind
        self.key = key
        self.checkBox = QCheckBox(key)
        self.checkBox.stateChanged.connect(self.checkBox_clicked)
        self.flag = False

    def setCheckState(self, val):
        self.checkBox.setCheckState(Qt.CheckState(val))
        self.flag = self.checkBox.isChecked()

    def checkState(self):
        return self.checkBox.checkState()

    def checkBox_clicked(self):
        self.flag = self.checkBox.isChecked()
        if self.mother.initDone is True:
            self.mother.drawMinuteGraph()

# 버튼 객체
class Button:
    def __init__(self, mother, key, widget):
        self.mother = mother
        self.key = key
        self.button = QPushButton(key, widget)
        self.button.setEnabled(False)

    def setEnabled(self):
        self.button.setEnabled(True)

# Label + Edit 객체
class LabelEdit:
    def __init__(self, mother, category, key, initStr, width):
        self.label = QLabel(f"{key}:")
        self.edit = QLineEdit()
        self.edit.setText(initStr)
        self.edit.setMaximumWidth(width)
        self.key = key
        self.mother = mother
        self.value = ''
        self.category = category

        self.layout = QGridLayout()
        self.layout.addWidget(self.label, 0, 0)
        self.layout.addWidget(self.edit, 0, 1)
        self.edit.textChanged.connect(self.editTextChanged)
        if self.key == '종목명':
            self.edit.returnPressed.connect(self.editReturnPressed)

    def setText(self, text):
        self.edit.setText(text)

    def editTextChanged(self):
        if self.edit.text() != '':
            self.value = self.edit.text()
            if self.category == '표':
                self.mother.clearTopList()

            if self.key == '분봉초':
                self.mother.datas[self.mother.selectedCode].periodUnit = int(self.value)
            elif self.key == '랜덤복기개수':
                self.mother.loadRandomNum = int(self.value)
            elif self.key == '복기날짜':
                self.mother.loadDate = self.value

    def setCompleter(self, completer):
        self.edit.setCompleter(completer)

    def editReturnPressed(self):
        inputText = self.edit.text()

        try:  # 종목코드가 입력된 경우인지 판별
            index = self.mother.codes.index(inputText)
        except:
            index = -1

        if index == -1:
            try:  # 종목명이 입력된 경우인지 판별
                index = self.mother.names.index(inputText)
            except:
                index = -1

        if index != -1:
            self.mother.selectedCode = self.mother.codes[index]
            self.edit.setText(self.mother.names[index])
            self.mother.labelEditDict['분봉초'].setText(str(self.mother.datas[self.mother.selectedCode].periodUnit))
            self.mother.updateGraph()



# 시종고저 클래스
class OCHL:
    def __init__(self, 초기값):
        self.시가, self.종가, self.고가, self.저가 = 초기값, 초기값, 초기값, 초기값
        self.start = False

    def update(self, 현재가):
        if self.start is False:
            self.start = True
            self.시가, self.종가, self.고가, self.저가 = 현재가, 현재가, 현재가, 현재가
        else:
            if self.고가 < 현재가:   self.고가 = 현재가
            if self.저가 > 현재가:   self.저가 = 현재가
            self.종가 = 현재가

    def syncToClose(self):
        self.시가, self.고가, self.저가 = self.종가, self.종가, self.종가

    def getValues(self):
        return OCHLValue(self.시가, self.종가, self.고가, self.저가)

# 시종고저 값만
class OCHLValue:
    def __init__(self, 시가, 종가, 고가, 저가):
        self.시가, self.종가, self.고가, self.저가 = 시가, 종가, 고가, 저가


