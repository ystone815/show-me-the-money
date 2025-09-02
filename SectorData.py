from Global import *
from BaseClass import *
from Utils import *

# 섹터 클래스
class SectorData:
    def __init__(self, name:str):
        self.name = name
        self.codes = [] # 섹터 종목들 코드
        self.names = [] # 섹터 종목들 이름
        self.numCodes = 0
        self.시가총액 = 0
        self.시각 = []
        self.등락율총합 = [] # 섹터 등락율 총합
        self.등락율 = []   # 등락율총합/종목수
        self.프로그램대금 = []
        self.순대금 = []
        self.업데이트 = []
        self.프로그램회전율 = []
        self.순회전율 = []
        self.latestIndex = 0    # 배열중 최근 데이터 인덱스

        for time in list(range(getTsec(str(MARKET_OPEN_TIME)), getTsec(str(MARKET_CLOSE_TIME+1)), PERIOD_UNIT)):
            iTime = int(secToTime(time))
            self.시각.append(iTime)
            self.등락율.append(0)
            self.등락율총합.append(0)
            self.프로그램대금.append(0)
            self.순대금.append(0)
            self.업데이트.append(False)   # 첫 종목이 업데이트 되면 True로
            self.프로그램회전율.append(0)
            self.순회전율.append(0)

    def appendStock(self, code, name, 시가총액):
        if code not in self.codes:
            self.codes.append(code)
            self.names.append(name)
            self.numCodes += 1
            self.시가총액 += 시가총액

    def updateSectorData(self, 시각, 등락율순증, 프로그램대금순증, 순대금순증):
        index = self.시각.index(시각)
        if self.업데이트[index] is False:
            self.업데이트[index] = True
            if index > 0:
                self.등락율총합[index] = self.등락율총합[index-1] + 등락율순증
                self.프로그램대금[index] = self.프로그램대금[index-1] + 프로그램대금순증
                self.순대금[index] = self.순대금[index-1] + 순대금순증
            else:
                self.등락율총합[index] = 등락율순증
                self.프로그램대금[index] = 프로그램대금순증
                self.순대금[index] = 순대금순증
            self.프로그램회전율[index] = round(safeDivide(100*self.프로그램대금[index],self.시가총액,0),2)
            self.순회전율[index] = round(safeDivide(100 * self.순대금[index], self.시가총액, 0), 2)
        else:
            for i in range(index, len(self.등락율총합)):
                self.등락율총합[i] = self.등락율총합[i] + 등락율순증
                self.프로그램대금[i] = self.프로그램대금[i] + 프로그램대금순증
                self.순대금[i] = self.순대금[i] + 순대금순증
                self.프로그램회전율[i] = round(safeDivide(100 * self.프로그램대금[i], self.시가총액, 0),2)
                self.순회전율[i] = round(safeDivide(100 * self.순대금[i], self.시가총액, 0),2)

        self.등락율[index] = round(safeDivide(self.등락율총합[index], self.numCodes, 0), 2)

        if index > self.latestIndex:
            self.latestIndex = index

