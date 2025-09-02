import threading
import os

from Global import *
from BaseClass import *
from Utils import *
from PeriodicData import *
from TradeData import *
from TickData import *
from FastData import *
from DayData import *
#from OneSecData import *

# 실시간 데이터 저장용 클래스
class RealData:
    # 생성자
    def __init__(self, code: str, name: str, mother):
        # 종목코드, 종목명, 시장타입 설정
        self.code = code
        self.name = name

        # self.tableRow = tableRow
        self.mother = mother
        self.fileName = f"{TODAY}_{self.name}.csv"
        self.dirFileName = f"{REAL_DATA_PATH}\\{self.fileName}"
        self.effectiveStockCountFileName = f"{STOCK_COUNT_PATH}\\{self.name}.txt"
        self.dayDatas = DayData(self);  # 일봉 데이터
        self.tradeData = TradeData();   # 일봉 매매 데이터

        self.periodUnit = PERIOD_UNIT

        self.chartWidth = getChartWidth(self.periodUnit)
        self.주식수, self.유통주식수, self.시가총액 = 1, 0, 100
        self.유통비율, self.유통시가총액 = 100, 100
        self.종목타입, self.섹터문자열 = 종목타입_기본, ""

        self.clear()

    def clear(self):
        self.tick_count = 0
        self.bHogaStart = False
        self.tableUpdateTime = 0

        self.periodicData = PeriodicData()
        self.fastData = FastData()                  # 파바박
        #self.oneSecData = OneSecData()                  # 파바박
        self.periodicUpdateTime = MARKET_OPEN_TIME

        self.섹터 = []

        # '주식체결' 데이터 저장용
        self.체결시간, self.현재가, self.등락율, self.거래량 = 0, 0, 0, 0
        self.현재가Pre, self.장후동시호가티켓 = 0, 1
        self.누적거래량, self.누적거래대금, self.시가, self.고가, self.저가, self.전일종가 = 0, 0, 0, 0, 0, 0
        for p in 평균가_KEYS:
            setattr(self, f'평균가{p}', 0)
            setattr(self, f'평균가등락율{p}', 0)    # 평균가를 전일종가대비 %로 나타냄 (평균가/전일종가)
        self.보정대금 = 0       # 회전율 고려하여 곱한값
        self.시가등락율, self.고가등락율, self.저가등락율 = 0, 0, 0
        self.순큰돈거래량, self.순큰돈대금, self.순큰돈횟수 = 0, 0, 0
        self.큰돈데이터 = {"PlusTime":[], "PlusPrice":[], "PlusMoney":[], "MinusTime":[], "MinusPrice":[], "MinusMoney":[]}
        self.형님데이터 = {"PlusTime":[], "PlusPrice":[], "PlusMoney":[], "MinusTime":[], "MinusPrice":[], "MinusMoney":[]}
        self.순형님대금 = 0

        self.순매수횟수, self.매수횟수, self.매도횟수 = 0, 0, 0
        self.거래량증가, self.순거래량, self.순대금, self.순장악력, self.파바박대금, self.파바박개수, self.일초대금 = 0, 0, 0, 0, 0, 0, 0
        self.매수파바박개수, self.매도파바박개수 = 0, 0
        self.순거래량증가 = 0
        self.매수거래량, self.매도거래량, self.매수대금, self.매도대금 = 0, 0, 0, 0
        self.단주개수, self.단주총합 = 0, 0
        self.회전율, self.순회전율, self.단주회전율, self.프로그램회전율 = 0, 0, 0, 0
        self.최대프로그램장악력 = 0
        self.최대프로그램, self.최소프로그램, self.프로그램갱신 = 0, 0, False
        self.최대순거래량, self.최소순거래량 = 0, 0
        self.최대순회전율, self.순회전율갱신 = 0, False
        self.당일고가, self.당일저가, self.고점후저점 = 0, 0, 0
        self.박스750, self.박스625, self.박스500, self.박스375, self.박스250 = 0,0,0,0,0
        self.가격박스권, self.순거래량박스권 = 0, 0
        self.순프로그램, self.순프로그램대금 = 0, 0
        self.프로그램장악력 = 0
        self.체강 = 100
        self.복기모드, self.복기날짜, self.복기보정값 = False, "", 0
        self.일봉로드 = False
        self.장시작 = False  

        for p in 분봉_거래대금_기준:
            setattr(self, f'거래대금{p}횟수', 0)
        for p in 분봉_순거래대금_기준:
            setattr(self, f'순거래대금{p}횟수', 0)

        # 단일조건
        self.저항대돌파 = 0
        self.신고가돌파240 = 0
        self.전일고점돌파 = 0

        self.매도호가합, self.매수호가합, self.매도호가비율 = 1, 1, 1
        self.매도호가변동, self.매수호가변동 = 0, 0
        self.매도호가수량1, self.매수호가수량1, self.매도호가변동1, self.매수호가변동1 = 0, 0, 0, 0
        self.매도호가대금, self.매수호가대금 = 0, 0
        self.근접매도호가수량, self.근접매수호가수량 = 0, 0
        self.근접매도호가비율, self.근접매수호가비율 = 0, 0
        self.매수파워, self.매도파워, self.순매수파워 = 0, 0, 0
        self.첫봉거래대금 = -1
        self.키움증권 = 0

        self.구간OCHL = {}
        for key in 구간OCHL_KEYS:
            self.구간OCHL[key] = OCHL(0)

        self.dataString = "체결시간,현재가,등락율,거래량," \
                          ", \n"

        self.체결배열 = {}  # 단주 계산용 Dict
        #self.매물대 = {}   # {가격, 체결량}

        # 조건식과 비교할 딕셔너리 {키, {시각:값, ...}}
        self.조건식_시각포인터 = 0
        self.조건식_체크시각 = 90000
        self.조건식_만족시각 = {}       # {조건식명, 시각}

        self.기준봉_체크시각 = 90000
        self.기준봉_만족시각 = {}   # {조건식명, 시각}
        #self.기준봉_값들 = {}       
        self.단일조건_만족시각 = {} # {조건식명, 시각}

        for day in [1,2,3,4,5,10]:
            setattr(self, f"세력봉최근{day}", -1)
            setattr(self, f"상한가최근{day}", -1)
            setattr(self, f"주도주최근{day}", -1)

        #for 체크값 in 기준봉_KEYS:
        #    self.기준봉_값들[체크값] = 0

    def updateStockCount(self, nCount):
        if nCount>0:
            self.주식수 = nCount

    def updateMarketCap(self, nLastVal):
        self.시가총액 = int(self.주식수*nLastVal / 억)

    def 거래원추가(self, 매도거래원:list, 매도거래원수량:list, 매도거래원증감:list, 매수거래원:list, 매수거래원수량:list, 매수거래원증감:list):
        if self.복기모드 is False:
            self.dataString += f"거,"
            for i in range(5):
                self.dataString += f"{매도거래원[i]},{매도거래원수량[i]},{매도거래원증감[i]},"
            for i in range(5):
                self.dataString += f"{매수거래원[i]},{매수거래원수량[i]},{매수거래원증감[i]},"
            self.dataString += f" \n"
        if '키움증권' in 매도거래원:
            self.키움증권 -= 매도거래원증감[매도거래원.index('키움증권')]
        if '키움증권' in 매수거래원:
            self.키움증권 += 매수거래원증감[매수거래원.index('키움증권')]

    # 실시간 데이터를 추가하는 함수
    def append(self, 체결시간: int, 현재가: int, 등락율: float, 거래량: int):
        if 체결시간 > MARKET_SECTOR_CLOSE_TIME and self.장후동시호가티켓:
            self.updatePeriodicData(체결시간)
            self.장후동시호가티켓 = 0

        if 체결시간 < MARKET_OPEN_TIME:
            return
        if 거래량 == 0: 
            return

        self.tick_count += 1
        거래대금 = 거래량 * 현재가 / 억

        if self.장시작 is False and 체결시간 >= MARKET_OPEN_TIME:
            if self.전일종가 == 0:
                if len(self.dayDatas.종가) > 0:
                    self.전일종가 = self.dayDatas.종가[-1-self.복기보정값]
                else:
                    self.전일종가 = int(현재가*100/(100+self.등락율))    # 역산

        if self.장시작 is False and 체결시간 >= MARKET_OPEN_TIME:
            self.시가, self.고가, self.저가, self.장시작 = 현재가, 현재가, 현재가, True
            self.시가등락율 = 등락율
            self.고가등락율 = 등락율
            self.저가등락율 = 등락율
            #print(f"시가등락율 = {self.시가등락율}")
        else:
            if 현재가 > self.고가:     
                self.고가, self.고가등락율 = 현재가, 등락율
            if 현재가 < self.저가:     
                self.저가, self.저가등락율 = 현재가, 등락율

            매수횟수 = 1 if 거래량 > 0 else 0
            매도횟수 = -1 if 거래량 < 0 else 0
            순매수횟수 = 1 if 거래량 > 0 else (0 if 거래량 == 0 else -1)

            #if self.매수호가합>1 and self.매도호가합>1: 파워 = safeDivideRounded( 거래량, self.매도호가합+self.매수호가합, 0, 5 )
            #else:                                     파워 = 0
            if self.매수호가대금>1 or self.매도호가대금>1: 파워 = safeDivideRounded( 거래대금, self.매도호가대금+self.매수호가대금, 0, 5 )
            else:                                         파워 = 0

            if 체결시간 < 시각_동시호가:
                if 등락율 < 상한가_기준:
                    self.fastData.updateTick(체결시간, 거래량, 현재가, 파워)
                    #self.oneSecData.updateTick(체결시간, 거래량, 현재가, 파워)
                    self.파바박대금 = self.fastData.result['PlusMoneyAcc']+self.fastData.result['MinusMoneyAcc']
                    self.파바박개수 = self.fastData.result['PlusCountAcc']+self.fastData.result['MinusCountAcc']
                    self.매수파바박개수 = self.fastData.result['PlusCountAcc']
                    self.매도파바박개수 = abs(self.fastData.result['MinusCountAcc'])
                    #self.일초대금 = self.oneSecData.result['PlusMoneyAcc']+self.oneSecData.result['MinusMoneyAcc']
                    self.순거래량 += 거래량

                if 거래량 > 0:
                    self.매수거래량 += 거래량
                    self.매수대금 += 거래대금
                else:
                    self.매도거래량 += abs(거래량)
                    self.매도대금 += abs(거래대금)

                if 등락율 < 상한가_기준:
                    self.순대금 += 거래대금

                    if abs(거래량 * 현재가) >= 큰돈기준:
                        self.순큰돈거래량 += 거래량
                        self.순큰돈대금 += 거래대금
                        #self.큰돈매수횟수 += 매수횟수
                        #self.큰돈매도횟수 += 매도횟수
                        self.순큰돈횟수 += 순매수횟수
                        #if 거래량 > 0:
                        #    self.큰돈데이터["PlusTime"].append(체결시간)
                        #    self.큰돈데이터["PlusPrice"].append(현재가)
                        #    self.큰돈데이터["PlusMoney"].append(abs(거래대금))
                        #else:
                        #    self.큰돈데이터["MinusTime"].append(체결시간)
                        #    self.큰돈데이터["MinusPrice"].append(현재가)
                        #    self.큰돈데이터["MinusMoney"].append(거래대금)

                    self.순매수횟수 += 순매수횟수
                    self.매수횟수 += 매수횟수
                    self.매도횟수 += 매도횟수                    

                #if self.매수호가합>1 and self.매도호가합>1:
                if self.매수호가대금>1 or self.매도호가대금>1:
                    #파워 = safeDivideRounded( 거래량, self.매도호가합+self.매수호가합, 0, 5 )
                    파워 = safeDivideRounded( 거래대금, self.매도호가대금+self.매수호가대금, 0, 5 )
                    #매수파워 = safeDivideRounded( 거래량, self.매도호가합, 0, 5 )
                    #매도파워 = safeDivideRounded( 거래량, self.매수호가합, 0, 5 )
                    if 거래량 > 0:
                        self.매수파워 += 파워
                    else:
                        self.매도파워 += abs(파워)
                    self.순매수파워 += 파워

                    if abs(파워) >= 형님대금_기준:
                        #if 거래량 > 0:
                        #    self.형님데이터["PlusTime"].append(체결시간)
                        #    self.형님데이터["PlusPrice"].append(현재가)
                        #    self.형님데이터["PlusMoney"].append(abs(거래대금))
                        #else:
                        #    self.형님데이터["MinusTime"].append(체결시간)
                        #    self.형님데이터["MinusPrice"].append(현재가)
                        #    self.형님데이터["MinusMoney"].append(거래대금)                            
                        self.순형님대금 += 거래대금

                #호가대비거래량 = safeDivideRounded(abs(거래량), (self.매도호가합+self.매수호가합), 0, 5)

                #if 호가대비거래량 > 형님대금_기준:
                #    self.형님대금 += 거래대금
                    #self.순매수파워 = self.매수파워 + self.매도파워

        # 단일조건 변수
        if self.저항대돌파 == 0:
            if len(self.dayDatas.저항대) > self.복기보정값:
                for 저항대 in self.dayDatas.저항대[-1-self.복기보정값]:
                    if 현재가 >= 저항대:
                        self.저항대돌파 = 1
        if self.신고가돌파240 == 0:
            if len(self.dayDatas.신고가[240]) > self.복기보정값:
                if 현재가 >= self.dayDatas.신고가[240][-1-self.복기보정값]:
                    self.신고가돌파240 = 1
        if self.전일고점돌파 == 0:
            if len(self.dayDatas.고가) > self.복기보정값:
                if 현재가 >= self.dayDatas.고가[-1-self.복기보정값]:
                    self.전일고점돌파 = 1
        
        for day in [1,2,3,4,5,10]:
            # 세력봉 최근 계산
            if getattr(self, f"세력봉최근{day}") == -1:  # 첫 계산
                temp_flag = 0
                for i in range(min(day, len(self.dayDatas.세력봉))-1):
                    if self.dayDatas.세력봉[-1-i-self.복기보정값]:
                        temp_flag = 1
                        break
                setattr(self, f"세력봉최근{day}", temp_flag)

            # 상한가 최근 계산                
            if getattr(self, f"상한가최근{day}") == -1:  # 첫 계산
                temp_flag = 0
                for i in range(min(day, len(self.dayDatas.상한가))-1):
                    if self.dayDatas.상한가[-1-i-self.복기보정값]:
                        temp_flag = 1
                        break
                setattr(self, f"상한가최근{day}", temp_flag)
            
            # 주도주 최근 계산                
            if getattr(self, f"주도주최근{day}") == -1:  # 첫 계산
                temp_flag = 0
                for i in range(min(day, len(self.dayDatas.주도주))-1):
                    if self.dayDatas.주도주[-1-i-self.복기보정값]:
                        temp_flag = 1
                        break
                setattr(self, f"주도주최근{day}", temp_flag)

        self.체결시간 = 체결시간
        self.현재가Pre = self.현재가
        self.현재가, self.등락율, self.거래량 = 현재가, 등락율, 거래량

        self.체강 = safeDivideRounded(100*self.매수거래량, self.매도거래량, 100, 0)

        self.누적거래량 += abs(거래량)
        self.누적거래대금 += abs(거래대금)

        if self.누적거래대금 > 0 and 체결시간 > 장악력_계산시작:
            self.순장악력 = round(safeDivide(100 * self.순대금, self.누적거래대금, 0), 1)

        for p in 평균가_KEYS:
            setattr(self, f'평균가{p}', getAvgPrice(self.dayDatas.거래대금[:-1-self.복기보정값]+[self.누적거래대금], self.dayDatas.거래량[:-1-self.복기보정값]+[self.누적거래량], p, self.시가, 억))
            #setattr( self, f'평균가등락율{p}', round( 100*getattr(self, f'평균가{p}')/(self.전일종가 if self.전일종가!=0 else self.시가),2)-100 )
            setattr( self, f'평균가등락율{p}', getRate( getattr(self, f'평균가{p}'), (self.전일종가 if self.전일종가!=0 else self.시가) ,2 ) )

        #if self.유통주식수 > 0:
        #    self.회전율 = round(safeDivide(100*self.누적거래량, self.유통주식수, 0),2)
        #elif self.주식수>0:
        if self.주식수>0:
            self.회전율 = round(safeDivide(100*self.누적거래량, self.주식수, 0), 2)
        else:
            self.회전율 = 1

        #if self.유통주식수>0:
        #    self.순회전율 = round(safeDivide(100 * self.순거래량, self.유통주식수, 0), 2)
        #elif self.주식수>0:
        if self.주식수>0:
            self.순회전율 = round(safeDivide(100 * self.순거래량, self.주식수, 0), 2)
        else:
            self.순회전율 = 1

        if len(self.dayDatas.거래대금) > 0:
            self.거래량증가 = int(safeDivide(100*self.누적거래대금, self.dayDatas.거래대금[-1-self.복기보정값], 1))
            self.순거래량증가 = int(safeDivide(100*self.순대금, self.dayDatas.거래대금[-1-self.복기보정값], 1))
        else:
            self.거래량증가 = 0
            self.순거래량증가 = 0

        if self.순프로그램 > self.최대프로그램:
            self.최대프로그램 = self.순프로그램
            self.프로그램갱신 = True
        if self.순프로그램 < self.최소프로그램:     self.최소프로그램 = self.순프로그램
        if self.순거래량 > self.최대순거래량:      self.최대순거래량 = self.순거래량
        if self.순거래량 < self.최소순거래량:      self.최소순거래량 = self.순거래량

        if self.당일고가 == 0:
            self.당일고가 = max([현재가, self.전일종가])
            self.고점후저점 = max([현재가, self.전일종가])
        else:
            if self.당일고가 < 현재가:
                self.당일고가 = 현재가
                self.고점후저점 = 현재가
        if self.당일저가 == 0:
            self.당일저가 = min([현재가, self.전일종가])
        else:
            if self.당일저가 > 현재가:
                self.당일저가 = 현재가

        if self.고점후저점 > 현재가:
            self.고점후저점 = 현재가

        for key in [250, 375, 500, 625, 750]:
            setattr( self, f'박스{key}', getBoxValue(self.당일저가, self.당일고가, round(key/1000,3)) )

        if self.복기모드 is False:
            self.dataString = f"{self.dataString}{체결시간},{현재가},{등락율},{거래량}, \n"

            if self.tick_count >= DATA_FULL_SIZE:
                self._saveData(True)
                self.tick_count = 0
            elif 체결시간 >= 153000:
                try:
                    self.mother.save_data_list.append(self.code)
                except Exception as e:
                    print(f"*E Append Data List Fail : {e}")

        # 단주배열 처리
        #if abs(거래량) >= MIN_DANJU_NUM and abs(거래량) % 100 != 0:
        #if (abs(거래량)*현재가 >= MIN_DANJU_MONEY or abs(거래량)>=MIN_DANJU_NUM)and abs(거래량) % 100 != 0:
        #    if 거래량 not in self.체결배열:
        #        self.체결배열[거래량] = TickData()
        #    #result = self.체결배열[거래량].append(체결시간)
        #    self.체결배열[거래량].append(체결시간, 현재가)
        #    #if result is True:
        
        #if 거래량 > 0:
        #    if 현재가 not in self.매물대:
        #        self.매물대[현재가] = abs(거래량)
        #    else:
        #        self.매물대[현재가] += abs(거래량)

        for key in self.구간OCHL.keys():
            #if key=='파바박대금': self.구간OCHL[key].update()
            #else:                self.구간OCHL[key].update(getattr(self, key))
            self.구간OCHL[key].update(getattr(self, key))

        # 박스권 위치 계산 - 등락율 / 순대금
        self.순거래량박스권 = round(safeDivide(100 * (self.순거래량 - self.최소순거래량), self.최대순거래량 - self.최소순거래량, 0), 2)
        self.가격박스권 = round(safeDivide(100 * (현재가 - self.당일저가), self.당일고가 - self.당일저가, 0), 2)

        if self.순회전율 > self.최대순회전율:
            self.최대순회전율 = self.순회전율
            self.순회전율갱신 = True

        #int(secToTime(getTsec(self.periodicUpdateTime) + self.periodUnit))

        #if self.복기모드 is False:
            #self.tradeRB(현재가, 체결시간)

        # Periodic 데이터 업데이트
        self.updatePeriodicData(체결시간)

        # 장마감 동시호가
        #if 체결시간 > MARKET_PRECLOSE_TIME and 체결시간 < MARKET_CLOSE_TIME:
        #    self.updatePeriodicData(체결시간)

    def updateProgram(self, 체결시간, 순프로그램: int):
        if 체결시간 < MARKET_OPEN_TIME or 체결시간 >= MARKET_CLOSE_TIME:
            return
        #프로그램변화량 = 순프로그램 - self.순프로그램        
        self.순프로그램 = int(순프로그램)
        #self.순프로그램대금 += round(프로그램변화량*self.현재가/억, 2)

        #if 체결시간 >= 장악력_계산시작:
        #    self.프로그램장악력 = round(safeDivide(100*self.순프로그램, self.누적거래량, 0), 2)

        #if self.프로그램장악력 > self.최대프로그램장악력:
        #    self.최대프로그램장악력 = self.프로그램장악력

        ##if self.유통주식수 > 0: self.프로그램회전율 = round(safeDivide(100 * self.순프로그램, self.유통주식수, 0), 2)
        #self.프로그램회전율 = round(safeDivide(100 * self.순프로그램, self.주식수, 0), 2)            
        
        if self.복기모드 is False:
            self.dataString += f"프,{체결시간},{순프로그램}, \n" 

    def updateHoga(self, 호가시간, 매도호가합, 매수호가합, 매도호가수량1, 매수호가수량1, 매도호가대금=0, 매수호가대금=0):
        if self.장시작 is False:
            return

        if self.복기모드 is False:
            if 매도호가합 != self.매도호가합 or 매수호가합 != self.매수호가합:      # 똑같은 데이터가 계속 올 때가 있음(ex.동시호가)
                self.dataString += f"호,{호가시간}," \
                                f"{매도호가합},{매수호가합},{매도호가수량1},{매수호가수량1},{매도호가대금},{매수호가대금}, " \
                                f" \n"
                            #f"{매도호가},{매도변화량},{매수호가},{매수변화량}, \n"
            #self.tick_count += 1

        if 매도호가합: self.매도호가합 = 매도호가합
        if 매수호가합: self.매수호가합 = 매수호가합
        if 매도호가수량1: self.매도호가수량1 = 매도호가수량1
        if 매수호가수량1: self.매수호가수량1 = 매수호가수량1

        self.매도호가대금 = round(매도호가대금/억,2)
        self.매수호가대금 = round(매수호가대금/억,2)

        #    if self.tick_count >= DATA_FULL_SIZE or 호가시간 >= 153000:
        #        self._saveData(True)
        #        self.tick_count = 0

        if 매도호가합 !=0 and 매수호가합 != 0:
            self.매도호가비율 = round(safeDivide(매도호가합, 매수호가합, 1), 2)

    def updateDanjuInfo(self, 체결시간):
        self.단주개수 = self.getDanjuNum()
        self.단주총합 = self.getDanjuSum()

        if self.유통주식수 > 0:
            self.단주회전율 = round(safeDivide(100 * self.단주총합, self.유통주식수, 0), 2)
        elif self.주식수 > 0:
            self.단주회전율 = round(safeDivide(100 * self.단주총합, self.주식수, 0), 2)
        else:
            self.단주회전율 = 0

        #if 체결시간 >= 장악력_계산시작:
        #    self.단주장악력 = round(safeDivide(100 * self.단주총합, self.누적거래량, 0), 2)

    # Periodic 데이터 업데이트
    def updatePeriodicData(self, 체결시간):
        if 체결시간 - self.periodicUpdateTime >= self.periodUnit or 체결시간 >= 시각_동시호가:
            self.updateDanjuInfo(체결시간)

            self.periodicData.append(self)

            #if len(self.섹터) > 0:
                #등락율순증 = getListDelta(self.periodicData.구간VAL["등락율"], 1)
               # 프로그램대금순증 = getListDelta(self.periodicData.구간VAL["순프로그램대금"], 1)
               # 순대금순증 = getListDelta(self.periodicData.구간VAL["순대금"], 1)

                #for 섹터 in self.섹터:
                    #self.mother.sectors[섹터].updateSectorData(self.periodicUpdateTime, 등락율순증, 프로그램대금순증, 순대금순증)    # 섹터 업데이트

            self.periodicUpdateTime = int(secToTime(getTsec(self.periodicUpdateTime) + self.periodUnit))
            self.순회전율갱신, self.프로그램갱신 = False, False            

            if self.첫봉거래대금 == -1:
                self.첫봉거래대금 = self.누적거래대금

            if 체결시간 < 시각_동시호가:
                # 조건식 체크
                for cond_name, cond in self.mother.조건식.items():
                    if cond_name not in self.조건식_만족시각.keys():
                        # 기준봉부터 체크
                        if cond_name not in self.기준봉_만족시각.keys():
                            기준봉_만족 = 1
                            if "기준봉" in cond.keys():
                                for sub_key, sub_value in cond["기준봉"].items():
                                    if self.periodicData.구간DELTA[sub_key][1][-1] < sub_value:
                                        기준봉_만족 = 0
                                        break
                            if 기준봉_만족:
                                self.기준봉_만족시각[cond_name] = 체결시간     # {조건식명, 시각}

                        if cond_name in self.기준봉_만족시각.keys():
                            조건식_만족 = 1
                            for key, value in cond.items():
                                if key=="기준봉":
                                    pass
                                elif key=="종목타입":
                                    if getattr(self, key) != value:
                                        조건식_만족 = 0
                                        break
                                else:
                                    if getattr(self, key) < value:
                                        조건식_만족 = 0
                                        break

                            if 조건식_만족:
                                self.mother.조건식_만족_종목들[cond_name].append([self.code, self.name, 체결시간])
                                self.조건식_만족시각[cond_name] = 체결시간     # {조건식명, 시각}

                        #cond_true = 1
                        #for key, value in cond.items():
                        #    if key=="기준봉":
                        #        for sub_key, sub_value in value.items():

                            #else:                        
                        #    if cond_true == 0:
                        #        break           
                        #if cond_true:
                        #    self.mother.조건식_만족_종목들[cond_name].append([self.code, self.name, 체결시간])
                        #    self.조건식_만족시각[cond_name] = 체결시간     # {조건식명, 시각}
                        
            if 체결시간 - self.periodicUpdateTime >= self.periodUnit:       # 재귀함수 (거래량 적은 주식들)
                self.updatePeriodicData(체결시간)

    # 종목의 단주개수 리턴
    def getDanjuNum(self):
        danjuNum = 0
        if len(self.체결배열) > 0:
            for key, value in self.체결배열.items():
                if len(value.danjuTime) > MIN_DANJU_FILTER :  # 훼이크 제외
                    danjuNum += len(value.danjuTime)
        return danjuNum
