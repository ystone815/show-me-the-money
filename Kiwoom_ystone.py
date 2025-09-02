import csv
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QAxContainer import *
import psutil  # 메모리 사용량 조회용
import pyqtgraph as pg
import random
from Utils import *
from GraphUtils import *
from Global import *
from BaseClass import *
from RealData import *
from Table import *
from DayTable import *
from SectorData import *
import time
from threading import Thread

class SubWindow(QMainWindow):
    def __init__(self, parent, startX, startY, widthX, widthY, title=None):
        super(SubWindow, self).__init__(parent)
        #super().__init__()
        self.setGeometry(startX, startY, widthX, widthY)
        if title!=None:
            self.setWindowTitle(title)
        self.widget = QWidget(self)
        self.layout = QGridLayout(self.widget)
        self.setCentralWidget(self.widget)
        #self.show()

# 메인 윈도우. UI는 내부에서 직접 작성하여 대응함
class MyWindow(QMainWindow):
    # 해상도에 따라 레이아웃이 깨지는 문제에 대응하는 코드. QApplication 객체 생성 이전에 실행해야 한다.
    @classmethod
    def setHiDpi(cls):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)  # Enable highdpi scaling
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)  # Use highdpi icons

    # 클래스 생성자
    def __init__(self):
        super().__init__()

        #self.weekend = isWeekend()

        self.selectedCode = -1
        self.selectedSector = 전체섹터_이름
        self.loadDate = 0  # 복기 날짜
        self.initDone = False  # Code불러오는 작업 끝났을때 True (이때부터 Timer 동작 시작)

        self.file_loading = False   # 파일 로드시 GUI나 sort 동작하지 않게

        self.codes = []  # 확인할 종목코드
        self.temp_codes = {}  # 필터링용 임시
        self.names = []  # 종목코드에 대한 이름 저장용
        self.nameToCode = {}  # name - code 딕셔너리
        self.datas = {}  # 실시간 수신 데이터 저장용, key는 종목코드, 값은 RealData형식
        self.sectors = {}
        self.loadRandomNum = 10  # 랜덤 복기 종목 개수

        # 키움 객체 및 사용자 이벤트용 객체
        self.objKiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")

        self.조건식 = {}   # {"조건식명", {}}
        self.조건식_만족_종목들 = {} # {"조건식명", [code, name, 시각]}

        self.initUI()
        self.initSignalSlot()  # 시그널/슬롯 설정

        # 로그인을 실행한다.
        if SKIP_LOGIN == 0:
            self.objKiwoom.dynamicCall("CommConnect()")

        #atexit.register(self.__del__)  # 종료 버튼으로 종료할 때 실행시킨다. __del__ 실행을 보장하기 위해서 사용

        self.reqOpt10001_list = []
        self.reqOpt10081_list = []
        self.reqOpt90004_list = []

        #t = threading.Thread(target=self._loadAllButton_clicked, args=())
        #t.start()
        self.timerPhase = 0
        self.timerSort = QTimer(self)
        self.timerSort.start(TIMER_PERIOD)
        self.timerSort.timeout.connect(self.timeout)

        self.topList = {}
        for listKey in TOP_LIST_KEY:
            self.topList[listKey] = []

        self.accountNo = ""
        self.reqOpt90004_scrNo = 0

        self.상승종목수, self.보합종목수, self.하락종목수 = 0, 0, 0

        if SKIP_LOGIN == 1:
            self.doInit()

    # 시그널/슬롯 연결 설정
    def initSignalSlot(self):
        # 수신 이벤트 연결
        self.objKiwoom.OnEventConnect.connect(self.myOnEventConnect)
        self.objKiwoom.OnReceiveRealData.connect(self.myOnReceiveRealData)
        self.objKiwoom.OnReceiveTrData.connect(self.myOnReceiveTrData)

        # 위젯 이벤트 연결
        self.loadCurrButton.clicked.connect(self.loadCurrButton_clicked)
        self.loadRandomButton.clicked.connect(self.loadRandomButton_clicked)
        self.loadAllButton.clicked.connect(self.loadAllButton_clicked)
        self.loadStrongButton.clicked.connect(self.loadStrongButton_clicked)
        self.loadTypeButton.clicked.connect(self.loadTypeButton_clicked)

        self.refreshChartButton.clicked.connect(self.refreshChartButton_clicked)

    def doInit(self):
        if SKIP_LOGIN == 0:
            self.setCodeList()  # 코드 리스트 초기화
            self.regRealItem()  # 실시간 등록
        else:
            self.loadCodeList()

        # 각 종목코드에 대한 저장 클래스의 객체를 만든다.
        for code in self.codes:
            if SKIP_LOGIN==0:
                name = self.objKiwoom.dynamicCall("GetMasterCodeName(str)", code)
                #market = self.objKiwoom.dynamicCall("KOA_Functions(str, str)", "GetMasterStockInfo", code).split(";")[0].split("|")[1]
                self.datas[code] = RealData(code, name, self)
                self.names.append(name)
                self.nameToCode[name] = code

                nStockCount = int(self.objKiwoom.dynamicCall("GetMasterListedStockCnt(str)", code))
                self.datas[code].updateStockCount(nStockCount)

                nLastVal = int(self.objKiwoom.dynamicCall("GetMasterLastPrice(str)", code))
                self.datas[code].updateMarketCap(nLastVal)

        self.loadConditionFile()    # 조건식 세팅
        self.loadUserConfig()               # 최근 세팅 로드
        self.loadTypeFile()
        #self.loadEffectiveStockCount()
        self.loadDayData()
        #self.loadTradeDataAll()        
        #self.loadSector()   # 섹터 로드
        self.setMarketSector()
        self.appendDayTable()

        #self.checkNoEffectiveStockCountCase()
        self.checkNoLatestDayData()

        # 종목코드나 종목명 입력시 자동 완성 기능을 적용한다.
        completer = QCompleter(self.codes + self.names)
        self.labelEditDict['종목명'].setCompleter(completer)

        listAccountNo = self.objKiwoom.dynamicCall("GetLoginInfo(QString)", "ACCNO").rstrip(';').split(';')
        self.accountNo = listAccountNo[0]
        print(f"계좌 : {self.accountNo}")

        self.updateGUI()
        self.loadCurrButton.setEnabled(True)
        self.loadRandomButton.setEnabled(True)
        self.loadAllButton.setEnabled(True)
        self.loadStrongButton.setEnabled(True)
        self.loadTypeButton.setEnabled(True)

        # Program 실시간 등록
        #if SKIP_LOGIN == 0:
        #    self.reqOpt90004_list.append([True, 0])   # 코스피
        #    self.reqOpt90004_list.append([False, 0])  # 코스닥
        #print(f"프로그램 실시간 등록 시작")

        self.initDone = True
        self.장마감_일봉로드 = False
        self.동시호가전_데이터정리 = False

        self.load_data_list = []
        self.buy_list = []
        self.sell_list = []
        self.save_data_list = []

    # 코드 리스트를 설정한다.
    def setCodeList(self):
        # KOSPI(0), KOSDAQ(10) List
        codeText = self.objKiwoom.dynamicCall("GetCodeListByMarket(str)", "0") \
                   + self.objKiwoom.dynamicCall("GetCodeListByMarket(str)", "10")
        for code in codeText[:-1].split(";"):  # 복수개의 코드를 등록한다. 코드간 ";"로 구분한다.
            self.temp_codes[code] = self.objKiwoom.dynamicCall("GetMasterCodeName(str)", code)

        # 코드순으로 된 순서를 이름으로 정렬
        self.temp_codes = sorted(self.temp_codes.items(), key=lambda item: item[1])

        # ETF List
        codeText = self.objKiwoom.dynamicCall("GetCodeListByMarket(str)", "8")
        etf_codes = codeText[:-1].split(";")

        # 증거금100% / 우선주 / ETF / 스팩 제외
        for code, name in self.temp_codes:
            # '증거금20%'|'담보대출'|'신용가능'] 순서로 리턴 받음
            증거금 = self.objKiwoom.dynamicCall("GetMasterStockState(str)", code).split('|')[0]

            # 코드 끝자리가 0이 아니면 우선주나 기타
            if 증거금 != "증거금100%" and code[-1] == '0' and (code not in etf_codes) and ("스팩" not in name):
            #if code[-1] == '0' and (code not in etf_codes) and ("스팩" not in name):
                self.codes.append(code)

    # self.codes에 저장되어 있는 종목코드를 실시간 등록한다.
    def regRealItem(self):
        # 키움은 스크린번호당 100개까지 등록 가능 --> 한 스크린 번호당 100개씩 등록한다.
        nLength = len(self.codes)  # 전체 종목수
        nReqScrNo = int(nLength / 100) + 1  # 100개 단위 필요 스크린 수, +1 --> 100개 단위를 모으고 남은 자투리 항목용

        for i in range(nReqScrNo):
            sScreenNo = f"7{i:03}"  # 스크린 이름, 이름은 서로 구분만 되면 됨
            start = i * 100
            end = start + 100
            sCodes = ";".join(self.codes[start:end])  # 100개의 종목 문자열을 하나의 문자열로 만든다.
            # 41~50: 매도호가1~10 | 51~60: 매수호가1~10 |
            # 61~70: 매도호가수량1~10 | 71~80: 매수호가수량1~10 |
            # 81~90: 매도호가직전대비 | 91~100: 매수호가직전대비
            #'41;42;43;44;45;46;47;48;49;50;' \
            #'51;52;53;54;55;56;57;58;59;60' \            
            #'61;62;63;64;65;66;67;68;69;70;' \
            #'71;72;73;74;75;76;77;78;79;80;' \
            # '81;82;83;84;85;86;87;88;89;90;'  \
            # '91;92;93;94;95;96;97;98;99;100'
            # 228 - 체결강도
            # 311 - 시가총액
            # 30 - 전일대비거래량
            # 16 시가 17 고가 18 저가

            sFidList = '20;10;12;15;21;121;125;'
            for i in range(41,81,1):
                sFidList += f'{i};'
            
            for i in range(5):
                sFidList += f"{141+i};"     # 매도거래원 - 141~145
            for i in range(5):
                sFidList += f"{161+i};"     # 매도거래원수량 - 161~165
            for i in range(5):
                sFidList += f"{166+i};"     # 매도거래원별증감 - 166~170
            for i in range(5):
                sFidList += f"{151+i};"     # 매수거래원 - 151~155
            for i in range(5):    
                sFidList += f"{171+i};"     # 매수거래원수량 - 171~175
            for i in range(5):    
                sFidList += f"{176+i};"     # 매수거래원별증감 - 176~180

            self.objKiwoom.dynamicCall("SetRealReg(str, str, str, str)", sScreenNo, sCodes, sFidList, "0")

        self.statusBar.showMessage(f"실시간 등록 완료 - 종목수 : {len(self.codes)} | "
                                   f"RAM Usage : {str(psutil.virtual_memory().percent)}%")

    # 수신 Event 함수 (로그인 이벤트)
    # 로그인 성공시 실시간 등록을 실행한다(실시간 등록 함수는 로그인 되어야 사용가능).
    # 로그인 실패시 종료한다.
    def myOnEventConnect(self, nErrCode):
        if nErrCode == 0:
            self.statusBar.showMessage("로그인 OK")
            self.doInit()
        else:  # 로그인 실패시 --> 종료시켜 버림
            self.statusBar.showMessage(f"Error[{nErrCode}]")
            QCoreApplication.instance().quit()

    # 실시간 수신 이벤트
    def myOnReceiveRealData(self, sCode, sRealType, sRealData):
        # '주식 체결'만 데이터를 저장한다. '주식 시세'는 고려하지 않음
        if sRealType == "주식체결":
            try:
                체결시간 = int(self.objKiwoom.dynamicCall("GetCommRealData(str, int)", sCode, '20'))  # HHMMSS
                현재가 = abs(int(self.objKiwoom.dynamicCall("GetCommRealData(str, int)", sCode, '10')))
                등락율 = float(self.objKiwoom.dynamicCall("GetCommRealData(str, int)", sCode, '12'))
                거래량 = int(self.objKiwoom.dynamicCall("GetCommRealData(str, int)", sCode, '15'))
                if sCode in self.codes:
                    self.pushRealData(sCode, 체결시간, 현재가, 등락율, 거래량)
            # 일반 TR을 전송해도 전송한 코드에 대해 실시간 등록을 하지 않아도 Real이벤트가 발생한다.
            # 따라서 해당 코드에 대해 처리되지 않으면 오류가 발생한다. 이를 걸러 주기 위해 예외로 대응함
            except Exception as e:
                print(f"*E: {datetime.datetime.now().strftime('%H:%M:%S')} | Real Data Load Error(주식체결) | sRealType={sRealType} | sCode={sCode} : {e}")
        elif sRealType == "주식당일거래원":
            try:
                매도거래원, 매도거래원수량, 매도거래원증감 = [], [], []
                매수거래원, 매수거래원수량, 매수거래원증감 = [], [], []
                for i in range(5):
                    fidCode = str(141+i)    # 매도거래원 - 141~145
                    매도거래원.append( self.objKiwoom.dynamicCall("GetCommRealData(str, int)", sCode, fidCode) )
                for i in range(5):
                    fidCode = str(161+i)    # 매도거래원수량 - 161~165
                    매도거래원수량.append( abs(int(self.objKiwoom.dynamicCall("GetCommRealData(str, int)", sCode, fidCode))) )
                for i in range(5):
                    fidCode = str(166+i)    # 매도거래원증감 - 166~170
                    매도거래원증감.append(abs(int(self.objKiwoom.dynamicCall("GetCommRealData(str, int)", sCode, fidCode))))
                for i in range(5):
                    fidCode = str(151+i)    # 매수거래원 - 151~155
                    매수거래원.append( self.objKiwoom.dynamicCall("GetCommRealData(str, int)", sCode, fidCode) )
                for i in range(5):
                    fidCode = str(171+i)    # 매수거래원수량 - 171~175
                    매수거래원수량.append(abs(int(self.objKiwoom.dynamicCall("GetCommRealData(str, int)", sCode, fidCode))))
                for i in range(5):
                    fidCode = str(176+i)    # 매수거래원증감 - 176~180
                    매수거래원증감.append(abs(int(self.objKiwoom.dynamicCall("GetCommRealData(str, int)", sCode, fidCode))))
                if sCode in self.codes:
                    self.datas[sCode].거래원추가(매도거래원, 매도거래원수량, 매도거래원증감, 매수거래원, 매수거래원수량, 매수거래원증감)
                    #print(f"*D: {datetime.datetime.now().strftime('%H:%M:%S')} | 거래원데이터 | {sCode} | {self.datas[sCode].name} | sRealType={sRealType} | {sRealData}")
            except Exception as e:
                print(f"*E: {datetime.datetime.now().strftime('%H:%M:%S')} | Real Data Load Error(주식당일거래원) | sRealType={sRealType} | sCode={sCode} : {e}")
        elif sRealType == "주식호가잔량":
            try:
                매도호가, 매수호가 = [], []
                매도호가수량, 매수호가수량 = [], []
                매도호가합 = int(self.objKiwoom.dynamicCall("GetCommRealData(str, int)", sCode, '121'))
                매수호가합 = int(self.objKiwoom.dynamicCall("GetCommRealData(str, int)", sCode, '125'))
                #매도호가변동 = int(self.objKiwoom.dynamicCall("GetCommRealData(str, int)", sCode, '122'))
                #매수호가변동 = int(self.objKiwoom.dynamicCall("GetCommRealData(str, int)", sCode, '126'))
                #매도호가수량1 = int(self.objKiwoom.dynamicCall("GetCommRealData(str, int)", sCode, '61'))
                #매수호가수량1 = int(self.objKiwoom.dynamicCall("GetCommRealData(str, int)", sCode, '71'))
                #매도호가변동1 = int(self.objKiwoom.dynamicCall("GetCommRealData(str, int)", sCode, '81'))
               # 매수호가변동1 = int(self.objKiwoom.dynamicCall("GetCommRealData(str, int)", sCode, '91'))
                호가시간 = int(self.objKiwoom.dynamicCall("GetCommRealData(str, int)", sCode, '21'))
                if sCode in self.codes:
                    ## 41~50: 매도호가1~10
                    for i in range(10):
                        fidCode = str(41+i)
                        매도호가.append(abs(int(self.objKiwoom.dynamicCall("GetCommRealData(str, int)", sCode, fidCode))))
                    ## 51~60: 매수호가1~10 |
                    for i in range(10):
                        fidCode = str(51+i)
                        매수호가.append(abs(int(self.objKiwoom.dynamicCall("GetCommRealData(str, int)", sCode, fidCode))))
                    ## 61~70: 매도호가수량1~10 
                    for i in range(10):
                        fidCode = str(61+i)
                        매도호가수량.append(abs(int(self.objKiwoom.dynamicCall("GetCommRealData(str, int)", sCode, fidCode))))
                    ## 71~80: 매수호가수량1~10 
                    for i in range(10):
                        fidCode = str(71 + i)
                        매수호가수량.append(abs(int(self.objKiwoom.dynamicCall("GetCommRealData(str, int)", sCode, fidCode))))

                    매도호가대금, 매수호가대금 = 0, 0
                    for i in range(10):
                        매도호가대금 += 매도호가[i]*매도호가수량[i]
                        매수호가대금 += 매수호가[i]*매수호가수량[i]

                    #if 호가시간>MARKET_OPEN_TIME and (매도호가합==0 and 매수호가합==0):
                    #    print(f"*D: {datetime.datetime.now().strftime('%H:%M:%S')} | 호가데이터 | {sCode} | {self.datas[sCode].name} | sRealType={sRealType} | 매도호가합={매도호가합} | 매수호가합={매수호가합}")

                    if 호가시간 < 시각_동시호가:
                        self.datas[sCode].updateHoga(호가시간, 매도호가합, 매수호가합, 매도호가[0], 매수호가[0], 매도호가대금, 매수호가대금)

                    # 매도호가수량 제일 많은거 체크
                    #근접매도호가수량 = 매도호가수량[0] + 매도호가수량[1] + 매도호가수량[2]

                    # 매수호가수량 제일 많은거 체크
                    #근접매수호가수량 = 매수호가수량[0] + 매수호가수량[1] + 매수호가수량[2]
            except Exception as e:
                print(f"*E: {datetime.datetime.now().strftime('%H:%M:%S')} | Real Data Load Error(주식호가잔량) | sRealType={sRealType} | sCode={sCode} : {e}")

        elif sRealType == "종목프로그램매매":
            #print(f"RealData Receive : sCode={sCode}")
            try:
                순매수수량 = int(self.objKiwoom.dynamicCall("GetCommRealData(str, int)", sCode, '210'))
                체결시간 = int(self.objKiwoom.dynamicCall("GetCommRealData(str, int)", sCode, '20'))  # HHMMSS
                누적거래량 = int(self.objKiwoom.dynamicCall("GetCommRealData(str, int)", sCode, '13'))
                #print(f"체결시간={체결시간} | 누적거래량={누적거래량} | 순매수수량={순매수수량}")
                # 212 : 순매수 금액

                if sCode in self.codes:
                    self.datas[sCode].updateProgram(체결시간, 순매수수량)
                #else:
                    #print(f"*W : sCode={sCode} is Not in code list")

            except Exception as e:
                print(f"*E: {datetime.datetime.now().strftime('%H:%M:%S')} | Real Data Load Error(종목프로그램매매): {e}")
        elif sRealType in ["ECN주식호가잔량", "주식시간외호가", "주식예상체결", "ECN주식체결", "시간외종목정보", "주식우선호가", "주식종목정보", "주식시세"]:
            pass
        else:
            print(f"*D: {datetime.datetime.now().strftime('%H:%M:%S')} | Not Intended Real Data Detected. sCode={sCode} | sRealType={sRealType} | sRealData={sRealData}")

        # elif sRealType == "선물시세":

    def myOnReceiveTrData(self, sScreenNo, sRqName, sTrCode, sRecordName, sPreNext):
        print(f"Screen No : {sScreenNo} | Rq Name : {sRqName} | Tr Code : {sTrCode} | Record Name : {sRecordName} | PreNext : {sPreNext}")

        if sRqName == "주식일봉차트조회" or sRqName == "주식일봉차트조회단일":
            dataCount = self.objKiwoom.dynamicCall("GetRepeatCnt(str, str)", sTrCode, sRqName)
            code = self.objKiwoom.GetCommData(sTrCode, sRqName, 0, "종목코드").lstrip()
            #print(f"총데이터 수: {dataCount} | 종목코드: {code}")
            #print("------------------------------")
            if code == '':
                return
            # 가장최근에서 300 거래일 전까지 데이터 조회
            tempStr = "일자,거래량,거래대금,시가,고가,저가,현재가"
            for dataIdx in range(min(dataCount, NUM_LOAD_DATE)-1, -1, -1):  # 과거일자부터 write
                inputVal = ["일자", '거래량', "거래대금", "시가", "고가", "저가", "현재가"]
                outputVal = ['', '', '', '', '', '', '']
                tempStr = f"{tempStr}\n"
                for idx, j in enumerate(inputVal):
                    outputVal[idx] = self.objKiwoom.GetCommData(sTrCode, sRqName, dataIdx, j).lstrip()
                for x in outputVal:
                    tempStr = f"{tempStr}{x},"

            DATE_FILE = f"{DAY_DIR_NAME}/{self.datas[code].name}.csv"

            try:
                with open(DATE_FILE, "w") as f:
                    f.write(tempStr)
                    print(f"{DATE_FILE} File writting complete @ {datetime.datetime.now().strftime('%H:%M:%S')}")
            except Exception as e:
                print(f"File writting error : {e}")

            #if sRqName == "주식일봉차트조회단일" and len(self.datas[code].dayDatas.종가)==0:
            if sRqName == "주식일봉차트조회단일":
                self.loadDayDataSingle(code)
        elif sTrCode == "opt90004":
            dataCount = self.objKiwoom.dynamicCall("GetRepeatCnt(str, str)", sTrCode, sRqName)
            code = self.objKiwoom.GetCommData(sTrCode, sRqName, 0, "종목코드").lstrip()
            #print(f"총데이터 수: {dataCount} | 종목코드: {code}")
            #print("------------------------------")
            #for dataIdx in range(dataCount):
            #    inputVal = ["종목명", "종목코드", "순매수대금", "전체거래비율"]
            #    outputVal = ['', '', '', '']
                #for idx, j in enumerate(inputVal):
                #    outputVal[idx] = self.objKiwoom.GetCommData(sTrCode, sRqName, dataIdx, j).lstrip()
                #print(outputVal)
            if sPreNext == "2":
                if sRqName == "코스피":    self.reqOpt90004_list.append([True, 2])
                else:                     self.reqOpt90004_list.append([False, 2])
        elif sTrCode == "opt10001":
            try:
                code = self.objKiwoom.GetCommData(sTrCode, sRqName, 0, "종목코드").lstrip()
                유통주식수 = 1000*int(self.objKiwoom.GetCommData(sTrCode, sRqName, 0, "유통주식").lstrip())  # 천단위
                self.datas[code].유통주식수 = 유통주식수
                print(f"종목코드={code} | 주식수={self.datas[code].주식수} | "
                      f"유통비율={round(safeDivide(self.datas[code].유통주식수, self.datas[code].주식수, 0),2)} | 유통주식수={self.datas[code].유통주식수}")
                self.datas[code].saveEffectiveStockCount()
            except Exception as e:
                print(f"유통주식 받기 실패 {self.datas[code].name} : {e}")
        else:
            print(f"*D: {datetime.datetime.now().strftime('%H:%M:%S')} | Not Intended TR Data Detected. {sRqName} | {sTrCode} | {sRecordName} | {sPreNext}")

    def pushRealData(self, sCode, 체결시간: int, 현재가: int, 등락율: float, 거래량: int):
        if 체결시간 < MARKET_OPEN_TIME or 체결시간 >= MARKET_CLOSE_TIME:
            return

        self.datas[sCode].append(체결시간, 현재가, 등락율, 거래량)

        #if 체결시간 - self.datas[sCode].tableUpdateTime >= TABLE_UPDATE_PERIOD or 체결시간 >= MARKET_CLOSE_TIME:
        #    self.datas[sCode].tableUpdateTime = 체결시간
        #    for i in range(NUM_TABLE):
        #        if sCode in list(self.tableArray[i].topList.keys()):
        #            self.tableArray[i].updateTable(self.tableArray[i].topList[sCode], self.datas[sCode])

    def loadConditionFile(self):
        FileName = 조건식_파일

        try:
            with open(FileName, 'r') as f:
                rdr = f.readlines()
                condName = ''
                for count, line_raw in enumerate(rdr):
                    line_raw = line_raw.rstrip(',')
                    line = line_raw.split(',')
                    if line[0] == 'EOL': # 끝줄
                        break
                    elif line[0] == '조건식명': # 새 조건식 시작
                        condName = line[1]
                        self.조건식[condName] = {}
                        self.조건식_만족_종목들[condName] = []
                    elif line[0] == '':
                        pass
                    else: # 서브 조건들
                        cond = line[0]
                        if cond=="기준봉":
                            self.조건식[condName][cond] = {}
                            for i in range(1, len(line)-1, 2):
                                if line[i]!='':
                                    기준봉_조건 = line[i].rstrip(' ')
                                    기준봉_값 = line[i+1].rstrip('\n')
                                    #print(f"DEBUG 기준봉: 조건={기준봉_조건} | 값={기준봉_값}")
                                    self.조건식[condName][cond][기준봉_조건] = float(기준봉_값)
                        elif cond=="종목타입":
                            종목타입 = line[1]
                            self.조건식[condName][cond] = 종목타입
                        #elif cond=="단일조건":
                        else:
                            조건값 = line[1].rstrip('\n')
                            #print(f"DEBUG: 조건={cond} | 값={조건값}")
                            self.조건식[condName][cond] = float(조건값)

                print(f"조건식 파일 읽기 완료({FileName}) at {datetime.datetime.now().strftime('%H:%M:%S')}")
                f.close

                #print(self.조건식)
                for key in self.조건식.keys():
                    print(f"<<<< 조건식 = {key} >>>>")
                    for cond, value in self.조건식[key].items():
                        print(f"세부조건:{cond} = {value}")
                    self.combo.addItem(key)
                    for i in range(NUM_TABLE):
                        self.tableArray[i].combo.addItem(key)
                    print("")
                self.combo.setCurrentIndex(0)

        except Exception as e:
            print(f"File Load error @ loadDayDataSingle {FileName} : {e}")

    def printCondition(self):
        조건식명 = self.combo.currentText()
        print(f"조건식명 = {조건식명}")
        for key in self.조건식[조건식명].keys():
            print(f"Key={key} {self.조건식[조건식명][key]}")
        print("조건식_만족_종목들")
        print(self.조건식_만족_종목들[조건식명])
        codeList = self.조건식_만족_종목들[조건식명]
        for val in codeList:
            print(val[1])
            print(self.datas[val[0]].조건식_만족시각)
            print(self.datas[val[0]].조건식_값들)    



    # UI를 구성한다
    def initUI(self):
        self.setWindowTitle("MOON BOT")
        #self.resize(2200, 1200)
        #self.setGeometry(0, 30, 700, 1300)
        #self.centralwidget = QWidget(self)

        #self.sectorWindow = SubWindow(self, 700, 30, 480, 1300, "종목들")
        #self.dayGraphWindow = SubWindow(self, 700+480, 30, MINUTE_GRAPH_WIDTH, 290, "일봉")
        #self.minuteGraphWindow = SubWindow(self, 700+480, 30+320, MINUTE_GRAPH_WIDTH, 1040, "분봉")

        self.setGeometry(0, 30, MAIN_TABLE_WIDTH, 600)
        self.centralwidget = QWidget(self)
        #self.condWindow = SubWindow(self, 0, 500, 700, 200, "조건식")
        self.sectorWindow = SubWindow(self, 0, 30+30+600, MAIN_TABLE_WIDTH, 730, "종목들")
        self.dayGraphWindow = SubWindow(self, MAIN_TABLE_WIDTH, 30, MINUTE_GRAPH_WIDTH, 290, "일봉")
        self.minuteGraphWindow = SubWindow(self, MAIN_TABLE_WIDTH, 30+320, MINUTE_GRAPH_WIDTH, 1040, "분봉")


        #self.dayGraphWindow.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        #self.dayGraphWindow.setWindowFlags(Qt.FramelessWindowHint)

        # 메뉴액션
        exitAction = QAction('Exit', self)
        exitAction.triggered.connect(self.exitApp)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')

        initTradeDataAction = QAction('Init Trade Data', self)
        saveTradeDataAction = QAction('Save Trade Data', self)
        initTradeDataAction.triggered.connect(self.initTradeDataAll)
        saveTradeDataAction.triggered.connect(self.saveTradeDataAll)

        getDayDataAction = QAction('일데이터 얻기', self)
        getDayDataAction.triggered.connect(self.getDayData)
        checkNoLatestDayDataForTodayAction = QAction('일데이터 체크(미)', self)
        checkNoLatestDayDataForTodayAction.triggered.connect(self.checkNoLatestDayDataForToday)
        getEffectiveStockCountAction = QAction('유통주식 얻기', self)
        getEffectiveStockCountAction.triggered.connect(self.getEffectiveStockCount)

        viewDayGraphWindowAction = QAction('일봉 창 열기', self)
        viewDayGraphWindowAction.triggered.connect(self.viewDayGraphWindow)
        viewMinuteGraphWindowAction = QAction('분봉 창 열기', self)
        viewMinuteGraphWindowAction.triggered.connect(self.viewMinuteGraphWindow)
        viewSectorWindowAction = QAction('섹터 창 열기', self)
        viewSectorWindowAction.triggered.connect(self.viewSectorWindow)

        # 메뉴바
        self.menubar = self.menuBar()
        self.menubar.setNativeMenuBar(False)
        self.fileMenu = self.menubar.addMenu('&File')
        self.fileMenu.addAction(exitAction)
        self.getDataMenu = self.menubar.addMenu('&Get Data')
        self.getDataMenu.addAction(getDayDataAction)
        self.getDataMenu.addAction(checkNoLatestDayDataForTodayAction)
        self.getDataMenu.addAction(getEffectiveStockCountAction)
        self.tradeDataMenu = self.menubar.addMenu('&Trade Data')
        self.tradeDataMenu.addAction(initTradeDataAction)
        self.tradeDataMenu.addAction(saveTradeDataAction)
        self.viewMenu = self.menubar.addMenu('&View')
        self.viewMenu.addAction(viewDayGraphWindowAction)
        self.viewMenu.addAction(viewMinuteGraphWindowAction)
        self.viewMenu.addAction(viewSectorWindowAction)

        # 상태표시줄 설정 ---------------------------------------------
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready...")

        self.dummyLabel = QLabel('    ')

        # 버튼 설정
        self.loadCurrButton = QPushButton("복기(선택종목)", self.centralwidget)
        self.loadRandomButton = QPushButton("랜덤복기", self.centralwidget)
        self.loadAllButton = QPushButton("모두복기", self.centralwidget)
        self.loadStrongButton = QPushButton("강한놈복기", self.centralwidget)
        self.loadTypeButton = QPushButton("타입복기", self.centralwidget)

        # 로그인 전까지 버튼을 사용할 수 없게 한다.
        self.loadCurrButton.setEnabled(False)
        self.loadRandomButton.setEnabled(False)
        self.loadAllButton.setEnabled(False)
        self.loadStrongButton.setEnabled(False)
        self.loadTypeButton.setEnabled(False)

        # 버튼 딕셔너리
        self.buttonDict = {}

        # 체크박스 딕셔너리
        self.checkBoxDict, self.checkBoxDictSub = {}, {}
        for key in CHECK_BOX_KEY:
            self.checkBoxDict[key] = CheckBox(self, key)
        
        for key in CHECK_BOX_KEY_SUB:
            self.checkBoxDictSub[key] = CheckBox(self, key)

        # Label + Edit 딕셔너리
        self.labelEditDict = {}
        for i, key in enumerate(LABEL_EDIT_KEY):
            self.labelEditDict[key] = LabelEdit(self, '메인', key, LABEL_EDIT_INIT[i], WIDTH_EDIT_BOX)

        self.refreshChartButton = QPushButton("▽", self.centralwidget)
        self.refreshChartButton.setMaximumWidth(50)

        self.plot, self.dayPlot, self.sectorPlot = [], [], []

        self.graph = pg.GraphicsLayoutWidget()
        self.graph.setBackground(COLOR_IVORY)
        for i in range(NUM_GRAPH):
            showValue = False if i>0 else True
            self.plot.append(self.graph.addPlot(row=i, col=0, axisItems={'bottom': pg.DateAxisItem(showValues=showValue)}))
            self.plot[i].showGrid(x=True, y=True)
            self.plot[i].setRange(xRange=[0, WHOLE_DAY_SEC])
            self.plot[i].getAxis('left').setWidth(GRAPH_YAXIS_WIDTH)

        self.graph.ci.layout.setRowStretchFactor(0, 25)
        for i in range(1, NUM_GRAPH):
            self.graph.ci.layout.setRowStretchFactor(i, 5)

        self.dayGraph = pg.GraphicsLayoutWidget()
        self.dayGraph.setBackground(COLOR_IVORY)
        for i in range(NUM_DAYGRAPH):
            self.dayPlot.append(self.dayGraph.addPlot(row=i, col=0, axisItems={'bottom': pg.DateAxisItem(showValues=False)}))
            self.dayPlot[i].showGrid(x=True, y=True)
            self.dayPlot[i].enableAutoRange()

        self.dayGraph.ci.layout.setRowStretchFactor(0, 30)
        for i in range(1, NUM_DAYGRAPH):
            self.dayGraph.ci.layout.setRowStretchFactor(i, 5)

        #self.sectorGraph = pg.GraphicsLayoutWidget()
        #self.sectorGraph.setBackground(COLOR_IVORY)
        #for i in range(NUM_SECTORGRAPH):
        #    self.sectorPlot.append(self.sectorGraph.addPlot(row=i, col=0, axisItems={'bottom': pg.DateAxisItem()}))
        #    self.sectorPlot[i].showGrid(x=True, y=True)
        #    self.sectorPlot[i].setRange(xRange=[0, WHOLE_DAY_SEC])

        # 조건식 콤보박스
        self.combo = QComboBox()
        self.combo.setMaximumWidth(120)
        self.combo.currentIndexChanged.connect(self.printCondition)

        # 종목타입 콤보박스
        self.codeTypeCombo = QComboBox()
        self.codeTypeCombo.setMaximumWidth(120)

        # 레이아웃 배치 ---------------------------------------------
        self.codeLayout = QGridLayout()
        self.codeLayout.addLayout(self.labelEditDict['종목명'].layout, 0, 0)
        self.codeLayout.addLayout(self.labelEditDict['복기날짜'].layout, 1, 0)
        self.codeLayout.addLayout(self.labelEditDict['랜덤복기개수'].layout, 1, 1)
        self.codeLayout.addWidget(self.combo, 0, 1)
        self.codeLayout.addWidget(self.loadCurrButton, 0, 2)
        self.codeLayout.addWidget(self.codeTypeCombo, 0, 3)
        self.codeLayout.addWidget(self.loadTypeButton, 0, 4)
        self.codeLayout.addWidget(self.loadRandomButton, 1, 2)
        self.codeLayout.addWidget(self.loadAllButton, 1, 3)
        self.codeLayout.addWidget(self.loadStrongButton, 1, 4)
        self.codeLayout.addWidget(self.dummyLabel, 1, 5)
        self.codeLayout.addWidget(self.dummyLabel, 2, 0)
        self.codeLayout.setColumnStretch(5, 1)

        # Table / Condition 생성
        self.tableArray = []
        for i in range(NUM_TABLE):
            self.tableArray.append(Table(self, i))

        self.tableLayout1 = QGridLayout()

        for i in range(NUM_TABLE):
            self.tableLayout1.addLayout(self.tableArray[i].layout, i, 0)

        #self.dayTable = DayTable(self, "전체 종목들", ["등락율","거래증가","누적대금","순대금","P대금",'회전율',"순회전율","P회전율"], [45, 55, 55, 55, 55, 50, 50])
        self.dayTable = DayTable(self, "전체 종목들")

        self.checkBoxLayout = QGridLayout()
        for idx, key in enumerate(CHECK_BOX_KEY):
            self.checkBoxLayout.addWidget(self.checkBoxDict[key].checkBox, 0, idx)

        self.checkBoxLayout.addWidget(self.dummyLabel, 0, len(CHECK_BOX_KEY))
        self.checkBoxLayout.addLayout(self.labelEditDict['분봉초'].layout, 0, len(CHECK_BOX_KEY)+1)
        self.checkBoxLayout.addWidget(self.refreshChartButton, 0, len(CHECK_BOX_KEY)+2)
        self.checkBoxLayout.setColumnStretch(len(CHECK_BOX_KEY), 1)

        self.checkBoxLayoutSub = QGridLayout()
        for idx, key in enumerate(CHECK_BOX_KEY_SUB):
            if idx < 12: self.checkBoxLayoutSub.addWidget(self.checkBoxDictSub[key].checkBox, 0, idx)
            else:        self.checkBoxLayoutSub.addWidget(self.checkBoxDictSub[key].checkBox, 1, idx-12)
        self.checkBoxLayoutSub.addWidget(self.dummyLabel, 0, len(CHECK_BOX_KEY_SUB))
        self.checkBoxLayoutSub.setColumnStretch(len(CHECK_BOX_KEY_SUB), 1)

        self.dayGraphLayout, self.dayTopGraphLayout = QGridLayout(), QGridLayout()
        #self.dayTopGraphLayout.addWidget(self.dummyLabel, 0, 2)
        #self.dayTopGraphLayout.setColumnStretch(2, 1)

        self.dayTableLayout = QGridLayout()
        self.dayTableLayout.addLayout(self.dayTable.layout, 0, 0)

        self.dayGraphWindow.layout.addWidget(self.dayGraph, 0, 0)

        #self.sectorWindow.layout.addWidget(self.sectorGraph, 0, 0)
        self.sectorWindow.layout.addLayout(self.dayTableLayout, 0, 0)
        #self.sectorWindow.layout.setRowStretch(0, 3)
        #self.sectorWindow.layout.setRowStretch(1, 10)

        self.graphLayout = QGridLayout()
        self.graphLayout.addWidget(self.graph, 0, 0)

        self.scrollStep = 1 
        self.zoomRatio = 1 # 0~1
        self.scrollbar = QScrollBar(Qt.Horizontal, sliderMoved=self.onAxisSliderMoved, valueChanged=self.onAxisSliderMoved, pageStep=self.scrollStep* self.zoomRatio * 100, )
        #self.onAxisSliderMoved(self.scrollbar.value())
        self.zoomSlider = QSlider(Qt.Horizontal, sliderMoved=self.onZoomSliderMoved, valueChanged=self.onZoomSliderMoved)
        
        #self.rightLayout = QGridLayout()
        #self.rightLayout.addLayout(self.checkBoxLayout, 0, 0)
        #self.rightLayout.addLayout(self.graphLayout, 1, 0)
        self.minuteGraphWindow.layout.addLayout(self.checkBoxLayout, 0, 0)
        self.minuteGraphWindow.layout.addLayout(self.graphLayout, 1, 0)
        self.minuteGraphWindow.layout.addLayout(self.checkBoxLayoutSub, 2, 0)
        self.minuteGraphWindow.layout.addWidget(self.scrollbar)
        self.minuteGraphWindow.layout.addWidget(self.zoomSlider)

        self.tableLayout = QGridLayout()
        self.tableLayout.addLayout(self.tableLayout1, 0, 0)
        self.leftLayout = QGridLayout()

        self.entireLayout = QGridLayout(self.centralwidget)
        self.leftLayout.addLayout(self.codeLayout, 0, 0)
        self.leftLayout.addLayout(self.tableLayout, 2, 0)
        #self.entireLayout.addLayout(self.dayGraphLayout, 0, 0)
        #self.entireLayout.addLayout(self.rightLayout, 0, 0)
        self.entireLayout.addLayout(self.leftLayout, 0, 0)
        #self.entireLayout.setColumnStretch(0, 7)
        #self.entireLayout.setColumnStretch(0, 6)
        #self.entireLayout.setColumnStretch(0, 3)

        # 레이아웃 설정
        self.setCentralWidget(self.centralwidget)

        self.sectorWindow.show()
        self.minuteGraphWindow.show()
        self.dayGraphWindow.show()
        #self.condWindow.show()

    # 그래프 그리기
    def drawMinuteGraph(self):
        if self.selectedCode != -1:
            danjuPlusTime, danjuPlusValue, danjuPlusPrice = [], [], []
            danjuMinusTime, danjuMinusValue, danjuMinusPrice = [], [], []

            realData:RealData = self.datas[self.selectedCode]
            dayData = realData.dayDatas
            pData = realData.periodicData
            fastData = realData.fastData
            #oneSecData = realData.oneSecData

            if len(realData.체결배열) > 0:
                for key, value in realData.체결배열.items():
                    if len(value.danjuTime) > MIN_DANJU_FILTER:    # 훼이크 필터링
                        if key > 0:
                            for i, t in enumerate(value.danjuTime):
                                danjuPlusTime.append(getTsec(t))
                                danjuPlusValue.append(key)
                                danjuPlusPrice.append(value.danjuPrice[i])
                        else:
                            for i, t in enumerate(value.danjuTime):
                                danjuMinusTime.append(getTsec(t))
                                danjuMinusValue.append(key)
                                danjuMinusPrice.append(value.danjuPrice[i])

            x, 고가눌림목, xSector = [], [], []

            idx = 0
            for i in range(고가눌림목_개수):
                고가눌림목.append([])

            for i in range(NUM_GRAPH):
                self.plot[i].clear()

            if len(realData.섹터) > 0:
                sData = self.sectors[realData.섹터[0]]
                if len(sData.시각) > 0:
                    for list in sData.시각:
                        t = str(list)
                        if len(t) == 5:
                            t = f"0{t}"
                        tsec = 3600 * (int(t[0:2]) - 9) + 60 * int(t[2:4]) + int(t[4:6])  # second 형식으로 변환
                        xSector.append(tsec)

            CHART_WIDTH = realData.chartWidth

            # 파바박
            fastDataPlusTime = []
            if len(fastData.result["PlusTime"]) > 0:
                for time in fastData.result["PlusTime"]:
                    fastDataPlusTime.append(getTsec(time))
            
            fastDataMinusTime = []
            if len(fastData.result["MinusTime"]) > 0:
                for time in fastData.result["MinusTime"]:
                    fastDataMinusTime.append(getTsec(time))

            #oneSecDataPlusTime = []
            #if len(oneSecData.result["PlusTime"]) > 0:
            #    for time in oneSecData.result["PlusTime"]:
            #        oneSecDataPlusTime.append(getTsec(time))
            #
            #oneSecDataMinusTime = []
            #if len(oneSecData.result["MinusTime"]) > 0:
            #    for time in oneSecData.result["MinusTime"]:
            #        oneSecDataMinusTime.append(getTsec(time))


            # 큰돈
            bigMoneyPlusTime = []
            if len(realData.큰돈데이터["PlusTime"]) > 0:
                for time in realData.큰돈데이터["PlusTime"]:
                    bigMoneyPlusTime.append(getTsec(time))
            
            bigMoneyMinusTime = []
            if len(realData.큰돈데이터["MinusTime"]) > 0:
                for time in realData.큰돈데이터["MinusTime"]:
                    bigMoneyMinusTime.append(getTsec(time))

            broMoneyPlusTime = []
            if len(realData.형님데이터["PlusTime"]) > 0:
                for time in realData.형님데이터["PlusTime"]:
                    broMoneyPlusTime.append(getTsec(time))
            
            broMoneyMinusTime = []
            if len(realData.형님데이터["MinusTime"]) > 0:
                for time in realData.형님데이터["MinusTime"]:
                    broMoneyMinusTime.append(getTsec(time))

            # 분봉데이터 그리기
            if len(pData.구간VAL["등락율"]) > 0:
                for list in pData.구간VAL["시각"]:
                    t = str(list)
                    if len(t) == 5:
                        t = f"0{t}"
                    tsec = 3600 * (int(t[0:2]) - 9) + 60 * int(t[2:4]) + int(t[4:6])  # second 형식으로 변환
                    x.append(tsec)

                #if self.checkBoxDict['매물대'].flag is True:
                #    self.plot[idx].addItem(HorizontalBarItem(realData.getVolumeProfile(), WHOLE_DAY_SEC, COLOR_YELLOW, COLOR_YELLOW_ALPHA100))

                if self.checkBoxDict['박스권'].flag is True:
                    self.plot[idx].addItem(PeriodCurveItem(x, pData.구간VAL['박스750'], COLOR_BLUE, Qt.DashDotLine))
                    self.plot[idx].addItem(PeriodCurveItem(x, pData.구간VAL['박스625'], COLOR_BLUE, Qt.DashDotLine))
                    self.plot[idx].addItem(PeriodCurveItem(x, pData.구간VAL['박스500'], COLOR_BLUE, Qt.SolidLine))
                    self.plot[idx].addItem(PeriodCurveItem(x, pData.구간VAL['박스375'], COLOR_BLUE, Qt.DashDotLine))
                    self.plot[idx].addItem(PeriodCurveItem(x, pData.구간VAL['박스250'], COLOR_BLUE, Qt.DashDotLine))
                    #for key in pData.구간박스가격.keys():
                    #    self.plot[idx].addItem(
                    #    LegendItem(f"{round(key/1000,3)}", COLOR_BLUE, x[-1]+20, pData.구간박스가격[key][-1], FONT_SIZE_MINUTE_GRAPH))

                #if self.flagAverageRate is True:
                if self.checkBoxDict['이평선'].flag is True:
                    self.plot[idx].addItem(PeriodCurveItem(x, pData.구간이평["현재가"][20], COLOR_BLACK, Qt.SolidLine))
                    #self.plot[idx].addItem(PeriodCurveItem(x, pData.구간이평["현재가"][60], COLOR_PURPLE, Qt.SolidLine))

                if self.checkBoxDict['볼밴'].flag is True:
                    self.plot[idx].addItem(PeriodCurveItem(x, pData.볼밴상단, COLOR_BLACK, Qt.SolidLine))
                    self.plot[idx].addItem(PeriodCurveItem(x, pData.볼밴하단, COLOR_BLACK, Qt.SolidLine))

                if self.checkBoxDict['고점대비'].flag is True:
                    for key in pData.구간고가눌림.keys():
                        self.plot[idx].addItem(PeriodCurveItem(x, pData.구간고가눌림[key], COLOR_DARK_GREEN, Qt.DashDotLine))
                        self.plot[idx].addItem(
                        LegendItem(f"-{key}%", COLOR_DARK_GREEN, x[-1]+20, pData.구간고가눌림[key][-1], FONT_SIZE_MINUTE_GRAPH))

                if self.checkBoxDict['고점후저점'].flag is True:
                    self.plot[idx].addItem(PeriodCurveItem(x, pData.구간VAL['고점후저점'], COLOR_BLUE, Qt.DashDotLine))

                if self.checkBoxDict['평균가'].flag is True:
                    #self.plot[idx].addItem(PeriodCurveItem(x, pData.구간VAL["매수평균가"], COLOR_RED, Qt.SolidLine))
                    #self.plot[idx].addItem(PeriodCurveItem(x, pData.구간VAL["매도평균가"], COLOR_BLUE, Qt.SolidLine))
                    self.plot[idx].addItem(PeriodCurveItem(x, pData.구간VAL["평균가1"], COLOR_DARK_GREEN, Qt.SolidLine, width=1))
                    self.plot[idx].addItem(PeriodCurveItem(x, pData.구간VAL["평균가2"], COLOR_DARK_GREEN, Qt.SolidLine, width=2))
                    self.plot[idx].addItem(PeriodCurveItem(x, pData.구간VAL["평균가3"], COLOR_BLACK, Qt.SolidLine, width=2))
                    #self.plot[idx].addItem(PeriodCurveItem(x, pData.구간VAL["평균가5"], COLOR_RED, Qt.SolidLine, width=2))
                    #self.plot[idx].addItem(PeriodCurveItem(x, pData.구간VAL["평균가10"], COLOR_BLUE, Qt.SolidLine, width=2))
                    #self.plot[idx].addItem(PeriodCurveItem(x, pData.구간VAL['평균가볼밴상단'], COLOR_BLACK, Qt.SolidLine))
                    #self.plot[idx].addItem(PeriodCurveItem(x, pData.구간VAL['평균가볼밴하단'], COLOR_BLACK, Qt.SolidLine))

                if self.checkBoxDict['SuperTrend'].flag is True:
                    self.plot[idx].addItem(PeriodCurveItem(x, pData.구간SPTRD_H['현재가'][10], COLOR_RED, Qt.DashDotLine))
                    self.plot[idx].addItem(PeriodCurveItem(x, pData.구간SPTRD_H2['현재가'][10], COLOR_RED, Qt.DashDotLine))
                    self.plot[idx].addItem(PeriodCurveItem(x, pData.구간SPTRD_L['현재가'][10], COLOR_BLUE, Qt.DashDotLine))
                    self.plot[idx].addItem(PeriodCurveItem(x, pData.구간SPTRD_L2['현재가'][10], COLOR_BLUE, Qt.DashDotLine))
                    self.plot[idx].addItem(PeriodCurveItem(x, pData.구간복합이평['현재가'][10], COLOR_BLACK_ALPHA100, Qt.DashDotLine))

                #if realData.당일고가Price>=dayData.고가120[-1-realData.복기보정값]:
                #    self.plot[idx].addItem(PeriodCurveItem(x, 고가120, COLOR_RED, Qt.SolidLine))

                if realData.복기모드 is True:
                    if len(dayData.저항대) > 1:
                        for val in dayData.저항대[-2]:
                            #rate = 100.0*(val/dayData.종가[-2]-1)
                            if realData.당일고가 >= val and \
                                (realData.당일저가 <= val or dayData.종가[-2] <= val) :
                                self.plot[idx].addItem(LineListItem(x[0], x[-1], [val], COLOR_RED, 2, Qt.DotLine))
                else:
                    if len(dayData.저항대) > 0:
                        for val in dayData.저항대[-1]:
                            #rate = 100.0*(val/dayData.종가[-1]-1)
                            if realData.당일고가 >= val and \
                                (realData.당일저가 <= val or dayData.종가[-1] <= val) :
                                self.plot[idx].addItem(LineListItem(x[0], x[-1], [val], COLOR_RED_ALPHA200, 2, Qt.DotLine))

                if len(realData.dayDatas.고가)> 0:
                    self.plot[idx].addItem(LineListItem(x[0], x[-1], [realData.dayDatas.고가[-1-realData.복기보정값]], COLOR_BLACK_ALPHA200, 2, Qt.DotLine))

                tempMinY = min([realData.당일저가] + [getattr(realData, f'평균가{p}') for p in 평균가_KEYS])
                tempMaxY = max([realData.당일고가] + [realData.당일저가*1.1] + [getattr(realData, f'평균가{p}') for p in 평균가_KEYS])

                if realData.전일종가 != 0:
                    tempLines = []
                    for i in [0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3]:
                        tempVal = round(i*realData.전일종가,1)
                        tempLines.append(tempVal)
                        self.plot[idx].addItem(LegendItem(f"{str(round((i-1)*100))}%",COLOR_GRAY,MARKET_CLOSE_SEC,tempVal*1.003,FONT_SIZE_MINUTE_GRAPH))
                    self.plot[idx].addItem(LineListItem(x[0], x[-1], tempLines, COLOR_GRAY, 1, Qt.SolidLine))

                # 당일 고가선/저가선
                #self.plot[idx].addItem(LineListItem(x[0], x[-1], [realData.당일고가], COLOR_BLACK, 1, Qt.DashDotLine))
                #self.plot[idx].addItem(LegendItem(f"{str(round(safeDivide(100*realData.당일고가, realData.전일종가, 100)-100, 1))}%",
                #                                  COLOR_BLACK, MARKET_CLOSE_SEC, realData.당일고가,FONT_SIZE_MINUTE_GRAPH))
                #self.plot[idx].addItem(
                #    LineListItem(x[0], x[-1], [realData.당일저가], COLOR_BLACK, 1, Qt.DashDotLine))
                #self.plot[idx].addItem(LegendItem(f"{str(round(safeDivide(100 * realData.당일저가, realData.전일종가, 100) - 100, 1))}%",
                #                                  COLOR_BLACK, MARKET_CLOSE_SEC, realData.당일저가, FONT_SIZE_MINUTE_GRAPH))

                if len(realData.섹터) > 0:
                    self.plot[idx].addItem(LegendItem(f"{realData.name} | {realData.복기날짜} | 시총{realData.시가총액}억 | 거래대금{int(realData.누적거래대금)}억 | 회전율{realData.회전율}% | {realData.섹터문자열}",
                                                          COLOR_BROWN, 0, tempMinY, 14))
                else:
                    #self.plot[idx].addItem(LegendItem(f"{realData.name} | {realData.복기날짜} | {realData.시가총액}억 | 유통{realData.유통비율}% ",
                    #                                          COLOR_BROWN, 0, tempMinY, 14))
                    self.plot[idx].addItem(LegendItem(f"{realData.name} | {realData.복기날짜} | 시총{realData.시가총액}억 | 거래대금{int(realData.누적거래대금)}억 | 회전율{realData.회전율}% |",
                                                              COLOR_BROWN, 0, tempMinY, 14))
                # 누적대금 하이라이트 
                self.plot[idx].addItem(PeriodHighLightWithMinItem
                                       (x, pData.구간VAL["누적거래대금"], 100, CHART_WIDTH, tempMaxY+(tempMaxY-tempMinY)*0.11, tempMaxY+(tempMaxY-tempMinY)*0.08, COLOR_BLACK, 0.09))
                self.plot[idx].addItem(PeriodHighLightWithMinItem
                                       (x, pData.구간VAL["누적거래대금"], 500, CHART_WIDTH, tempMaxY+(tempMaxY-tempMinY)*0.11, tempMaxY+(tempMaxY-tempMinY)*0.08, COLOR_BLACK, 0.2))
                self.plot[idx].addItem(PeriodHighLightWithMinItem
                                       (x, pData.구간VAL["누적거래대금"], 1000, CHART_WIDTH, tempMaxY+(tempMaxY-tempMinY)*0.11, tempMaxY+(tempMaxY-tempMinY)*0.08, COLOR_BLUE, 0.3))
                self.plot[idx].addItem(LegendItem(f"누적거래대금", COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY+(tempMaxY-tempMinY)*0.13, 7))
                self.plot[idx].addItem(LegendItem(f"100/500/1000", COLOR_BLACK, x[0], tempMaxY+(tempMaxY-tempMinY)*0.13, 7))

                # 거래량증가 하이라이트
                self.plot[idx].addItem(PeriodHighLightWithMinItem
                                       (x, pData.구간VAL["거래량증가"], 50, CHART_WIDTH, tempMaxY+(tempMaxY-tempMinY)*0.07, tempMaxY+(tempMaxY-tempMinY)*0.04, COLOR_BLACK, 0.09))
                self.plot[idx].addItem(PeriodHighLightWithMinItem
                                       (x, pData.구간VAL["거래량증가"], 100, CHART_WIDTH, tempMaxY+(tempMaxY-tempMinY)*0.07, tempMaxY+(tempMaxY-tempMinY)*0.04, COLOR_BLACK, 0.2))
                self.plot[idx].addItem(PeriodHighLightWithMinItem
                                       (x, pData.구간VAL["거래량증가"], 200, CHART_WIDTH, tempMaxY+(tempMaxY-tempMinY)*0.07, tempMaxY+(tempMaxY-tempMinY)*0.04, COLOR_RED, 0.3))
                self.plot[idx].addItem(LegendItem(f"거래량증가", COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY+(tempMaxY-tempMinY)*0.09, 7))
                self.plot[idx].addItem(LegendItem(f"50/100/200", COLOR_BLACK, x[0], tempMaxY+(tempMaxY-tempMinY)*0.09, 7))

                #self.plot[idx].setRange(xRange=[0, WHOLE_DAY_SEC], yRange=[tempMinY, tempMaxY])
                self.plot[idx].setRange(yRange=[tempMinY-(tempMaxY-tempMinY)*MINUTE_CHART_MARGIN, tempMaxY+(tempMaxY-tempMinY)*0.1])

                if self.checkBoxDict['파바박'].flag is True:
                    self.plot[idx].addItem(pg.ScatterPlotItem(x=fastDataPlusTime, y=fastData.result["PlusPrice"], size=4, symbol='o', pen=None,
                                            brush=pg.mkBrush(color=COLOR_RED, width=2)))
                    self.plot[idx].addItem(pg.ScatterPlotItem(x=fastDataMinusTime, y=fastData.result["MinusPrice"], size=4, symbol='t', pen=None,
                                            brush=pg.mkBrush(color=COLOR_BLUE, width=2)))
                
                #if self.checkBoxDict['일초대금'].flag is True:
                #    self.plot[idx].addItem(pg.ScatterPlotItem(x=oneSecDataPlusTime, y=oneSecData.result["PlusPrice"], size=4, symbol='o', pen=None,
                #                            brush=pg.mkBrush(color=COLOR_RED, width=2)))
                #    self.plot[idx].addItem(pg.ScatterPlotItem(x=oneSecDataMinusTime, y=oneSecData.result["MinusPrice"], size=4, symbol='t', pen=None,
                #                            brush=pg.mkBrush(color=COLOR_BLUE, width=2)))

                #if self.checkBoxDict['큰돈'].flag is True:
                #    self.plot[idx].addItem(pg.ScatterPlotItem(x=bigMoneyPlusTime, y=realData.큰돈데이터["PlusPrice"], size=4, symbol='o', pen=None,
                #                            brush=pg.mkBrush(color=COLOR_RED, width=2)))
                #    self.plot[idx].addItem(pg.ScatterPlotItem(x=bigMoneyMinusTime, y=realData.큰돈데이터["MinusPrice"], size=4, symbol='t', pen=None,
                #                            brush=pg.mkBrush(color=COLOR_BLUE, width=2)))
