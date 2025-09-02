from Global import *
from BaseClass import *
from Utils import *

class PeriodicData:
    def __init__(self):
        self.clear()

    def clear(self):
        self.구간순회전율 = []
        self.표준편차, self.볼밴상단, self.볼밴하단 = [], [], []
        self.체강이평 = {1:[], 5:[], 10:[]}
        self.순회전율표준편차, self.순회전율볼밴상단, self.순회전율볼밴하단 = [], [], []
        self.양봉 = []
        self.범위체강 = {60:[]}
        self.범위체강이평 = {5:[], 10:[]}
        self.구간고가눌림 = {3:[], 4:[], 5:[], 6:[], 7:[], 8:[], 9:[], 10:[]}
        # 구간최대값들
        self.최대구간프로그램회전율, self.최대구간순회전율 = -1, -1
        self.최대구간누적거래대금 = 0

        self.구간VAL    = {key:[] for key in 구간VAL_KEYS}
        self.구간OCHL   = {key:[] for key in 구간OCHL_KEYS}
        self.구간변동     = {key:[] for key in 구간변동_KEYS}
        self.구간변동율     = {key:[] for key in 구간변동율_KEYS}
        self.구간DELTA = {}
        for key in 구간DELTA_KEYS:
            keyStr, keyPeriod = key
            self.구간DELTA[keyStr] = {}
            for period in keyPeriod:  # ex) key[0] = "현재가" | key[1] = [20,30,...]
                self.구간DELTA[keyStr][period] = []

        self.구간DELTA_ACC = {}
        for key in 구간DELTA_ACC_KEYS:
            keyStr, keyPeriod = key
            self.구간DELTA_ACC[keyStr] = {}
            for period in keyPeriod:  # ex) key[0] = "현재가" | key[1] = [20,30,...]
                self.구간DELTA_ACC[keyStr][period] = []

        self.구간강조 = {}
        for key in 구간강조_KEYS:
            keyStr, keyVal = key
            self.구간강조[keyStr] = {}
            for v in keyVal:    # 구간강조["순회전율"][1] = [false, True, ...]
                self.구간강조[keyStr][v] = []

        self.구간이평 = {}
        for key in 구간이평_KEYS:
            keyStr, keyPeriod = key
            self.구간이평[keyStr] = {}
            for period in keyPeriod:   # ex) key[0] = "현재가" | key[1] = [20,30,...]
                self.구간이평[keyStr][period] = []

        self.구간복합이평 = {}
        for key in 구간복합이평_KEYS:
            keyStr, keyPeriod = key
            self.구간복합이평[keyStr] = {}
            for period in keyPeriod:   # ex) key[0] = "현재가" | key[1] = [20,30,...]
                self.구간복합이평[keyStr][period] = []

        self.구간ATR = {}
        for key in 구간ATR_KEYS:
            keyStr, keyPeriod = key
            self.구간ATR[keyStr] = {}
            for period in keyPeriod:   # ex) key[0] = "현재가" | key[1] = [20,30,...]
                self.구간ATR[keyStr][period] = []                

        self.구간SPTRD_H, self.구간SPTRD_L = {}, {}
        self.구간SPTRD_H2, self.구간SPTRD_L2 = {}, {}
        for key in 구간SPTRD_KEYS:
            keyStr, keyPeriod = key
            self.구간SPTRD_H[keyStr] = {}
            self.구간SPTRD_L[keyStr] = {}
            self.구간SPTRD_H2[keyStr] = {}
            self.구간SPTRD_L2[keyStr] = {}
            for period in keyPeriod:   # ex) key[0] = "현재가" | key[1] = [20,30,...]
                self.구간SPTRD_H[keyStr][period] = []
                self.구간SPTRD_L[keyStr][period] = []
                self.구간SPTRD_H2[keyStr][period] = []
                self.구간SPTRD_L2[keyStr][period] = []

    def append(self, mother):
        self.구간VAL["시각"].append(mother.periodicUpdateTime)
        
        for key in self.구간VAL.keys():
            if key in ["시각", "최고매물대가격", "매수평균가", "매도평균가", '평균가볼밴상단', '평균가볼밴하단', '순매수율']:
                continue
            elif key=='파바박대금':
                self.구간VAL[key].append(mother.fastData.result['PlusMoneyAcc']+mother.fastData.result['MinusMoneyAcc'])
            #elif key=='순매수율':
            #    self.구간VAL[key].append( safeDivideRounded(100*self.구간VAL['순대금'][1][-1], self.구간VAL['누적거래대금'][1][-1], 0, 1) )
            else:
                self.구간VAL[key].append(getattr(mother, key))

        #self.구간VAL["최고매물대가격"].append(mother.getMaxVolumeProfilePrice())
        #self.구간VAL["매수평균가"].append( safeDivideRounded(mother.매수대금, mother.매수거래량, mother.시가, 0) )
        #self.구간VAL["매도평균가"].append( safeDivideRounded(mother.매도대금, mother.매도거래량, mother.시가, 0) )
  

        for key in self.구간OCHL.keys():
            #self.구간OCHL[key].append(getattr(mother, f"구간{key}OCHL").getValues())
            self.구간OCHL[key].append(mother.구간OCHL[key].getValues())

        for key in self.구간변동.keys():
            if key=="현재가":
                self.구간변동[key].append(getTrueRange(self.구간OCHL[key], mother.전일종가))
            else:
                self.구간변동[key].append(getTrueRange(self.구간OCHL[key], 0))

        for key in self.구간변동율.keys():
            if key=="현재가":
                self.구간변동율[key].append(getTrueRangeRate(self.구간OCHL[key]))

        for keyStr in self.구간ATR.keys():
            for period in self.구간ATR[keyStr].keys():
                self.구간ATR[keyStr][period].append(getMA(self.구간변동[keyStr], period, self.구간변동[keyStr][0]))

        for key in self.구간고가눌림.keys():
            self.구간고가눌림[key].append(round(mother.당일고가*(100-key)/100, 0))

        for keyStr in self.구간DELTA.keys():
            if keyStr in (['순매수율', '누적순매수율','보정대금'] + [f'평균가등락율{p}' for p in 평균가_KEYS]):
                continue
            else:
                for period in self.구간DELTA[keyStr].keys():
                    self.구간DELTA[keyStr][period].append( getListDelta(self.구간VAL[keyStr], period ))

        for period in self.구간DELTA['순매수율'].keys():
            self.구간DELTA['순매수율'][period].append( safeDivideRounded(100*self.구간DELTA['순대금'][1][-1], self.구간DELTA['누적거래대금'][1][-1], 0, 1) )
        
        for p in 평균가_KEYS:
            keyStr = f'평균가등락율{p}'
            # 1일평균가 제외, 첫 봉에 대한 평균가 등락율 계산. 일봉 데이터 없는경우는 패스
            #if len(self.구간DELTA[keyStr][1])==0 and p!=1 and len(mother.dayDatas.평균가이평[p-1])>mother.복기보정값:  
            # 첫봉은 0으로
            if len(self.구간DELTA[keyStr][1])==0:  
                self.구간DELTA[keyStr][1].append( 0 )
            else:
                self.구간DELTA[keyStr][1].append( getListDelta(self.구간VAL[keyStr], period ))
                            
        
        for keyStr in self.구간DELTA_ACC.keys():
            for period in self.구간DELTA_ACC[keyStr].keys():
                self.구간DELTA_ACC[keyStr][period].append( getListSum( self.구간DELTA[keyStr][1], period, False ) )

        #for period in self.구간DELTA['보정대금'].keys():
        #    #self.구간DELTA['보정대금'][period].append( getCalibratedMoney(self.구간DELTA['누적거래대금'][1][-1], self.구간DELTA['회전율'][1][-1], 1) )
        #    self.구간DELTA['보정대금'][period].append( getCalibratedMoney(self.구간DELTA['누적거래대금'][1][-1], (self.구간DELTA['매수파워'][1][-1]+self.구간DELTA['매도파워'][1][-1]), 5) )
            
        for keyStr in self.구간강조.keys():
            for v in self.구간강조[keyStr].keys():
                if self.구간DELTA[keyStr][1][-1] >= v:
                    self.구간강조[keyStr][v].append(True)
                else:
                    self.구간강조[keyStr][v].append(False)

        for keyStr in self.구간이평.keys():
            for period in self.구간이평[keyStr].keys():
                if keyStr=="현재가":
                    self.구간이평[keyStr][period].append(getMA(self.구간VAL[keyStr], period, mother.전일종가))
                elif keyStr=="체강":
                    self.구간이평[keyStr][period].append(getMA(self.구간VAL[keyStr], period, 100))
                else:
                    self.구간이평[keyStr][period].append(getMA(self.구간VAL[keyStr], period, 0))

        for keyStr in self.구간복합이평.keys():
            for period in self.구간복합이평[keyStr].keys():
                if keyStr=="현재가":
                    self.구간복합이평[keyStr][period].append(getOCHLListMA(self.구간OCHL[keyStr], period, OCHL(mother.전일종가)))
                elif keyStr=="체강":
                    self.구간복합이평[keyStr][period].append(getOCHLListMA(self.구간OCHL[keyStr], period, OCHL(100)))
                else:
                    self.구간복합이평[keyStr][period].append(getOCHLListMA(self.구간OCHL[keyStr], period, OCHL(0)))

        for keyStr in self.구간SPTRD_H.keys():
            for period in self.구간SPTRD_H[keyStr].keys():
                self.구간SPTRD_H[keyStr][period].append( round(self.구간복합이평[keyStr][period][-1] + SPTRD_MULTIPLE*self.구간ATR[keyStr][period][-1]) )
                self.구간SPTRD_L[keyStr][period].append( round(self.구간복합이평[keyStr][period][-1] - SPTRD_MULTIPLE*self.구간ATR[keyStr][period][-1]) )
                self.구간SPTRD_H2[keyStr][period].append( round(self.구간복합이평[keyStr][period][-1] + 2*SPTRD_MULTIPLE*self.구간ATR[keyStr][period][-1]) )
                self.구간SPTRD_L2[keyStr][period].append( round(self.구간복합이평[keyStr][period][-1] - 2*SPTRD_MULTIPLE*self.구간ATR[keyStr][period][-1]) )

        self.표준편차.append(getSigma(self.구간VAL["현재가"], self.구간이평["현재가"][10], 10))
        self.볼밴상단.append(self.구간이평["현재가"][10][-1] + 2*self.표준편차[-1])
        self.볼밴하단.append(self.구간이평["현재가"][10][-1] - 2*self.표준편차[-1])

        #self.순회전율표준편차.append(getSigma(getOCHLCloseList(self.구간OCHL["순회전율"]), self.구간이평["순회전율"][20], 20))
        #self.순회전율볼밴상단.append(self.구간이평["순회전율"][20][-1] + 2*self.순회전율표준편차[-1])
        #self.순회전율볼밴하단.append(self.구간이평["순회전율"][20][-1] - 2*self.순회전율표준편차[-1])

        for key in self.범위체강.keys():
            self.범위체강[key].append( safeDivideRounded(100*getListSum(self.구간DELTA["매수거래량"][1],key, True),
                                                     getListSum(self.구간DELTA["매도거래량"][1],key, True), 0, 0) )

        for key in self.범위체강이평.keys():
            self.범위체강이평[key].append( getMA(self.범위체강[60], key, 100) )

        for key in self.체강이평.keys():
            self.체강이평[key].append( getMA(getOCHLCloseList(self.구간OCHL["체강"]), key, 100) )

        if self.구간OCHL["현재가"][-1].종가>=self.구간OCHL["현재가"][-1].시가:
            self.양봉.append(True)
        else:
            self.양봉.append(False)

        if self.구간DELTA["프로그램회전율"][1][-1] > self.최대구간프로그램회전율:
            self.최대구간프로그램회전율 = self.구간DELTA["프로그램회전율"][1][-1]
        if self.구간DELTA["순회전율"][1][-1] > self.최대구간순회전율:
            self.최대구간순회전율 = self.구간DELTA["순회전율"][1][-1]
        if self.구간DELTA["누적거래대금"][1][-1] > self.최대구간누적거래대금:
            self.최대구간누적거래대금 = self.구간DELTA["누적거래대금"][1][-1]

        # realData의 데이터들 종가에 align
        for key in self.구간OCHL.keys():
            #getattr(mother, f"구간{key}OCHL").syncToClose()
            mother.구간OCHL[key].syncToClose()

        for p in 분봉_거래대금_기준:
            if int(self.구간DELTA['누적거래대금'][1][-1]) >= p:
                setattr( mother, f'거래대금{p}횟수', getattr(mother, f'거래대금{p}횟수')+1 )
        for p in 분봉_순거래대금_기준:
            if int(self.구간DELTA['순대금'][1][-1]) >= p:
                setattr( mother, f'순거래대금{p}횟수', getattr(mother, f'순거래대금{p}횟수')+1 )



        # 기준봉 체크
        #mother.checkReferenceBar()