#
    def getDanjuPlusNum(self):
        danjuNum = 0
        if len(self.체결배열) > 0:
            for key, value in self.체결배열.items():
                if len(value.danjuTime) > MIN_DANJU_FILTER and key > 0:  # 훼이크 제외
                    danjuNum += len(value.danjuTime)
        return danjuNum
#
    def getDanjuPureNum(self):
        danjuNum = 0
        if len(self.체결배열) > 0:
            for key, value in self.체결배열.items():
                if len(value.danjuTime) > MIN_DANJU_FILTER :  # 훼이크 제외
                    if key > 0:
                        danjuNum += len(value.danjuTime)
                    else:
                        danjuNum -= len(value.danjuTime)
        return danjuNum
#
    ## 종목의 단주총합 리턴
    def getDanjuSum(self):
        danjuSum = 0
        if len(self.체결배열) > 0:
            for key, value in self.체결배열.items():
                if len(value.danjuTime) > MIN_DANJU_FILTER:    # 훼이크 제외
                    danjuSum += len(value.danjuTime) * key
        return danjuSum

    # Threading
    def saveData(self, saveEn: bool):
        t = threading.Thread(target=self._saveData, args=(saveEn,))
        t.start()

    # 현재 저장된 데이터를 저장한다.
    def _saveData(self, saveEn: bool) -> None:
        if not os.path.isdir(REAL_DATA_PATH):
            os.mkdir(REAL_DATA_PATH)

        try:
            with open(self.dirFileName, "a") as f:
                f.write(self.dataString)
        except Exception as e:
            print(f"File writting error : {e}")
        self.dataString = ''

    def saveEffectiveStockCount(self):
        if not os.path.isdir(STOCK_COUNT_PATH):
            os.mkdir(STOCK_COUNT_PATH)
        try:
            with open(self.effectiveStockCountFileName, "w") as f:
                f.write(f"{self.유통주식수}")
        except Exception as e:
            print(f"유통주식수 로드 에러({self.effectiveStockCountFileName}) : {e}")

    def appendSector(self, 섹터):
        if 섹터 not in self.섹터:
            self.섹터.append(섹터)
            if 섹터!=전체섹터_이름:
                self.섹터문자열 = f"{self.섹터문자열}|{섹터}"

    #def getVolumeProfile(self):
#        profileList = []    # [가격, percent]의 리스트
#
#        maxVal = getDictMaxValue(self.매물대)
#
#        if len(self.매물대) > 0:
#            for key, value in self.매물대.items():
#                profileList.append([key, safeDivideRounded(value, maxVal, 0, 2)])
#
#        # 가격순으로 정렬
#        profileList.sort(key=lambda x: x[0], reverse=False)
#
#        return profileList
#
    #def getMaxVolumeProfilePrice(self):
#        return getDictMaxKey(self.매물대)

