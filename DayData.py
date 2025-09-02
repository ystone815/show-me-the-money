from Global import *
from BaseClass import *
from Utils import *

# 일봉데이터
class DayData:
    def __init__(self, mother):
        self.clear()
        self.mother = mother

    def clear(self):
        self.clearBase()

    def clearBase(self):
        self.날짜, self.거래대금, self.시가, self.고가, self.저가, self.종가, self.양봉 = [], [], [], [], [], [], []
        self.거래량, self.평균가 = [], []
        self.시가등락율, self.고가등락율, self.저가등락율, self.종가등락율 = [], [], [], []
        self.이평 = {5:[], 10:[], 20:[], 60:[], 120:[]}
        self.평균가이평 = {p:[] for p in 평균가_KEYS}
        self.신고가 = {5:[], 20:[], 60:[], 120:[], 240:[]}
        self.신고가갱신 = {5: [], 20: [], 60: [], 120: [], 240: []}
        self.세력대금, self.회전율 = [], []

        self.세력봉, self.주도주 = [], []
        self.상한가, self.단일가 = [], []
        self.최고대금 = {120:[], 240:[]}
        self.최고대금갱신 = {120:[], 240:[]}
        self.이평5저가, self.이평5고가, self.이평20저가, self.이평20중가, self.이평20고가 = [], [], [], [], []
        self.박스5, self.박스20 = [], []

        self.저항대 = []

    def append(self, 날짜, 거래량, 거래대금, 시가, 고가, 저가, 종가, 주식수):
        if len(self.날짜) > 0:
            if 종가 >= self.종가[-1] * (상한가_기준/100+1):
                self.상한가.append(True)
            else:
                self.상한가.append(False)
        else:
            self.상한가.append(False)

        if len(self.날짜) > 0:
            self.시가등락율.append(round(시가/self.종가[-1]-1, 2))
            self.고가등락율.append(round(고가/self.종가[-1]-1, 2))
            self.저가등락율.append(round(저가/self.종가[-1]-1, 2))
            self.종가등락율.append(round(종가/self.종가[-1]-1, 2))
        else:
            self.시가등락율.append(0)
            self.고가등락율.append(0)
            self.저가등락율.append(0)
            self.종가등락율.append(0)

        if self.종가==self.시가 and self.종가==self.고가 and self.종가==self.저가:
            self.단일가.append(True)
        else:
            self.단일가.append(False)

        for key in self.신고가갱신.keys():
            if len(self.신고가[key]) > 0:
                if 종가 > self.신고가[key][-1]:   self.신고가갱신[key].append(True)
                else:                           self.신고가갱신[key].append(False)
            else:
                self.신고가갱신[key].append(False)

        for key in self.최고대금갱신.keys():
            if len(self.최고대금[key]) > 0:
                if 거래대금 > self.최고대금[key][-1]:  self.최고대금갱신[key].append(True)
                else:                               self.최고대금갱신[key].append(False)
            else:
                self.최고대금갱신[key].append(False)

        if 주식수 > 0:
            self.회전율.append( round(100*(거래대금*억/((시가+고가+저가+종가)/4)) / 주식수, 2) )
        else:
            self.회전율.append(0)

        if len(self.날짜) > 0:
            # 원래 세력봉
            #if 거래대금 > 세력봉_거래대금 and self.종가[-1] * 1.15 <= 고가 and 저가 * 1.15 <= 고가 and 시가 * 1.09 <= 종가:
            #if (거래대금 > 세력봉_거래대금 and  self.종가[-1] * 1.10 <= 종가 and self.종가[-1] * 1.15 <= 고가 and 종가 > 시가 and self.신고가갱신[5][-1]):
            #if (거래대금>=100 and  self.종가[-1]*1.29<=종가 and 종가 > 시가) or \
            #    (거래대금>=500 and  self.종가[-1]*1.20<=종가 and 종가 > 시가) or \
            #    (거래대금>=1000 and  self.종가[-1]*1.15<=종가 and 종가 > 시가) or \
            #    (거래대금>=2000 and  self.종가[-1]*1.10<=종가 and 종가 > 시가) \
#                            and self.신고가갱신[5][-1]:
            if (거래대금>=500 and  self.종가[-1]*1.15<=종가 and 종가>시가 and self.거래대금[-1]*3<=거래대금 and round(거래대금/self.mother.시가총액,2))>=0.5:
                self.세력봉.append(True)
            else:
                self.세력봉.append(False)
        else:
            self.세력봉.append(False)

        if len(self.날짜) > 0:
            if (거래대금>=주도주_거래대금 and self.종가[-1]*(1+주도주_등락율/100)<=종가 and 종가>시가 and self.회전율[-1]>=주도주_회전율):
                self.주도주.append(True)
            else:
                self.주도주.append(False)
        else:
            self.주도주.append(False)


        self.날짜.append(날짜)
        self.시가.append(시가)
        self.고가.append(고가)
        self.저가.append(저가)
        self.종가.append(종가)
        self.거래량.append(거래량)
        self.거래대금.append(거래대금)        
        self.평균가.append( safeDivideRounded(거래대금*억, 거래량, 종가, 0) )

        if 종가>=시가:      self.양봉.append(True)
        else:              self.양봉.append(False)

        if self.양봉[-1] is True:        순대금 = 거래대금
        else:                           순대금 = -거래대금

        if len(self.세력대금) == 0:      self.세력대금.append(순대금)
        else:                           self.세력대금.append(순대금+self.세력대금[-1])

        # 이평계산
        for key in self.이평.keys():
            self.이평[key].append(getMA(self.종가, key, self.종가[0]))

        for key in self.신고가.keys():
            self.신고가[key].append(getMax(self.고가, key))

        for key in self.최고대금.keys():
            self.최고대금[key].append(getMax(self.거래대금, key))

        for key in self.평균가이평.keys():
            self.평균가이평[key].append( getAvgPrice(self.거래대금, self.거래량, key, default=종가, moneyUnit=억) )

        self.이평5저가.append(getLowBelowMA(self.저가, self.이평[5]))
        self.이평5고가.append(getHighAboveMA(self.고가, self.저가, self.이평[5]))
        self.이평20저가.append(getLowBelowMA(self.저가, self.이평[20]))
        self.이평20고가.append(getHighAboveMA(self.고가, self.저가, self.이평[20]))
        self.이평20중가.append(round((self.이평20저가[-1]+self.이평20고가[-1])/2,0))
        self.박스5.append(round(safeDivide(self.이평5고가[-1], self.이평5저가[-1], 1) - 1, 1))
        self.박스20.append(round(safeDivide(self.이평20고가[-1], self.이평20저가[-1], 1)-1, 1))

        # 저항대 계산
        self.저항대_계산()

    def 저항대_계산(self):
        #self.저항대.append(getPrevHighList(self.고가, self.저가, self.종가, self.이평[10]))
        self.저항대.append(getPrevHighList(self.고가, self.저가, self.종가, self.이평[20]))