#
                #if self.checkBoxDict['형님돈'].flag is True:
                #    self.plot[idx].addItem(pg.ScatterPlotItem(x=broMoneyPlusTime, y=realData.형님데이터["PlusPrice"], size=4, symbol='o', pen=None,
                #                            brush=pg.mkBrush(color=COLOR_RED, width=2)))
                #    self.plot[idx].addItem(pg.ScatterPlotItem(x=broMoneyMinusTime, y=realData.형님데이터["MinusPrice"], size=4, symbol='t', pen=None,
                #                            brush=pg.mkBrush(color=COLOR_BLUE, width=2)))                                            
                    
                #if self.checkBoxDict['단주'].flag is True:
                #    self.plot[idx].addItem(pg.ScatterPlotItem(x=danjuPlusTime, y=danjuPlusPrice, size=4, symbol='o', pen=None,
                #                            brush=pg.mkBrush(color=COLOR_RED, width=2)))
                #    self.plot[idx].addItem(pg.ScatterPlotItem(x=danjuMinusTime, y=danjuMinusPrice, size=4, symbol='o', pen=None,
                #                            brush=pg.mkBrush(color=COLOR_BLUE, width=2)))                    

                self.plot[idx].addItem(PeriodChartItemOCHL(x, pData.구간OCHL["현재가"], CHART_WIDTH, COLOR_RED, COLOR_BLUE, COLOR_TRANS, COLOR_TRANS))
                ##########################################################################
                ##########################################################################
                ##########################################################################


                # 거래대금 / 순대금
                if self.checkBoxDictSub['누적거래대금'].flag is True and (idx < NUM_GRAPH - 1):
                    idx += 1
                    tempMinY, tempMaxY = getAlignedMinMax(pData.구간VAL["누적거래대금"], 0, 1, 100)
                    #self.plot[idx].addItem(PeriodBarItem(x, pData.구간DELTA["순대금"][1], CHART_WIDTH, COLOR_RED, COLOR_RED_ALPHA100, COLOR_BLUE, COLOR_BLUE_ALPHA100))
                    self.plot[idx].addItem(PeriodCurveItem(x, pData.구간VAL["누적거래대금"], COLOR_BLACK, Qt.SolidLine))
                    self.plot[idx].addItem(LegendItem('거래대금', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY,FONT_SIZE_MINUTE_GRAPH))
                    self.plot[idx].setRange(yRange=[tempMinY, tempMaxY])
                    self.plot[idx].getAxis('left').setTicks([getTicksQuad(tempMinY, tempMaxY), []])
                    #self.plot[idx].addItem(LegendItem('\n순대금', COLOR_RED, MARKET_CLOSE_SEC, tempMaxY,FONT_SIZE_MINUTE_GRAPH))
                    #self.plot[idx].addItem(LegendItem('\n\n큰돈', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY,FONT_SIZE_MINUTE_GRAPH))

                # 구간 거래대금 / 순대금
                if self.checkBoxDictSub['구간거래대금'].flag is True and (idx < NUM_GRAPH - 1):
                    idx += 1
                    #tempMinY, tempMaxY = getAlignedMinMax(pData.구간DELTA["순대금"][1] + pData.구간DELTA["누적거래대금"][1], -100, 100, 100)
                    tempMinY, tempMaxY = getAlignedMinMax(pData.구간DELTA["누적거래대금"][1]+pData.구간DELTA["순대금"][1], 0, 100, 50)
                    self.plot[idx].addItem(PeriodHighLightItem(x, pData.구간강조["누적거래대금"][30], CHART_WIDTH, tempMaxY, tempMinY, COLOR_BLACK, 0.1))
                    self.plot[idx].addItem(PeriodHighLightItem(x, pData.구간강조["순대금"][10], CHART_WIDTH, tempMaxY, tempMinY, COLOR_RED, 0.1))                                        
                    self.plot[idx].addItem(PeriodBarItem(x, pData.구간DELTA["순대금"][1], CHART_WIDTH, COLOR_RED, COLOR_RED_ALPHA100, COLOR_BLUE, COLOR_BLUE_ALPHA100))                    
                    self.plot[idx].addItem(PeriodBarItem(x, pData.구간DELTA["누적거래대금"][1], CHART_WIDTH, COLOR_BLACK, COLOR_TRANS, COLOR_BLACK, COLOR_TRANS))                                    
                    self.plot[idx].addItem(LegendItem('거래대금', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                    #self.plot[idx].addItem(LegendItem('\n순대금', COLOR_RED, MARKET_CLOSE_SEC, tempMaxY,FONT_SIZE_MINUTE_GRAPH))
                    self.plot[idx].setRange(yRange=[tempMinY, tempMaxY])
                    self.plot[idx].getAxis('left').setTicks([getTicksQuad(tempMinY, tempMaxY), []])

                # 구간거래량증가
                if self.checkBoxDictSub['구간거래량증가'].flag is True and (idx < NUM_GRAPH - 1):
                    idx += 1
                    tempMinY, tempMaxY = getAlignedMinMax(pData.구간DELTA["거래량증가"][1]+pData.구간DELTA["순거래량증가"][1], 0, 50, 10)
                    self.plot[idx].addItem(PeriodHighLightItem(x, pData.구간강조["거래량증가"][50], CHART_WIDTH, tempMaxY, tempMinY, COLOR_BLACK, 0.1))
                    self.plot[idx].addItem(PeriodHighLightItem(x, pData.구간강조["순거래량증가"][10], CHART_WIDTH, tempMaxY, tempMinY, COLOR_RED, 0.1))
                    self.plot[idx].addItem(PeriodBarItem(x, pData.구간DELTA["거래량증가"][1], CHART_WIDTH, COLOR_BLACK, COLOR_TRANS, COLOR_BLACK, COLOR_TRANS))                
                    self.plot[idx].addItem(PeriodBarItem(x, pData.구간DELTA["순거래량증가"][1], CHART_WIDTH, COLOR_TRANS, COLOR_RED_ALPHA100, COLOR_TRANS, COLOR_BLUE_ALPHA100))
                    self.plot[idx].addItem(LegendItem('구간거래량증가', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                    self.plot[idx].addItem(LegendItem('\n구간순거래량증가', COLOR_RED, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                    self.plot[idx].setRange(yRange=[tempMinY, tempMaxY])
                    self.plot[idx].getAxis('left').setTicks([getTicksQuad(tempMinY, tempMaxY), []])

                # 보정대금
                #if self.checkBoxDictSub['보정대금'].flag is True and (idx < NUM_GRAPH - 1):
                #    idx += 1
                #    tempMinY, tempMaxY = getAlignedMinMax(pData.구간DELTA["보정대금"][1], 0, 100, 100)
                #    self.plot[idx].addItem(PeriodBarItem(x, pData.구간DELTA["보정대금"][1], CHART_WIDTH, COLOR_BLACK, COLOR_TRANS, COLOR_BLACK, COLOR_TRANS))                
                #    self.plot[idx].addItem(LegendItem('보정대금', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                #    self.plot[idx].setRange(yRange=[tempMinY, tempMaxY])
                #    self.plot[idx].getAxis('left').setTicks([getTicksQuad(tempMinY, tempMaxY), []])

                if self.checkBoxDictSub['순대금'].flag is True and (idx < NUM_GRAPH - 1):
                    idx += 1
                    tempMinY, tempMaxY = getAlignedMinMax( getOCHLHighLowList(pData.구간OCHL["순대금"]), -1, 1, 50 )
                    self.plot[idx].addItem(PeriodHighLightItem(x, pData.구간강조["순대금"][10], CHART_WIDTH, tempMaxY, tempMinY, COLOR_RED, 0.1))
                    self.plot[idx].addItem(PeriodChartItemOCHL(x, pData.구간OCHL["순대금"], CHART_WIDTH, COLOR_RED, COLOR_BLUE, COLOR_TRANS, COLOR_TRANS))
                    self.plot[idx].addItem(PeriodCurveItem(x, pData.구간복합이평["순대금"][10], COLOR_BLACK, Qt.SolidLine))
                    self.plot[idx].addItem(LegendItem('순대금', COLOR_RED, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                    self.plot[idx].setRange(yRange=[tempMinY, tempMaxY])
                    self.plot[idx].getAxis('left').setTicks([getTicksQuad(tempMinY, tempMaxY), []])

#                if self.checkBoxDictSub['순대금이평DT'].flag is True and (idx < NUM_GRAPH - 1):
#                    idx += 1
#                    tempMinY, tempMaxY = getAlignedMinMax( pData.구간복합이평DELTA["순대금"][10], -5, 5, 10 )
#                    self.plot[idx].addItem(PeriodBarItem(x, pData.구간복합이평DELTA["순대금"][10], CHART_WIDTH, COLOR_RED, COLOR_RED_ALPHA100, COLOR_BLUE, COLOR_BLUE_ALPHA100))
#                    self.plot[idx].addItem(LegendItem('순대금이평순증', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
#                    self.plot[idx].setRange(yRange=[tempMinY, tempMaxY])
#                    self.plot[idx].getAxis('left').setTicks([getTicksQuad(tempMinY, tempMaxY), []])

                #if self.checkBoxDictSub['구간순대금'].flag is True and (idx < NUM_GRAPH - 1):
                #    idx += 1
                #    tempMinY, tempMaxY = getAlignedMinMax( pData.구간DELTA["순대금"][1], -10, 10, 50 )
                #    self.plot[idx].addItem(PeriodBarItem(x, pData.구간DELTA["순대금"][1], CHART_WIDTH, COLOR_RED, COLOR_RED_ALPHA100, COLOR_BLUE, COLOR_BLUE_ALPHA100))
                #    self.plot[idx].addItem(PeriodHighLightItem(x, pData.구간강조["순대금"][10], CHART_WIDTH, tempMaxY, tempMinY, COLOR_BLACK, 0.1))
                #    self.plot[idx].addItem(LegendItem('구간순대금', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                #    self.plot[idx].setRange(yRange=[tempMinY, tempMaxY])
                #    self.plot[idx].getAxis('left').setTicks([getTicksQuad(tempMinY, tempMaxY), []])
#
                if self.checkBoxDictSub['매수매도대금'].flag is True and (idx < NUM_GRAPH - 1):
                    idx += 1
                    tempMinY, tempMaxY = getAlignedMinMax( pData.구간DELTA["매수대금"][1] + pData.구간DELTA["매도대금"][1], 0, 1, 50 )
                    self.plot[idx].addItem(PeriodBarItem(x, pData.구간DELTA["매수대금"][1], CHART_WIDTH, COLOR_RED, COLOR_TRANS, COLOR_BLUE, COLOR_TRANS))
                    self.plot[idx].addItem(PeriodBarItem(x, pData.구간DELTA["매도대금"][1], CHART_WIDTH, COLOR_TRANS, COLOR_BLUE_ALPHA100, COLOR_BLUE_ALPHA100, COLOR_TRANS))
                    self.plot[idx].addItem(LegendItem('매수대금', COLOR_RED, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                    self.plot[idx].addItem(LegendItem('\n매도대금', COLOR_BLUE, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                    self.plot[idx].setRange(yRange=[tempMinY, tempMaxY])
                    self.plot[idx].getAxis('left').setTicks([getTicksQuad(tempMinY, tempMaxY), []])

                if self.checkBoxDictSub['파바박대금'].flag is True and (idx < NUM_GRAPH - 1):
                    idx += 1
                    tempMinY, tempMaxY = getAlignedMinMax(pData.구간VAL["파바박대금"], -1, 1, 50)
                    self.plot[idx].addItem(PeriodHighLightItem(x, pData.구간강조["파바박대금"][10], CHART_WIDTH, tempMaxY, tempMinY, COLOR_BLACK, 0.1))
                    self.plot[idx].addItem(PeriodChartItemOCHL(x, pData.구간OCHL["파바박대금"], CHART_WIDTH, COLOR_RED, COLOR_BLUE, COLOR_TRANS, COLOR_TRANS))
                    self.plot[idx].addItem(PeriodCurveItem(x, pData.구간복합이평["파바박대금"][10], COLOR_BLACK, Qt.SolidLine))
                    self.plot[idx].addItem(LegendItem('파바박대금', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))                    
                    self.plot[idx].setRange(yRange=[tempMinY, tempMaxY])
                    self.plot[idx].getAxis('left').setTicks([getTicksQuad(tempMinY, tempMaxY), []])

                if self.checkBoxDictSub['구간파바박개수'].flag is True and (idx < NUM_GRAPH - 1):
                    idx += 1
                    tempMinY, tempMaxY = getAlignedMinMax(pData.구간DELTA["파바박개수"][1], 0, 100, 100)
                    self.plot[idx].addItem(PeriodHighLightItem(x, pData.구간강조["파바박개수"][50], CHART_WIDTH, tempMaxY, tempMinY, COLOR_BLACK, 0.1))
                    self.plot[idx].addItem(PeriodBarItem(x, pData.구간DELTA["파바박개수"][1], CHART_WIDTH, COLOR_RED, COLOR_RED_ALPHA100, COLOR_BLUE, COLOR_BLUE_ALPHA100))
                    self.plot[idx].addItem(LegendItem('구간파바박개수', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                    #if tempMinY==0 and tempMaxY==0: self.plot[idx].setRange(yRange=[-1, 1])   
                    #else:                           self.plot[idx].enableAutoRange(axis='y')
                    self.plot[idx].setRange(yRange=[tempMinY, tempMaxY])
                    self.plot[idx].getAxis('left').setTicks([getTicksQuad(tempMinY, tempMaxY), []])

                if self.checkBoxDictSub['매수매도파바박개수'].flag is True and (idx < NUM_GRAPH - 1):
                    idx += 1
                    tempMinY, tempMaxY = getAlignedMinMax(pData.구간DELTA["매수파바박개수"][1] + pData.구간DELTA["매도파바박개수"][1], 0, 10, 50)
                    self.plot[idx].addItem(PeriodBarItem(x, pData.구간DELTA["매수파바박개수"][1], CHART_WIDTH, COLOR_RED, COLOR_TRANS, COLOR_BLUE, COLOR_TRANS))
                    self.plot[idx].addItem(PeriodBarItem(x, pData.구간DELTA["매도파바박개수"][1], CHART_WIDTH, COLOR_TRANS, COLOR_BLUE_ALPHA100, COLOR_BLUE_ALPHA100, COLOR_TRANS))
                    self.plot[idx].addItem(LegendItem('매수파바박개수', COLOR_RED, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                    self.plot[idx].addItem(LegendItem('\n매도파바박개수', COLOR_BLUE, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                    self.plot[idx].setRange(yRange=[tempMinY, tempMaxY])
                    self.plot[idx].getAxis('left').setTicks([getTicksQuad(tempMinY, tempMaxY), []])

                if self.checkBoxDictSub['순매수율'].flag is True and (idx < NUM_GRAPH - 1):
                    idx += 1
                    tempMinY, tempMaxY = -100, 100
                    self.plot[idx].addItem(PeriodBarItem(x, pData.구간DELTA["순매수율"][1], CHART_WIDTH, COLOR_RED, COLOR_RED_ALPHA100, COLOR_BLUE, COLOR_BLUE_ALPHA100))
                    self.plot[idx].addItem(LegendItem('순매수율', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                    self.plot[idx].setRange(yRange=[tempMinY, tempMaxY])
                    self.plot[idx].getAxis('left').setTicks([getTicksQuad(tempMinY, tempMaxY), []])
                
                if self.checkBoxDictSub['순매수율누적'].flag is True and (idx < NUM_GRAPH - 1):
                    idx += 1
                    tempMinY, tempMaxY = -1000, 1000
                    self.plot[idx].addItem(PeriodBarItem(x, pData.구간DELTA_ACC["순매수율"][10], CHART_WIDTH, COLOR_RED, COLOR_RED_ALPHA100, COLOR_BLUE, COLOR_BLUE_ALPHA100))
                    self.plot[idx].addItem(LegendItem('순매수율누적(10)', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                    self.plot[idx].setRange(yRange=[tempMinY, tempMaxY])
                    self.plot[idx].getAxis('left').setTicks([getTicksQuad(tempMinY, tempMaxY), []])

                #if self.checkBoxDictSub['일초대금'].flag is True and (idx < NUM_GRAPH - 1):
                #    idx += 1
                #    tempMinY = min([0] + pData.구간VAL["일초대금"])
                #    tempMaxY = max([0] + pData.구간VAL["일초대금"])
                #    self.plot[idx].addItem(PeriodHighLightItem(x, pData.구간강조["일초대금"][10], CHART_WIDTH, tempMaxY, tempMinY, COLOR_BLACK, 0.1))
                #    self.plot[idx].addItem(PeriodChartItemOCHL(x, pData.구간OCHL["일초대금"], CHART_WIDTH, COLOR_RED, COLOR_BLUE, COLOR_TRANS, COLOR_TRANS))
                #    self.plot[idx].addItem(PeriodCurveItem(x, pData.구간복합이평["일초대금"][10], COLOR_BLACK, Qt.SolidLine))
                #    self.plot[idx].addItem(LegendItem('일초대금', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))                    
                #    if tempMinY==0 and tempMaxY==0: self.plot[idx].setRange(yRange=[-1, 1])   
                #    else:                           self.plot[idx].enableAutoRange(axis='y')

                if self.checkBoxDictSub['구간회전율'].flag is True and (idx < NUM_GRAPH - 1):
                    idx += 1
                    tempMinY, tempMaxY = getAlignedMinMax(pData.구간DELTA["회전율"][1] + pData.구간DELTA["순회전율"][1], -1, 1, 1)
                    self.plot[idx].addItem(PeriodHighLightItem(x, pData.구간강조["회전율"][1], CHART_WIDTH, tempMaxY, tempMinY, COLOR_BLACK, 0.1))
                    self.plot[idx].addItem(PeriodBarItem(x, pData.구간DELTA["순회전율"][1], CHART_WIDTH, COLOR_RED, COLOR_RED_ALPHA100, COLOR_BLUE, COLOR_BLUE_ALPHA100))
                    self.plot[idx].addItem(PeriodBarItem(x, pData.구간DELTA["회전율"][1], CHART_WIDTH, COLOR_BLACK, COLOR_TRANS, COLOR_BLACK, COLOR_TRANS))                
                    self.plot[idx].addItem(LegendItem('회전율', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                    self.plot[idx].setRange(yRange=[tempMinY, tempMaxY])
                    self.plot[idx].getAxis('left').setTicks([getTicksQuad(tempMinY, tempMaxY), []])

                if self.checkBoxDictSub['순회전율'].flag is True and (idx < NUM_GRAPH - 1):
                    idx += 1
                    tempMinY, tempMaxY = getAlignedMinMax(getOCHLHighLowList(pData.구간OCHL["순회전율"]), -1, 1, 1)
                    self.plot[idx].addItem(PeriodHighLightItem(x, pData.구간강조["순회전율"][1], CHART_WIDTH, tempMaxY, tempMinY, COLOR_BLACK, 0.1))
                    self.plot[idx].addItem(PeriodChartItemOCHL(x, pData.구간OCHL["순회전율"], CHART_WIDTH, COLOR_RED, COLOR_BLUE, COLOR_RED_ALPHA100, COLOR_TRANS))
                    #self.plot[idx].addItem(PeriodCurveItem(x, pData.구간VAL["순회전율"], COLOR_BLACK, Qt.SolidLine))
                    self.plot[idx].addItem(PeriodCurveItem(x, pData.구간이평["순회전율"][10], COLOR_BLUE, Qt.SolidLine))
                    self.plot[idx].addItem(LegendItem('순회전율', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                    self.plot[idx].setRange(yRange=[tempMinY, tempMaxY])
                    self.plot[idx].getAxis('left').setTicks([getTicksQuad(tempMinY, tempMaxY), []])

                if self.checkBoxDictSub['구간평균가등락율'].flag is True and (idx < NUM_GRAPH - 1):
                    idx += 1
                    tempMinY, tempMaxY = getAlignedMinMax(pData.구간DELTA["평균가등락율2"][1], -5, 5, 1)
                    self.plot[idx].addItem(PeriodBarItem(x, pData.구간DELTA["평균가등락율2"][1], CHART_WIDTH, COLOR_BLACK, COLOR_TRANS, COLOR_BLACK, COLOR_TRANS))                
                    self.plot[idx].addItem(PeriodHighLightItem(x, pData.구간강조["평균가등락율2"][0.5], CHART_WIDTH, tempMaxY, tempMinY, COLOR_RED, 0.1))                                        
                    self.plot[idx].addItem(LegendItem('구간평균가등락율(2)', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                    self.plot[idx].setRange(yRange=[tempMinY, tempMaxY])
                    self.plot[idx].getAxis('left').setTicks([getTicksQuad(tempMinY, tempMaxY), []])

                # 파바박 돈
                #idx += 1
                #tempMinY = min(fastData.result["MinusMoney"] + [-10])
                #tempMaxY = max(fastData.result["PlusMoney"] + [10])
                #self.plot[idx].addItem(pg.ScatterPlotItem(x=fastDataPlusTime, y=fastData.result["PlusMoney"], size=4, symbol='o', pen=None,
                #                                        brush=pg.mkBrush(color=COLOR_RED, width=2)))
                #self.plot[idx].addItem(pg.ScatterPlotItem(x=fastDataMinusTime, y=fastData.result["MinusMoney"], size=4, symbol='o', pen=None,
                #                                        brush=pg.mkBrush(color=COLOR_BLUE, width=2)))                                                    
                #self.plot[idx].addItem(LegendItem('파바박대금(억)', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))

                #if self.checkBoxDictSub['구간순큰돈횟수'].flag is True and (idx < NUM_GRAPH - 1):
                #    idx += 1
                #    tempMinY = min([0] + pData.구간DELTA["순큰돈횟수"][1])
                #    tempMaxY = max([0] + pData.구간DELTA["순큰돈횟수"][1])
                #    self.plot[idx].addItem(PeriodBarItem(x, pData.구간DELTA["순큰돈횟수"][1], CHART_WIDTH, COLOR_RED, COLOR_RED_ALPHA100, COLOR_BLUE, COLOR_BLUE_ALPHA100))
                #    self.plot[idx].addItem(LegendItem('순큰돈횟수', COLOR_RED, MARKET_CLOSE_SEC, tempMaxY,FONT_SIZE_MINUTE_GRAPH))
                #    if tempMinY==0 and tempMaxY==0: self.plot[idx].setRange(yRange=[-1, 1])   
                #    else:                           self.plot[idx].enableAutoRange(axis='y')

                #if self.checkBoxDictSub['순큰돈횟수'].flag is True and (idx < NUM_GRAPH - 1):
                #    idx += 1
                #    tempMinY = min([0] + getOCHLLowList(pData.구간OCHL["순큰돈횟수"]))
                #    tempMaxY = max([0] + getOCHLHighList(pData.구간OCHL["순큰돈횟수"]))
                #    self.plot[idx].addItem(PeriodChartItemOCHL(x, pData.구간OCHL["순큰돈횟수"], CHART_WIDTH, COLOR_RED, COLOR_BLUE, COLOR_RED_ALPHA100, COLOR_TRANS))
                #    #self.plot[idx].addItem(PeriodCurveItem(x, pData.구간VAL["순큰돈횟수"], COLOR_BLACK, Qt.SolidLine))
                #    self.plot[idx].addItem(PeriodCurveItem(x, pData.구간이평["순큰돈횟수"][10], COLOR_BLUE, Qt.SolidLine))
                #    self.plot[idx].addItem(LegendItem('순큰돈횟수', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                #    if tempMinY==0 and tempMaxY==0: self.plot[idx].setRange(yRange=[-1, 1])   
                #    else:                           self.plot[idx].enableAutoRange(axis='y')

                if self.checkBoxDictSub['순장악력'].flag is True and (idx < NUM_GRAPH - 1):
                    idx += 1
                    tempMinY, tempMaxY = -100, 100
                    self.plot[idx].addItem(PeriodChartItemOCHL(x, pData.구간OCHL["순장악력"], CHART_WIDTH, COLOR_RED, COLOR_BLUE, COLOR_RED_ALPHA100, COLOR_TRANS))
                    #self.plot[idx].addItem(PeriodCurveItem(x, pData.구간VAL["순장악력"], COLOR_BLACK, Qt.SolidLine))
                    self.plot[idx].addItem(PeriodCurveItem(x, pData.구간이평["순장악력"][10], COLOR_BLUE, Qt.SolidLine))
                    self.plot[idx].addItem(LegendItem('순장악력', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                    self.plot[idx].setRange(yRange=[tempMinY, tempMaxY])
                    self.plot[idx].getAxis('left').setTicks([getTicksQuad(tempMinY, tempMaxY), []])

                if self.checkBoxDictSub['매수매도파워'].flag is True and (idx < NUM_GRAPH - 1):
                    idx += 1
                    tempMinY, tempMaxY = getAlignedMinMax(pData.구간DELTA["매수파워"][1] + pData.구간DELTA["매도파워"][1], 0, 1, 5)
                    self.plot[idx].addItem(PeriodBarItem(x, pData.구간DELTA["매수파워"][1], CHART_WIDTH, COLOR_RED, COLOR_TRANS, COLOR_BLUE, COLOR_TRANS))
                    self.plot[idx].addItem(PeriodBarItem(x, pData.구간DELTA["매도파워"][1], CHART_WIDTH, COLOR_TRANS, COLOR_BLUE_ALPHA100, COLOR_BLUE_ALPHA100, COLOR_TRANS))
                    #self.plot[idx].addItem(PeriodCurveItem(x, pData.구간DELTA["매수파워"][1], COLOR_RED, Qt.SolidLine))
                    #self.plot[idx].addItem(PeriodCurveItem(x, pData.구간DELTA["매도파워"][1], COLOR_BLUE, Qt.SolidLine))
                    #self.plot[idx].addItem(PeriodChartItemOCHL(x, pData.구간OCHL["매수파워"], CHART_WIDTH, COLOR_RED, COLOR_RED, COLOR_TRANS, COLOR_TRANS))
                    #self.plot[idx].addItem(PeriodChartItemOCHL(x, pData.구간OCHL["매도파워"], CHART_WIDTH, COLOR_BLUE, COLOR_BLUE, COLOR_TRANS, COLOR_TRANS))
                    #self.plot[idx].addItem(PeriodCurveItem(x, pData.구간VAL["매수파워"], COLOR_BLACK, Qt.SolidLine))
                    #self.plot[idx].addItem(PeriodCurveItem(x, pData.구간이평["매수파워"][10], COLOR_BLUE, Qt.SolidLine))
                    self.plot[idx].addItem(LegendItem('매수파워', COLOR_RED, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                    self.plot[idx].addItem(LegendItem('\n매도파워', COLOR_BLUE, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                    self.plot[idx].setRange(yRange=[tempMinY, tempMaxY])
                    self.plot[idx].getAxis('left').setTicks([getTicksQuad(tempMinY, tempMaxY), []])

                #if self.checkBoxDictSub['매도파워'].flag is True and (idx < NUM_GRAPH - 1):
                #    idx += 1
                #    tempMinY = min([0] + pData.구간DELTA["매도파워"][1])
                #    tempMaxY = max([0] + pData.구간DELTA["매도파워"][1])
                #    self.plot[idx].addItem(PeriodBarItem(x, pData.구간DELTA["매도파워"][1], CHART_WIDTH, COLOR_RED, COLOR_RED_ALPHA100, COLOR_BLUE, COLOR_BLUE_ALPHA100))
                #    self.plot[idx].addItem(LegendItem('매도파워', COLOR_BLUE, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                #    if tempMinY==0 and tempMaxY==0: self.plot[idx].setRange(yRange=[-1, 1])   
                #    else:                           self.plot[idx].enableAutoRange(axis='y')

                if self.checkBoxDictSub['순매수파워'].flag is True and (idx < NUM_GRAPH - 1):
                    idx += 1
                    tempMinY, tempMaxY = getAlignedMinMax(getOCHLHighLowList(pData.구간OCHL["순매수파워"]), -1, 1, 5)
                    self.plot[idx].addItem(PeriodHighLightItem(x, pData.구간강조["순매수파워"][1], CHART_WIDTH, tempMaxY, tempMinY, COLOR_BLACK, 0.1))
                    self.plot[idx].addItem(PeriodChartItemOCHL(x, pData.구간OCHL["순매수파워"], CHART_WIDTH, COLOR_RED, COLOR_BLUE, COLOR_RED_ALPHA100, COLOR_TRANS))
                    #self.plot[idx].addItem(PeriodCurveItem(x, pData.구간VAL["순매수파워"], COLOR_BLACK, Qt.SolidLine))
                    self.plot[idx].addItem(PeriodCurveItem(x, pData.구간이평["순매수파워"][10], COLOR_BLUE, Qt.SolidLine))
                    self.plot[idx].addItem(LegendItem('순매수파워', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                    self.plot[idx].setRange(yRange=[tempMinY, tempMaxY])
                    self.plot[idx].getAxis('left').setTicks([getTicksQuad(tempMinY, tempMaxY), []])

                if self.checkBoxDictSub['구간순매수파워'].flag is True and (idx < NUM_GRAPH - 1):
                    idx += 1
                    tempMinY, tempMaxY = getAlignedMinMax(pData.구간DELTA["순매수파워"][1], -5 ,5, 5)
                    self.plot[idx].addItem(PeriodBarItem(x, pData.구간DELTA["순매수파워"][1], CHART_WIDTH, COLOR_RED, COLOR_RED_ALPHA100, COLOR_BLUE, COLOR_BLUE_ALPHA100))
                    self.plot[idx].addItem(PeriodHighLightItem(x, pData.구간강조["순매수파워"][1], CHART_WIDTH, tempMaxY, tempMinY, COLOR_BLACK, 0.1))
                    self.plot[idx].addItem(LegendItem('구간순매수파워', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                    self.plot[idx].setRange(yRange=[tempMinY, tempMaxY])
                    self.plot[idx].getAxis('left').setTicks([getTicksQuad(tempMinY, tempMaxY), []])

                if self.checkBoxDictSub['순형님대금'].flag is True and (idx < NUM_GRAPH - 1):
                    idx += 1
                    tempMinY, tempMaxY = getAlignedMinMax(getOCHLHighLowList(pData.구간OCHL["순형님대금"]), -1, 1, 50)
                    self.plot[idx].addItem(PeriodHighLightItem(x, pData.구간강조["순형님대금"][5], CHART_WIDTH, tempMaxY, tempMinY, COLOR_BLACK, 0.1))
                    self.plot[idx].addItem(PeriodChartItemOCHL(x, pData.구간OCHL["순형님대금"], CHART_WIDTH, COLOR_RED, COLOR_BLUE, COLOR_RED_ALPHA100, COLOR_TRANS))
                    #self.plot[idx].addItem(PeriodCurveItem(x, pData.구간VAL["순형님대금"], COLOR_BLACK, Qt.SolidLine))
                    self.plot[idx].addItem(PeriodCurveItem(x, pData.구간이평["순형님대금"][10], COLOR_BLUE, Qt.SolidLine))
                    self.plot[idx].addItem(LegendItem('순형님대금', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                    self.plot[idx].setRange(yRange=[tempMinY, tempMaxY])
                    self.plot[idx].getAxis('left').setTicks([getTicksQuad(tempMinY, tempMaxY), []])

                #if self.checkBoxDictSub['거래원'].flag is True and (idx < NUM_GRAPH - 1):
                #    idx += 1
                #    tempMinY, tempMaxY = getAlignedMinMax(getOCHLHighLowList(pData.구간OCHL["키움증권"]), -1, 1, 1000)
                #    self.plot[idx].addItem(PeriodChartItemOCHL(x, pData.구간OCHL["키움증권"], CHART_WIDTH, COLOR_RED, COLOR_BLUE, COLOR_RED_ALPHA100, COLOR_TRANS))
                #    self.plot[idx].addItem(LegendItem('키움증권', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                #    self.plot[idx].setRange(yRange=[tempMinY, tempMaxY])
                #    self.plot[idx].getAxis('left').setTicks([getTicksQuad(tempMinY, tempMaxY), []])


                #if self.checkBoxDictSub['매도호가'].flag is True and (idx < NUM_GRAPH - 1):
                #    idx += 1
                #    tempMinY = min([0] + getOCHLLowList(pData.구간OCHL["매도호가합"]))
                #    tempMaxY = max([0] + getOCHLHighList(pData.구간OCHL["매도호가합"]))
                #    self.plot[idx].addItem(PeriodChartItemOCHL(x, pData.구간OCHL["매도호가합"], CHART_WIDTH, COLOR_RED, COLOR_BLUE, COLOR_RED_ALPHA100, COLOR_TRANS))
                #    self.plot[idx].addItem(LegendItem('매도호가합', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                #    if tempMinY==0 and tempMaxY==0: self.plot[idx].setRange(yRange=[-1, 1])
                #    else:                           self.plot[idx].enableAutoRange(axis='y')
#
                #if self.checkBoxDictSub['매수호가'].flag is True and (idx < NUM_GRAPH - 1):
                #    idx += 1
                #    tempMinY = min([0] + getOCHLLowList(pData.구간OCHL["매수호가합"]))
                #    tempMaxY = max([0] + getOCHLHighList(pData.구간OCHL["매수호가합"]))
                #    self.plot[idx].addItem(PeriodChartItemOCHL(x, pData.구간OCHL["매수호가합"], CHART_WIDTH, COLOR_RED, COLOR_BLUE, COLOR_RED_ALPHA100, COLOR_TRANS))
                #    self.plot[idx].addItem(LegendItem('매수호가합', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                #    if tempMinY==0 and tempMaxY==0: self.plot[idx].setRange(yRange=[-1, 1])
                #    else:                           self.plot[idx].enableAutoRange(axis='y')

                #if self.checkBoxDictSub['매도호가변동'].flag is True and (idx < NUM_GRAPH - 1):
                #    idx += 1
                #    tempMinY, tempMaxY = getAlignedMinMax(getOCHLHighLowList(pData.구간OCHL["매도호가변동"]), -1, 1, 1000)
                #    self.plot[idx].addItem(PeriodChartItemOCHL(x, pData.구간OCHL["매도호가변동"], CHART_WIDTH, COLOR_RED, COLOR_BLUE, COLOR_RED_ALPHA100, COLOR_TRANS))
                #    self.plot[idx].addItem(LegendItem('매도호가변동', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                #    self.plot[idx].setRange(yRange=[tempMinY, tempMaxY])
                #    self.plot[idx].getAxis('left').setTicks([getTicksQuad(tempMinY, tempMaxY), []])
#
                #if self.checkBoxDictSub['매수호가변동'].flag is True and (idx < NUM_GRAPH - 1):
                #    idx += 1
                #    tempMinY, tempMaxY = getAlignedMinMax(getOCHLHighLowList(pData.구간OCHL["매수호가변동"]), -1, 1, 1000)
                #    self.plot[idx].addItem(PeriodChartItemOCHL(x, pData.구간OCHL["매수호가변동"], CHART_WIDTH, COLOR_RED, COLOR_BLUE, COLOR_RED_ALPHA100, COLOR_TRANS))
                #    self.plot[idx].addItem(LegendItem('매수호가변동', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                #    self.plot[idx].setRange(yRange=[tempMinY, tempMaxY])
                #    self.plot[idx].getAxis('left').setTicks([getTicksQuad(tempMinY, tempMaxY), []])
                    
                #if self.checkBoxDictSub['매도호가비율'].flag is True and (idx < NUM_GRAPH - 1):
                #    idx += 1
                #    tempMinY, tempMaxY = getAlignedMinMax(getOCHLHighLowList(pData.구간OCHL["매도호가비율"]), -1, 1, 10)
                #    self.plot[idx].addItem(PeriodChartItemOCHL(x, pData.구간OCHL["매도호가비율"], CHART_WIDTH, COLOR_RED, COLOR_BLUE, COLOR_RED_ALPHA100, COLOR_TRANS))
                #    self.plot[idx].addItem(LegendItem('매도호가비율', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                #    self.plot[idx].setRange(yRange=[tempMinY, tempMaxY])
                #    self.plot[idx].getAxis('left').setTicks([getTicksQuad(tempMinY, tempMaxY), []])

                if self.checkBoxDictSub['호가대금'].flag is True and (idx < NUM_GRAPH - 1):
                    idx += 1
                    tempMinY, tempMaxY = getAlignedMinMax(getOCHLHighLowList(pData.구간OCHL["매도호가대금"])+getOCHLHighLowList(pData.구간OCHL['매수호가대금']), 0, 1, 10)
                    self.plot[idx].addItem(PeriodChartItemOCHL(x, pData.구간OCHL["매도호가대금"], CHART_WIDTH, COLOR_BLUE, COLOR_BLUE, COLOR_BLUE_ALPHA100, COLOR_TRANS))
                    self.plot[idx].addItem(PeriodChartItemOCHL(x, pData.구간OCHL["매수호가대금"], CHART_WIDTH, COLOR_RED, COLOR_RED, COLOR_RED_ALPHA100, COLOR_TRANS))
                    self.plot[idx].addItem(LegendItem('매도호가대금', COLOR_BLUE, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                    self.plot[idx].addItem(LegendItem('\n매수호가대금', COLOR_RED, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                    self.plot[idx].setRange(yRange=[tempMinY, tempMaxY])
                    self.plot[idx].getAxis('left').setTicks([getTicksQuad(tempMinY, tempMaxY), []])

                if self.checkBoxDictSub['가격변동율'].flag is True and (idx < NUM_GRAPH - 1):
                    idx += 1
                    tempMinY, tempMaxY = getAlignedMinMax(pData.구간변동율["현재가"], 0, 1, 5)
                    self.plot[idx].addItem(PeriodBarItem(x, pData.구간변동율['현재가'], CHART_WIDTH, COLOR_RED, COLOR_RED_ALPHA100, COLOR_BLUE, COLOR_BLUE_ALPHA100))
                    self.plot[idx].addItem(LegendItem('가격변동률', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                    #if tempMinY==0 and tempMaxY==0: self.plot[idx].setRange(yRange=[-1, 1])   
                    #else:                           self.plot[idx].enableAutoRange(axis='y')
                    self.plot[idx].setRange(yRange=[tempMinY, tempMaxY])
                    #self.plot[idx].getAxis('left').setTicks([[(val, str(val)) for val in range(tempMinY, tempMaxY+1, round((tempMaxY-tempMinY)/4))], []])
                    self.plot[idx].getAxis('left').setTicks([getTicksQuad(tempMinY, tempMaxY), []])    
                
                if self.checkBoxDictSub['순대금변동'].flag is True and (idx < NUM_GRAPH - 1):
                    idx += 1
                    tempMinY, tempMaxY = getAlignedMinMax(pData.구간변동["순대금"], 0, 10, 20)
                    self.plot[idx].addItem(PeriodBarItem(x, pData.구간변동['순대금'], CHART_WIDTH, COLOR_RED, COLOR_RED_ALPHA100, COLOR_BLUE, COLOR_BLUE_ALPHA100))
                    self.plot[idx].addItem(LegendItem('순대금변동', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                    #if tempMinY==0 and tempMaxY==0: self.plot[idx].setRange(yRange=[-1, 1])   
                    #else:                           self.plot[idx].enableAutoRange(axis='y')
                    self.plot[idx].setRange(yRange=[tempMinY, tempMaxY])
                    #self.plot[idx].getAxis('left').setTicks([[(val, str(val)) for val in range(tempMinY, tempMaxY+1, round((tempMaxY-tempMinY)/4))], []])
                    self.plot[idx].getAxis('left').setTicks([getTicksQuad(tempMinY, tempMaxY), []])    

                if (self.checkBoxDictSub['순거래량박스권'].flag or self.checkBoxDictSub['가격박스권'].flag) and (idx < NUM_GRAPH - 1):
                    idx += 1
                    tempMinY, tempMaxY = getAlignedMinMax(getOCHLHighLowList(pData.구간OCHL["가격박스권"])+getOCHLHighLowList(pData.구간OCHL['순거래량박스권']), 0, 1, 100)
                    if self.checkBoxDictSub['순거래량박스권'].flag:
                        self.plot[idx].addItem(PeriodChartItemOCHL(x, pData.구간OCHL["순거래량박스권"], CHART_WIDTH, COLOR_RED, COLOR_RED, COLOR_RED_ALPHA100, COLOR_TRANS))
                        self.plot[idx].addItem(LegendItem('순거래량박스권', COLOR_RED, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                    if self.checkBoxDictSub['가격박스권'].flag:
                        self.plot[idx].addItem(PeriodChartItemOCHL(x, pData.구간OCHL["가격박스권"], CHART_WIDTH, COLOR_BLUE, COLOR_BLUE, COLOR_BLUE_ALPHA100, COLOR_TRANS))
                        self.plot[idx].addItem(LegendItem('\n가격박스권', COLOR_BLUE, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                    self.plot[idx].setRange(yRange=[tempMinY, tempMaxY])
                    self.plot[idx].getAxis('left').setTicks([getTicksQuad(tempMinY, tempMaxY), []])

                #if self.checkBoxDictSub['단주개수'].flag is True and (idx < NUM_GRAPH - 1):
                #    idx += 1
                #    tempMinY = min([0] + getOCHLLowList(pData.구간OCHL["단주개수"]))
                #    tempMaxY = max([0] + getOCHLHighList(pData.구간OCHL["단주개수"]))
                #    self.plot[idx].addItem(PeriodChartItemOCHL(x, pData.구간OCHL["단주개수"], CHART_WIDTH, COLOR_RED, COLOR_BLUE, COLOR_RED_ALPHA100, COLOR_TRANS))
                #    self.plot[idx].addItem(LegendItem('단주개수', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                #    if tempMinY==0 and tempMaxY==0: self.plot[idx].setRange(yRange=[-1, 1])
                #    else:                           self.plot[idx].enableAutoRange(axis='y')
#
                #if self.checkBoxDictSub['단주총합'].flag is True and (idx < NUM_GRAPH - 1):
                #    idx += 1
                #    tempMinY = min([0] + getOCHLLowList(pData.구간OCHL["단주총합"]))
                #    tempMaxY = max([0] + getOCHLHighList(pData.구간OCHL["단주총합"]))
                #    self.plot[idx].addItem(PeriodChartItemOCHL(x, pData.구간OCHL["단주총합"], CHART_WIDTH, COLOR_RED, COLOR_BLUE, COLOR_RED_ALPHA100, COLOR_TRANS))
                #    self.plot[idx].addItem(LegendItem('단주총합', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                #    if tempMinY==0 and tempMaxY==0: self.plot[idx].setRange(yRange=[-1, 1])
                #    else:                           self.plot[idx].enableAutoRange(axis='y')


                #idx += 1
                #tempMinY = min(pData.구간이평["체강"][1] + pData.구간이평["체강"][5] + pData.구간이평["체강"][10] + [100])
                #tempMaxY = max(pData.구간이평["체강"][1] + pData.구간이평["체강"][5] + pData.구간이평["체강"][10] + [100])
                #self.plot[idx].addItem(PeriodCurveItem(x, pData.구간이평["체강"][10], COLOR_BLACK, Qt.SolidLine))
                #self.plot[idx].addItem(PeriodCurveItem(x, pData.구간이평["체강"][5], COLOR_BLUE, Qt.SolidLine))
                #self.plot[idx].addItem(PeriodCurveItem(x, pData.구간이평["체강"][1], COLOR_RED, Qt.SolidLine))
                #self.plot[idx].addItem(
                #    LegendItem('체강이평1', COLOR_RED, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                #self.plot[idx].addItem(
                #    LegendItem('\n체강이평5', COLOR_BLUE, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))
                #self.plot[idx].addItem(
                #    LegendItem('\n\n체강이평10', COLOR_BLACK, MARKET_CLOSE_SEC, tempMaxY, FONT_SIZE_MINUTE_GRAPH))

                self.onAxisSliderMoved(self.scrollbar.value())

            self.drawDayGraph()
        #self.drawSectorGraph()

    def drawDayGraph(self):
        day날짜, day시가, day종가, day고가, day저가, day양봉, day세력대금 = [], [], [], [], [], [], []
        day이평 = {5:[], 10:[], 20:[], 60:[], 120:[]}
        day평균가이평 = {p:[] for p in 평균가_KEYS}
        day신고가 = {20:[], 120:[]}
        day상한가 = []
        day거래대금, day이평5저가, day이평20저가, day이평20중가, day이평20고가 = [], [], [], [], []
        day세력봉 = []
        회전율, 최대회전율 = [], []
        for i in range(NUM_DAYGRAPH):
            self.dayPlot[i].clear()

        # 일봉 데이터
        realData = self.datas[self.selectedCode]
        dayData = realData.dayDatas
        if len(dayData.날짜) > 0:
            startIndex = len(dayData.날짜) - min(NUM_PRINT_DAYGRAPH, len(dayData.날짜))
            for i in range(startIndex, len(dayData.날짜)+1):
                # day날짜.append(getTday(dayData.날짜[i]))
                day날짜.append(i - startIndex)

            # 복기모드때 중복 일봉 출력 방지
            if realData.복기모드 is True:
                day날짜.pop(-1)

            if realData.시가 == 0:    day시가 = dayData.시가[startIndex:] + [dayData.종가[-1]]
            else:                    day시가 = dayData.시가[startIndex:] + [realData.시가]
            if realData.현재가 == 0:  day종가 = dayData.종가[startIndex:] + [dayData.종가[-1]]
            else:                    day종가 = dayData.종가[startIndex:] + [realData.현재가]
            if realData.고가 == 0:    day고가 = dayData.고가[startIndex:] + [dayData.종가[-1]]
            else:                    day고가 = dayData.고가[startIndex:] + [realData.고가]
            if realData.저가 == 0:    day저가 = dayData.저가[startIndex:] + [dayData.종가[-1]]
            else:                    day저가 = dayData.저가[startIndex:] + [realData.저가]
            if realData.현재가>=realData.시가:
                day양봉 = dayData.양봉[startIndex:] + [True]
            else:
                day양봉 = dayData.양봉[startIndex:] + [False]

            for key in day이평.keys():
                if realData.시가 == 0:
                    day이평[key] = dayData.이평[key][startIndex:] + [dayData.이평[key][-1]]
                else:
                    day이평[key] = dayData.이평[key][startIndex:] + [(dayData.이평[key][-1] * (key-1) + realData.현재가) / key]

            for key in day평균가이평.keys():
                if realData.시가 == 0:
                    day평균가이평[key] = dayData.평균가이평[key][startIndex:] + [dayData.평균가이평[key][-1]]
                else:
                    day평균가이평[key] = dayData.평균가이평[key][startIndex:] + [safeDivideRounded(realData.누적거래대금*억, realData.누적거래량, realData.현재가, 0)]

            for key in day신고가.keys():
                day신고가[key] = dayData.신고가[key][startIndex:] + [dayData.신고가[key][-1]]
            day거래대금 = dayData.거래대금[startIndex:] + [int(realData.누적거래대금)]
            day이평5저가 = dayData.이평5저가[startIndex:] + [dayData.이평5저가[-1]]
            day이평20저가 = dayData.이평20저가[startIndex:] + [dayData.이평20저가[-1]]
            day이평20중가 = dayData.이평20중가[startIndex:] + [dayData.이평20중가[-1]]
            day이평20고가 = dayData.이평20고가[startIndex:] + [dayData.이평20고가[-1]]
            회전율 = dayData.회전율[startIndex:] + [realData.회전율]
            임시_최대회전율 = max(dayData.회전율 + [realData.회전율])
            for i in range(len(회전율)):
                최대회전율.append(임시_최대회전율)

            if realData.현재가>=realData.시가:
                day세력대금 = dayData.세력대금[startIndex:] + [dayData.세력대금[-1] + day거래대금[-1]]
            else:
                day세력대금 = dayData.세력대금[startIndex:] + [dayData.세력대금[-1] - day거래대금[-1]]

            if len(dayData.상한가) > 0:
                day상한가 = dayData.상한가[startIndex:] + [False]
            if len(dayData.세력봉) > 0:
                day세력봉 = dayData.세력봉[startIndex:] + [False]

            if realData.누적거래대금>0 and realData.누적거래량>0:
                day평균가 = dayData.평균가[startIndex:] + [round(realData.누적거래대금*억/realData.누적거래량,2)]
            else:
                day평균가 = dayData.평균가[startIndex:] + [dayData.평균가[-1]]
#self.plot[idx].addItem(PeriodCurveItem(x, pData.구간VAL['박스750'], COLOR_BLUE, Qt.DashDotLine))
            # 일봉데이터
            idx = 0
            tempY = min(day저가 + day이평[20])
            #self.dayPlot[idx].addItem(LegendItemWithSize(f"일봉", COLOR_BROWN, 0, tempY , 14))
            self.dayPlot[idx].addItem(PeriodChartItem(day날짜, day시가, day종가, day고가, day저가, DAYCHART_WIDTH, COLOR_RED, COLOR_BLUE, COLOR_RED, COLOR_BLUE))
            #self.dayPlot[idx].addItem(PeriodCurveOffsetItem(day날짜, day이평[5], DAYCHART_WIDTH/2, COLOR_RED, Qt.SolidLine))
            #self.dayPlot[idx].addItem(PeriodCurveOffsetItem(day날짜, day이평[10], DAYCHART_WIDTH/2, COLOR_BLUE, Qt.SolidLine))
            #self.dayPlot[idx].addItem(PeriodCurveOffsetItem(day날짜, day이평[20], DAYCHART_WIDTH/2, COLOR_BROWN, Qt.SolidLine))
            #self.dayPlot[idx].addItem(PeriodCurveOffsetItem(day날짜, day이평[60], DAYCHART_WIDTH/2, COLOR_DARK_GREEN, Qt.SolidLine))
            #self.dayPlot[idx].addItem(PeriodCurveOffsetItem(day날짜, day이평[120], DAYCHART_WIDTH/2, COLOR_PURPLE, Qt.SolidLine))
            #self.dayPlot[idx].addItem(PeriodCurveOffsetItem(day날짜, day평균가, DAYCHART_WIDTH/2, COLOR_BLACK, Qt.SolidLine))
            #self.dayPlot[idx].addItem(PeriodCurveItem(day날짜, day평균가, COLOR_BLACK, Qt.SolidLine))
            #self.dayPlot[idx].addItem(pg.ScatterPlotItem(x=day날짜, y=day평균가, size=4, symbol='o', pen=None,
            #                                brush=pg.mkBrush(color=COLOR_BLACK, width=2)))
            self.dayPlot[idx].addItem(PeriodCurveOffsetItem(day날짜, day평균가이평[5], DAYCHART_WIDTH/2, COLOR_RED, Qt.SolidLine))
            self.dayPlot[idx].addItem(PeriodCurveOffsetItem(day날짜, day평균가이평[10], DAYCHART_WIDTH/2, COLOR_BLUE, Qt.SolidLine))
            #self.dayPlot[idx].addItem(PeriodCurveOffsetItem(day날짜, day평균가이평[20], DAYCHART_WIDTH/2, COLOR_BROWN, Qt.SolidLine))
            if realData.복기모드 is True:
                if len(dayData.저항대) > 1:
                    if len(dayData.저항대[-2]) > 0:
                        self.dayPlot[idx].addItem(LineListItem(day날짜[0], day날짜[-1], dayData.저항대[-2], COLOR_RED, 1, Qt.SolidLine))
            else:
                if len(dayData.저항대[-1]) > 0:
                    self.dayPlot[idx].addItem(LineListItem(day날짜[0], day날짜[-1], dayData.저항대[-1], COLOR_RED, 1, Qt.SolidLine))
            #if len(dayData.상한가) > 0:
                #self.dayPlot[idx].addItem(PeriodHighLightItem(day날짜, day상한가, day고가, min(day저가)*0.9,
                #                                                   DAYCHART_WIDTH, COLOR_RED))

            tempMinY = int(min(day저가))
            tempMaxY = int(max(day고가))
            self.dayPlot[idx].enableAutoRange()
            self.dayPlot[idx].setRange(yRange=[tempMinY, tempMaxY])
            self.dayPlot[idx].getAxis('left').setWidth(GRAPH_YAXIS_WIDTH)

            idx += 1
            #self.dayPlot[idx].addItem(PeriodMoneyItem(day날짜, day거래대금, DAYCHART_WIDTH))
            self.dayPlot[idx].addItem(PeriodMoneyBarTypeItem(day날짜, day거래대금, day양봉, DAYCHART_WIDTH))
            self.dayPlot[idx].enableAutoRange()
            #self.dayPlot[idx].addItem(LegendItem('거래대금(억)', COLOR_BLACK, 0, min(day거래대금+[0])))
            self.dayPlot[idx].getAxis('left').setWidth(GRAPH_YAXIS_WIDTH)

    #def drawSectorGraph(self):
    #    for i in range(NUM_SECTORGRAPH):
    #        self.sectorPlot[i].clear()
    #    if 전체섹터_이름 in self.sectors.keys():
    #        self.drawSectorGraphSingle(0, 전체섹터_이름)
        #if self.selectedSector != "-" and self.selectedSector != 전체섹터_이름:
        #    self.drawSectorGraphSingle(1, self.selectedSector)

    #def drawSectorGraphSingle(self, graphIndex, sector):
    #    sData = self.sectors[sector]
    #    if len(sData.시각) > 0:
    #        xSector = []
    #        for list in sData.시각:
    #            t = str(list)
    #            if len(t) == 5:
    #                t = f"0{t}"
    #            tsec = 3600 * (int(t[0:2]) - 9) + 60 * int(t[2:4]) + int(t[4:6])  # second 형식으로 변환
    #            xSector.append(tsec)
    #        # 전체 프로그램
    #        idx = graphIndex
    #        tempY = min([0] + sData.프로그램대금 + sData.순대금)
    #        self.sectorPlot[idx].addItem(PeriodCurveItem(xSector, sData.프로그램대금, COLOR_RED, Qt.SolidLine))
    #        self.sectorPlot[idx].addItem(PeriodCurveItem(xSector, sData.순대금, COLOR_BLACK, Qt.SolidLine))
    #        self.sectorPlot[idx].addItem(LegendItem(f"{sData.name}", COLOR_RED, 0, tempY,FONT_SIZE_MINUTE_GRAPH))
    #        self.sectorPlot[idx].addItem(LegendItem(f"프로그램", COLOR_RED, 10800, tempY,FONT_SIZE_MINUTE_GRAPH))
    #        self.sectorPlot[idx].addItem(LegendItem(f"순대금", COLOR_BLACK, 16000, tempY,FONT_SIZE_MINUTE_GRAPH))
    #        if sData.순대금[0] == 0 and sData.순대금[-1] == 0:
    #            self.sectorPlot[idx].enableAutoRange()
    #            self.sectorPlot[idx].setRange(xRange=[0, WHOLE_DAY_SEC], yRange=[-1, 1])
    #        else:
    #            self.sectorPlot[idx].enableAutoRange()
    #            self.sectorPlot[idx].setRange(xRange=[0, WHOLE_DAY_SEC])
    #        self.sectorPlot[idx].getAxis('left').setWidth(GRAPH_YAXIS_WIDTH)

    def updateGraph(self):
        if self.initDone is True:
            self.drawMinuteGraph()

    def sortTopList(self):
        for sortKey in self.topList.keys():
            sortArray = []
            for key, value in self.datas.items():
                if sortKey == '거래량증가 상위':
                    sortArray.append([key, value.거래량증가])
                elif sortKey == '순장악력 상위':
                    sortArray.append([key, value.순장악력])
                elif sortKey == '누적거래대금 상위':
                    sortArray.append([key, value.누적거래대금])
                elif sortKey == '순대금 상위':
                    sortArray.append([key, value.순대금])
                elif sortKey == '회전율 상위':
                    sortArray.append([key, value.회전율])
                elif sortKey == '프로그램장악력 상위':
                    sortArray.append([key, value.프로그램장악력])
                elif sortKey == '순회전율 상위':
                    sortArray.append([key, value.순회전율])
                elif sortKey == '프로그램회전율 상위':
                    sortArray.append([key, value.프로그램회전율])
                #elif sortKey == '단주회전율 상위':
                #    sortArray.append([key, value.단주회전율])

            sortArray.sort(key=lambda x: x[1], reverse=True)

            self.topList[sortKey].clear()
            if len(sortArray) > 0:
                #for i in range(min(NUM_TOP_LIST, len(sortArray))):
                for i in range(len(sortArray)):
                    self.topList[sortKey].append(sortArray[i][0])

    def gatherMarketStat(self):
        self.상승종목수, self.보합종목수, self.하락종목수 = 0, 0, 0
        for code in self.codes:
            if self.datas[code].등락율 > 0:
                self.상승종목수 += 1
            elif self.datas[code].등락율 < 0:
                self.하락종목수 += 1
            else:
                self.보합종목수 += 1

    def timeout(self):
        if self.initDone is True and self.file_loading==False:
            if len(self.buy_list) > 0:
                self.buyOrder(self.buy_list[0][0], self.buy_list[0][1])
                print(f"buyOrder : {self.buy_list[0][0]} {self.buy_list[0][1]}")
                self.buy_list.pop(0)
            elif len(self.sell_list) > 0:
                self.sellOrder(self.sell_list[0][0], self.sell_list[0][1])
                print(f"sellOrder : {self.sell_list[0][0]} {self.sell_list[0][1]}")
                self.sell_list.pop(0)
            elif len(self.load_data_list)>0:
                for i in range(MAX_LOAD_DATA):
                    if len(self.load_data_list) > 0:
                        self.loadData(self.load_data_list[0])
                        self.load_data_list.pop(0)
            elif len(self.reqOpt10081_list)>0:
                self.reqOpt10081(self.reqOpt10081_list[0], True)
                self.reqOpt10081_list.pop(0)
            elif len(self.reqOpt10001_list)>0:
                self.reqOpt10001(self.reqOpt10001_list[0])
                self.reqOpt10001_list.pop(0)
            elif len(self.reqOpt90004_list)>0:
                self.reqOpt90004(self.reqOpt90004_list[0][0], self.reqOpt90004_list[0][1])
                self.reqOpt90004_list.pop(0)
            elif len(self.save_data_list):
                self.datas[self.save_data_list[0]]._saveData(True)
                self.save_data_list.pop(0)                

            if self.timerPhase % 5 == 0:
                self.gatherMarketStat()
                #if len(self.load_data_list)==0:
                self.updateGUI()

            currentTime = int(datetime.datetime.now().strftime("%H%M%S"))
            if self.timerPhase == 0:
                self.statusBar.showMessage(f"| 상승:{self.상승종목수} | 보합:{self.보합종목수} | 하락:{self.하락종목수} |  "
                                        f"RAM : {str(psutil.virtual_memory().percent)}% @ {currentTime}")
                print(f"| 상승:{self.상승종목수} | 보합:{self.보합종목수} | 하락:{self.하락종목수} |  "
                        f"RAM : {str(psutil.virtual_memory().percent)}% @ {currentTime}")

            if self.timerPhase == 24:    self.timerPhase = 0
            else:                        self.timerPhase += 1

            # 동시호가전 dataString 정리 
            if self.동시호가전_데이터정리 is False:
                if 데이터정리_시각 < currentTime and currentTime < 데이터정리_시각+100:
                    self.동시호가전_데이터정리 = True
                    for code in self.codes:
                        self.datas[code]._saveData(True)

            # 일봉자동 로드
            if self.장마감_일봉로드 is False:
                if 일봉로드_시각 < currentTime and currentTime < 일봉로드_시각+100:
                    self.장마감_일봉로드 = True
                    self.getDayData()

    def updateGUI(self):
        #self.sortTopList()
        # self.clearTables()
        for i in range(NUM_TABLE):
            self.tableArray[i].condListToTable()

        self.updateGraph()
        self.appendDayTable()

    def loadData(self, code):
        FileName = f"{self.loadDate}_{self.datas[code].name}.csv"
        DirFileName = f"{LOAD_DIR_NAME}\\{self.loadDate}\\{FileName}"

        if self.datas[code].체결시간 != 0:  # 복기된 상태면
            return

        self.datas[code].복기모드 = True  # 복기모드 flag
        self.datas[code].복기날짜 = self.loadDate
        if len(self.datas[code].dayDatas.날짜) > 0:
            for i in range(len(self.datas[code].dayDatas.날짜)):
                if self.datas[code].dayDatas.날짜[-1-i] == self.loadDate:
                    self.datas[code].복기보정값 = i+1
                    break
        else:
            self.datas[code].복기보정값 = 0

        try:
            # with open(DirFileName, 'r', encoding='utf-8') as f:
            with open(DirFileName, 'r') as f:
            
        #f = open(DirFileName, 'r')
                rdr = csv.reader(f, delimiter=',')
                for count, line in enumerate(rdr):
                    if line[0] == '체결시간' or line[0] == ' ':  # 첫줄 / 끝줄 처리
                        continue
                    # print(line)
                    if line[0] in ['거']:
                        매도거래원, 매도거래원수량, 매도거래원증감 = [], [], []
                        매수거래원, 매수거래원수량, 매수거래원증감 = [], [], []
                        for i in range(0,5,1):
                            매도거래원.append(line[i*3+1])
                            매도거래원수량.append(int(line[i*3+2]))
                            매도거래원증감.append(int(line[i*3+3]))
                        for i in range(5,10,1):
                            매수거래원.append(line[i*3+1])
                            매수거래원수량.append(int(line[i*3+2]))
                            매수거래원증감.append(int(line[i*3+3]))
                        self.datas[code].거래원추가(매도거래원, 매도거래원수량, 매도거래원증감, 매수거래원, 매수거래원수량, 매수거래원증감)
                    elif line[0] in ['호']:
                        #호가시간, 매도호가합, 매수호가합, 매도호가변동, 매수호가변동, 매도호가수량1, 매수호가수량1, 매도호가변동1, 매수호가변동1, 매도호가대금, 매수호가대금 = list(map(int, line[1:12]))
                        호가시간, 매도호가합, 매수호가합, 매도호가수량1, 매수호가수량1, 매도호가대금, 매수호가대금 = list(map(int, line[1:8]))
                        #self.datas[code].updateHoga(호가시간, 매도호가합, 매수호가합, 매도호가변동, 매수호가변동, 매도호가수량1, 매수호가수량1, 매도호가변동1, 매수호가변동1, 매도호가대금, 매수호가대금)
                        self.datas[code].updateHoga(호가시간, 매도호가합, 매수호가합, 매도호가수량1, 매수호가수량1, 매도호가대금, 매수호가대금)
                    elif line[0] in ['프']:
                        체결시간, 순프로그램 = int(line[1]), int(line[2])
                        self.datas[code].updateProgram(체결시간, 순프로그램)
                    else:
                        체결시간, 현재가, 등락율, 거래량 = int(line[0]), int(line[1]), float(line[2]), int(line[3])
                        #순프로그램, 매도호가합, 매수호가합 = int(line[4]), int(line[5]), int(line[6])
                        
                        self.pushRealData(code, 체결시간, 현재가, 등락율, 거래량)

                    #if count % 1000 == 0:
                    #    print(f"Reading File {FileName} : Line Number {count}")
                print(f"Reading File {FileName} : Done at {datetime.datetime.now().strftime('%H:%M:%S')}")
        #f.close

        except Exception as e:
            print(f"File Load error : {e}")
        #self.drawMinuteGraph()

        #print(self.datas[code].조건식_값들)

    def loadDayData(self):
        for code in self.codes:
            self.loadDayDataSingle(code)
        print(f"일봉데이터 로드 완료")

    def loadDayDataSingle(self, code):
        FileName = f"{DAY_DIR_NAME}/{self.datas[code].name}.csv"

        if self.datas[code].일봉로드:
            return 
        self.datas[code].dayDatas.clear()

        try:
            with open(FileName, 'r') as f:
                rdr = f.readlines()
                for count, line_raw in enumerate(rdr):
                    line = line_raw.split(',')
                    if count == 0 :  # 첫줄
                        continue
                    #if line[0] == '' or line[0]=='EOL' or line[0].lstrip() == TODAY:  # / 끝줄 / 당일데이터 처리
                    if line[0] == '' or line[0] == 'EOL':  # / 끝줄 / 당일데이터 처리
                        break

                    if self.datas[code].유통주식수>0: 주식수 = self.datas[code].유통주식수
                    else:                            주식수 = self.datas[code].주식수
                    #print(line[0].lstrip(), int(line[1]), float(line[2])/100, int(line[3]), int(line[4]), int(line[5]), int(line[6]))
                    self.datas[code].dayDatas.append(line[0].lstrip(), int(line[1]),
                                               float(line[2])/100, int(line[3]),
                                               int(line[4]), int(line[5]), int(line[6]), 주식수)
                print(f"일봉로드 완료 {datetime.datetime.now().strftime('%H:%M:%S')} : {FileName}")
                self.datas[code].일봉로드 = True
           
                f.close
        except Exception as e:
            print(f"File Load error @ loadDayDataSingle {FileName} : {e}")

    def checkNoLatestDayData(self):
        print("#### 최근 일봉데이터 없는 종목 요청 시작 ####")
        latestDate = 0
        for code in self.codes:
            if len(self.datas[code].dayDatas.날짜) > 0:
                if latestDate < int(self.datas[code].dayDatas.날짜[-1]) and \
                    self.datas[code].dayDatas.날짜[-1]!=TODAY:
                    latestDate = int(self.datas[code].dayDatas.날짜[-1])
        print(f"latestDate = {latestDate}")
        for code in self.codes:
            if len(self.datas[code].dayDatas.날짜) == 0:
                self.reqOpt10081_list.append(code)
            else:
                if int(self.datas[code].dayDatas.날짜[-1]) < latestDate:
                    self.reqOpt10081_list.append(code)

    def checkNoLatestDayDataForToday(self):
        print("#### 최근 일봉데이터 없는 종목 요청 시작 ####")
        latestDate = 0
        for code in self.codes:
            if len(self.datas[code].dayDatas.날짜) > 0:
                if latestDate < int(self.datas[code].dayDatas.날짜[-1]):
                    latestDate = int(self.datas[code].dayDatas.날짜[-1])
        print(f"latestDate = {latestDate}")
        for code in self.codes:
            if len(self.datas[code].dayDatas.날짜) == 0:
                self.reqOpt10081_list.append(code)
            else:
                if int(self.datas[code].dayDatas.날짜[-1]) < latestDate:
                    self.reqOpt10081_list.append(code)


    def checkNoEffectiveStockCountCase(self):
        print("#### 유통주식수 없는 종목 요청 시작 ####")
        for code in self.codes:
            if self.datas[code].유통주식수 == 0:
                self.reqOpt10001_list.append(code)  # TR큐에 추가 -> Timer에서 처리

    def loadUserConfig(self):
        try:
            with open(USER_COND_FILE, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    config = line.split(' ')
                    if config[0] == '랜덤복기개수':
                        self.labelEditDict['랜덤복기개수'].setText(config[1])
                    elif config[0] == '복기날짜':
                        self.labelEditDict['복기날짜'].setText(config[1])
                    elif config[0] == 'CHECK_BOX':
                        self.checkBoxDict[config[1]].setCheckState(config[2])
                    elif config[0] == 'CHECK_BOX_SUB':
                        self.checkBoxDictSub[config[1]].setCheckState(config[2])
                    elif config[0] == 'TABLE_COMBO_INDEX':
                        self.tableArray[int(config[1])].combo.setCurrentIndex(int(config[2]))
                print(f"Reading User Config File {USER_COND_FILE} : Done")
                f.close
        except Exception as e:
            print(f"File Load error : {e}")

    def loadTypeFile(self):
        print(f"#### 종목타입 로드 시작 ####")
        for realData in self.datas.values():
            if realData.시가총액 >= 시가총액_대형주:
                realData.종목타입 = '대형주'
            elif realData.시가총액 >= 시가총액_중형주:
                realData.종목타입 = '중형주'
            else:
                realData.종목타입 = '소형주'
        for key in ['대형주', '중형주', '소형주']:
            self.codeTypeCombo.addItem(key)
        #try:
        #    with open(TYPE_FILE, 'r') as f:
        #        lines = f.readlines()
        #        for line in lines:
        #            config = line.split(',')
        #            if config[0] in self.names:
        #                종목코드 = self.nameToCode[config[0]]
        #                종목타입 = config[1].rstrip('\n')
        #                if 종목타입 != '':
        #                    self.datas[종목코드].종목타입 = 종목타입
        #        f.close
#
        #        types = {}
        #        for realData in self.datas.values():
        #            iType = realData.종목타입
        #            iName = realData.name
        #            #if iType != '':
        #            if iType in types.keys():
        #                types[iType].append(iName)
        #            else:
        #                types[iType] = [iName]
        #        for key, value in types.items():
        #            print(f"{key} | {value}")
        #            self.codeTypeCombo.addItem(key)

        #        print(f"#### 종목타입 로드 완료 : {TYPE_FILE}")

        #except Exception as e:
        #    print(f"Type File Load error : {e}")

    def loadSector(self):
        print(f"#### 섹터파일 로드 시작 ####")
        try:
            with open(SECTOR_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    print(line)
                    config = line.split('|')
                    섹터 = config[0]
                    if 섹터 not in self.sectors:
                        self.sectors[섹터] = SectorData(섹터)

                        for i in range(1, len(config)):
                            if config[i]!='\n' and config[i]!='':   # EOL 처리
                                if config[i] in self.names:
                                    code = self.nameToCode[config[i]]
                                    self.datas[code].appendSector(섹터)
                                    #print(f"{섹터} 종목 추가 = {config[i]}")
                                    self.sectors[섹터].appendStock(code, config[i], self.datas[code].유통시가총액)
                                else:
                                    print(f"{섹터} | {config[i]} (Skip. Not in Name List)")
                        print(f"{섹터} 시가총액 = {self.sectors[섹터].시가총액}")
                        #print(f"{self.sectors[섹터].codes} | {self.sectors[섹터].names}")
                    else:
                        print(f"섹터중복! {섹터}")
                print(f"Reading Sector File {SECTOR_FILE} : Done")
                f.close

        except Exception as e:
            print(f"Sector Load error : {e}")

    # 전체시장 섹터
    def setMarketSector(self):
        print(f"#### 전체 섹터에 종목들 등록 ####")
        섹터 = 전체섹터_이름
        self.sectors[섹터] = SectorData(섹터)
        for code in self.codes:
            self.sectors[섹터].appendStock(code, self.datas[code].name, self.datas[code].유통시가총액)
            #print(f"{섹터} 종목 추가 = {self.datas[code].name}")
            self.datas[code].appendSector(섹터)

    def saveUserConfig(self):
        tempStr = ""
        tempStr = f"{tempStr}랜덤복기개수 {self.loadRandomNum} \n"
        tempStr = f"{tempStr}복기날짜 {self.loadDate} \n"
        for key in CHECK_BOX_KEY:
            keyStrip = key.strip("'")
            tempStr = f"{tempStr}CHECK_BOX {keyStrip} {self.checkBoxDict[key].checkState()} \n"
        for key in CHECK_BOX_KEY_SUB:
            keyStrip = key.strip("'")
            tempStr = f"{tempStr}CHECK_BOX_SUB {keyStrip} {self.checkBoxDictSub[key].checkState()} \n"
        for i in range(NUM_TABLE):
            tempStr = f"{tempStr}TABLE_COMBO_INDEX {i} {self.tableArray[i].combo.currentIndex()} \n"
        #    tempStr = f"{tempStr} \n"
        try:
            with open(USER_COND_FILE, "w") as f:
                f.write(tempStr)
                print(f"{USER_COND_FILE} File writting complete @ {datetime.datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"File writting error : {e}")

    def saveCodeList(self):
        tempStr = ""
        for code in self.codes:
            realData = self.datas[code]
            tempStr = f"{tempStr}{realData.code},{realData.name},{realData.주식수},{realData.유통주식수},{realData.시가총액}, \n"
        try:
            with open(CODE_LIST_FILE, "w") as f:
                f.write(tempStr)
                print(f"{CODE_LIST_FILE} File writting complete @ {datetime.datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"File writting error : {e}")

    def loadCodeList(self):
        try:
            with open(CODE_LIST_FILE, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    config = line.split(' ')

                    if config[0] != '':
                        code, name = config[0], config[1]

                        self.datas[code] = RealData(code, name, self)
                        self.codes.append(code)
                        self.names.append(name)
                        self.nameToCode[name] = code

                print(f"Reading {CODE_LIST_FILE} File : Done")
                f.close
        except Exception as e:
            print(f"File Load error : {e}")

    def loadEffectiveStockCount(self):
        for code in self.codes:
            fileName = self.datas[code].effectiveStockCountFileName

            try:
                with open(fileName, 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        config = line.split(' ')

                        self.datas[code].유통주식수 = int(config[0])
                        self.datas[code].유통비율 = round(safeDivide(100*int(config[0]), self.datas[code].주식수, 100), 2)
                        self.datas[code].유통시가총액 = int(self.datas[code].시가총액 *self.datas[code].유통비율 / 100)

                    print(f"유통주식수 로드 Done | {fileName} | 유통주식수={config[0]} | 시가총액 = {self.datas[code].시가총액} |"
                          f"유통비율={self.datas[code].유통비율} | 유통시가총액 = {self.datas[code].유통시가총액}")
                    f.close
            except Exception as e:
                print(f"File Load error @ loadEffectiveStockCount {fileName} : {e}")

    def initTradeDataAll(self):
        for code in self.codes:
            self.initTradeData(code)
            realData = self.datas[code]
            td = realData.tradeData
            print(f"TradeData {realData.name} {td.고가240} {td.고가120} {td.R0} {td.R1} {td.R2} {td.R3} {td.stateRB} "
                  f"{td.lastStandby} {td.lastTrade} {td.RB_물량} {td.RB_평단} {td.RB_매수일} {td.RB_기준일}")
        #self.dayTable2.clearTables()
        #self.appendDayTable2()

    def saveTradeDataAll(self):
        tempStr = ""
        for code in self.codes:
            realData = self.datas[code]
            td = realData.tradeData
            tempStr = f"{tempStr}{realData.name},{realData.code},{td.고가240},{td.고가120}," \
                         f"{int(td.R0)},{int(td.R1)},{int(td.R2)},{int(td.R3)},{td.stateRB}," \
                         f"{td.lastStandby},{td.lastTrade},{td.RB_물량},{int(td.RB_평단)},{td.RB_매수일},{td.RB_기준일},\n"

        tempStr = f"{tempStr}EOL"

        try:
            with open(TRADE_DATA_FILE, "w") as f:
                f.write(tempStr)
                print(f"{TRADE_DATA_FILE} File writting complete @ {datetime.datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"File writting error : {e}")

    def loadTradeDataAll(self):
        try:
            with open(TRADE_DATA_FILE, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    config = line.split(',')

                    if config[0] != 'EOL' and len(config)>0:
                        name, code = config[0], config[1]
                        고가240, 고가120 = int(config[2]), int(config[3])
                        R0, R1, R2, R3 = int(config[4]), int(config[5]), int(config[6]), int(config[7])
                        stateRB = int(config[8])
                        if config[9]=='True':   lastStandby = True
                        else:                   lastStandby = False
                        if config[10]=='True':  lastTrade = True
                        else:                   lastTrade = False

                        RB_물량, RB_평단, RB_매수일, RB_기준일 = float(config[11]), int(config[12]), config[13], config[14]

                        if code in self.codes:
                            self.datas[code].tradeData.update(고가240, 고가120, R0, R1, R2, R3, stateRB,
                                lastStandby, lastTrade, RB_물량, RB_평단, RB_매수일, RB_기준일)

                print(f"Reading {TRADE_DATA_FILE} File : Done")
                f.close
        except Exception as e:
            print(f"File Load error : {e}")

        for code in self.codes:
            realData = self.datas[code]
            td = realData.tradeData
            print(f"TradeData {realData.name} {td.고가240} {td.고가120} {td.R0} {td.R1} {td.R2} {td.R3} {td.RD} {td.stateRB} "
                  f"{td.lastStandby} {td.lastTrade} {td.RB_물량} {td.RB_평단} {td.RB_매수일} {td.RB_기준일}")

    def appendDayTable(self):
        #self.dayTable.clearTables()
        self.dayTable.refreshTable()
        #tempList = []
        #if self.selectedSector != "-":
        #    codes = self.sectors[self.selectedSector].codes
        #    for code in codes:
        #        #"등락율","거래증가","누적대금","순대금","P대금",'회전율',"순회전율","P회전율"
        #        tempList.append([self.datas[code].name, round(self.datas[code].등락율,2),
        #                         round(self.datas[code].거래량증가), int(self.datas[code].누적거래대금),
        #                         int(self.datas[code].순프로그램대금), int(self.datas[code].순대금),
        #                         self.datas[code].프로그램회전율, self.datas[code].순회전율])
        #    self.dayTable.appendList(tempList)
        #    self.dayTable.setTitle(f"{self.selectedSector} 섹터")

    def clearTables(self):
        for i in range(NUM_TABLE):
            self.tableArray[i].clearTopList()

    def updateSelectedCodeEdit(self, inputText):
        index = self.names.index(inputText)
        self.labelEditDict['종목명'].setText(inputText)
        self.selectedCode = self.codes[index]
        self.labelEditDict['분봉초'].setText(str(self.datas[self.selectedCode].periodUnit))
        #if len(self.datas[self.selectedCode].섹터) > 0:
        #    self.selectedSector = self.datas[self.selectedCode].섹터[0]
        self.drawMinuteGraph()
        #self.appendDayTable2()

    @pyqtSlot()
    def loadCurrButton_clicked(self):
        if self.selectedCode != -1:
            self.datas[self.selectedCode].clear()
            self.load_data_list.append(self.selectedCode)
        #self.updateGUI()
        #self.timeout()
        

    def loadRandomButton_clicked(self):
        self.file_loading = True
        t = threading.Thread(target=self._loadRandomButton_clicked, args=())
        t.start()

    def _loadRandomButton_clicked(self):
        for i in range(self.loadRandomNum):
            key, realData = random.choice(list(self.datas.items()))
            self.loadData(key)
        self.file_loading = False

    def loadAllButton_clicked(self):
        self.file_loading = True
        t = threading.Thread(target=self._loadAllButton_clicked, args=())
        t.start()

    def _loadAllButton_clicked(self):
        for key, realData in self.datas.items():
            if realData.체결시간 == 0:  # 복기된 상태가 아니면
                self.loadData(key)
        self.file_loading = False

    def loadStrongButton_clicked(self):
        self.file_loading = True
        t = threading.Thread(target=self._loadStrongButton_clicked, args=())
        t.start()

    def _loadStrongButton_clicked(self):
        load_count = 0
        for key, realData in self.datas.items():
            if realData.체결시간==0:  # 복기된 상태가 아니면
                if getMax(realData.dayDatas.거래대금, 강한놈조건['기간']) >= 강한놈조건['거래대금'] or \
                    realData.dayDatas.고가등락율[-1] >= 강한놈조건['고가등락율'] or \
                    realData.dayDatas.종가등락율[-1] >= 강한놈조건['종가등락율']:
                    #self.load_data_list.append(key)
                    self.loadData(key)
                    load_count += 1
        print(f'종목 로드 개수 : {load_count}')
        self.file_loading = False

    def loadTypeButton_clicked(self):
        for key, realData in self.datas.items():
            if realData.체결시간 == 0:  # 복기된 상태가 아니면
                if realData.종목타입 == self.codeTypeCombo.currentText():
                    self.load_data_list.append(key)

    def refreshChartButton_clicked(self):
        self.datas[self.selectedCode].clear()
        self.datas[self.selectedCode].chartWidth = getChartWidth(self.datas[self.selectedCode].periodUnit)
        self.loadData(self.selectedCode)
        self.updateGUI()

    # 분봉 scroll 영역 세팅
    def adjustMinuteXAxes(self, min, max):
        for iPlot in self.plot:
            iPlot.setRange(xRange=[min, max])

    @pyqtSlot(int)
    def onAxisSliderMoved(self, value):
        # scrollbar value = 0~99
        singleStep = 1/(self.scrollStep * 100)
        r = value * singleStep 
        l1 = r * WHOLE_DAY_SEC
        l2 = l1 + WHOLE_DAY_SEC * self.scrollStep * self.zoomRatio
        self.adjustMinuteXAxes(math.floor(l1), math.ceil(l2))


    @pyqtSlot(int)
    def onZoomSliderMoved(self, value):
        self.zoomRatio = round((100-value)/100,2)
        self.scrollbar.setPageStep( int(self.zoomRatio*self.scrollStep * 100) )
        self.onAxisSliderMoved(self.scrollbar.value())

    # Exit 버튼을 클릭시 실행. 프로그램을 종료한다.
    @pyqtSlot()
    def exitApp(self):
        self.saveUserConfig()
        self.saveCodeList()
        QCoreApplication.instance().quit()

    def saveDayDataButton_clicked(self):
        for code in self.codes:
            realData = self.datas[code]
            dayData = self.datas[code].dayDatas
            tempStr = "일자,거래량,거래대금,시가,고가,저가,종가"
            for i in range(len(dayData.날짜)):
                tempStr = f"{tempStr}\n{dayData.날짜[i]}, {dayData.거래량[i]}, {int(dayData.거래대금[i]*100)}, " \
                             f"{dayData.시가[i]}, {dayData.고가[i]}, {dayData.저가[i]}, {dayData.종가[i]},"

            if realData.시가 != 0:
                tempStr = f"{tempStr}\n{TODAY}, {realData.누적거래량}, {int(realData.누적거래대금)}, " \
                             f"{realData.시가}, {realData.고가}, {realData.저가}, {realData.현재가},"

            DATE_FILE = f"{DAY_DIR_NAME}/{self.datas[code].name}.csv"

            try:
                with open(DATE_FILE, "w") as f:
                    f.write(tempStr)
                    print(f"{DATE_FILE} File writting complete @ {datetime.datetime.now().strftime('%H:%M:%S')}")
            except Exception as e:
                print(f"File writting error : {e}")

    def getDayData(self):
        # 전 종목의 일봉 데이터
        print(f"##### 일봉 데이터 로드 시작! 등록 종목 개수 = {len(self.codes)} #####")
        for i, code in enumerate(self.codes):
            #print(f"{i}/{len(self.codes)} {code}")
            self.reqOpt10081_list.append(code)

    def getUnloadedDayData(self):
        print("#### 일봉데이터 없는 종목 요청 시작 ####")
        for code in self.codes:
            if len(self.datas[code].dayDatas.날짜) <= 1:
                self.reqOpt10081_list.append(code)  # TR큐에 추가 -> Timer에서 처리
            else:
                if self.datas[code].dayDatas.날짜[-1] != TODAY:
                    self.reqOpt10081_list.append(code)  # TR큐에 추가 -> Timer에서 처리

    # 유통주식수
    def getEffectiveStockCount(self):
        for i, code in enumerate(self.codes):
            #print(f"{i}/{len(self.codes)} {code}")
            self.reqOpt10001_list.append(code)

    def viewDayGraphWindow(self):
        self.dayGraphWindow.show()

    def viewMinuteGraphWindow(self):
        self.minuteGraphWindow.show()

    def viewSectorWindow(self):
        self.sectorWindow.show()

    def buyOrder(self, code, nQty):
        self.objKiwoom.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                                ["RqBuyOrder", "2000", self.accountNo, 1, code, nQty, 0, "03", ""])

    def sellOrder(self, code, nQty):
        self.objKiwoom.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                                ["RqSellOrder", "2000", self.accountNo, 2, code, nQty, 0, "03", ""])
    
    # 주식기본정보 요청 (유통주식수 받아오는 용도)
    def reqOpt10001(self, code):
        # opt10001 TR 요청
        print(f"Requesting opt10001(주식기본정보, 유통주식로드) for {code} {self.datas[code].name}")
        self.objKiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.objKiwoom.dynamicCall("CommRqData(QString, QString, int, QString", "주식기본정보요청", "opt10001", 0, "1001")

    # 장중투자자별매매차트요청 - 코스피/코스닥 외인 기관 개인등 추이
    def reqOpt10066(self, code):
        print(f"Requesting opt10066(장중투자자별매매차트) for {code} {self.datas[code].name}")
        self.objKiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.objKiwoom.dynamicCall("CommRqData(QString, QString, int, QString", "주식기본정보요청", "opt10001", 0, "1001")

    # 일봉차트 조회 TR
    def reqOpt10081(self, code, single:bool):
        print(f"Requesting opt10081(일봉차트조회) for {code} {self.datas[code].name}")
        self.objKiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.objKiwoom.dynamicCall("SetInputValue(QString, QString)", "기준일자", TODAY)
        self.objKiwoom.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", 1)
        if single is True:
            self.objKiwoom.dynamicCall("CommRqData(QString, QString, int, QString", "주식일봉차트조회단일", "opt10081", 0, "1081")
        else:
            self.objKiwoom.dynamicCall("CommRqData(QString, QString, int, QString", "주식일봉차트조회", "opt10081", 0, "1081")

    # 프로그램매매 현황
    def reqOpt90004(self, bKospi, nNext):
        sScrNo = f"9{self.reqOpt90004_scrNo:03}"
        self.reqOpt90004_scrNo = (self.reqOpt90004_scrNo + 1) % 100
        if bKospi is True:
            sRqName = "코스피"
        else:
            sRqName = "코스닥"
        #print(f"Requesting Program Data (opt90004) | scrNo={sScrNo}")
        self.objKiwoom.dynamicCall("SetInputValue(QString, QString)", "일자", TODAY)
        if bKospi is True:
            self.objKiwoom.dynamicCall("SetInputValue(QString, QString)", "시장구분", "P00101")  # P00101: 코스피, P10102: 코스닥
        else:
            self.objKiwoom.dynamicCall("SetInputValue(QString, QString)", "시장구분", "P10102")  # P00101: 코스피, P10102: 코스닥
        self.objKiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", sRqName, "opt90004", nNext, sScrNo)

    # 종료시 실행할 작업
    #def __del__(self):
    #    self.objKiwoom.dynamicCall("SetRealRemove(str, str)", "ALL", "ALL")




# 메인함수
if __name__ == "__main__":
    import cProfile, pstats, io
    from pstats import SortKey
    import sys

    if PROFILE_EN:
        pr = cProfile.Profile()
        pr.enable()

    MyWindow.setHiDpi()

    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion')) # ['Windows', 'WindowsXP', 'WindowsVista', 'Motif', 'CDE', 'Plastique', 'Cleanlooks', 'Fusion']

    myWindow = MyWindow()
    myWindow.show()
    #myWindow.dayGraphWindow.show()

    app.exec_()

    if PROFILE_EN:
        pr.disable()
        s = io.StringIO()
        sortby = SortKey.CUMULATIVE
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())

        try:
            with open(PROFILE_FILE+f"{datetime.datetime.now().strftime('%y%m%d_%H%M%S')}", "w") as f:
                f.write(s.getvalue())
                print(f"File {PROFILE_FILE} writting complete @ {datetime.datetime.now().strftime('%y%m%d_%H%M%S')}")
        except Exception as e:
            print(f"File writting error : {e}")
