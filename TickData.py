from Global import *
from BaseClass import *
from Utils import *
from collections import deque

# deque 형식의 TickData class - 단주 계산에 사용
class TickData:
    def __init__(self):
        self.tickArray = deque([], maxlen=TICK_ARRAY_DEPTH)
        self.priceArray = deque([], maxlen=TICK_ARRAY_DEPTH)
        self.danjuTime = []
        self.danjuPrice = []

    def append(self, 체결시간, 가격):
        self.tickArray.append(체결시간)
        self.priceArray.append(가격)

        # 단주 판단
        result = False
        #if len(self.tickArray) >= 4:    # 4개 비교 (3개 훼이크는 패스)
        if len(self.tickArray) >= 3:
            interval12 = self.tickArray[-1] - self.tickArray[-2]
            interval23 = self.tickArray[-2] - self.tickArray[-3]
            #interval34 = self.tickArray[-3] - self.tickArray[-4]

            #minInterval = min(interval12, interval23, interval34)
            minInterval = min(interval12, interval23)
            #if interval12 >= MIN_DANJU_INTERVAL and interval23 >= MIN_DANJU_INTERVAL and interval34 >= MIN_DANJU_INTERVAL:
            if interval12 >= MIN_DANJU_INTERVAL and interval23 >= MIN_DANJU_INTERVAL:
                # 간격이 같을 경우 / 2배까지는 허용
                if (abs(interval12 - minInterval) <= 1 or abs(interval12 - 2*minInterval) <= 1) and \
                        (abs(interval23 - minInterval) <= 1 or abs(interval23 - 2*minInterval) <= 1) :
                        #(abs(interval34 - minInterval) <= 1 or abs(interval34 - 2*minInterval) <= 1):

                    result = True

        # danjuTime 리스트에 추가
        if result is True:
            if len(self.danjuTime) == 0:  # 아무 데이터도 없는 경우, 앞의 두개도 추가
                #self.danjuTime.append(self.tickArray[-4])
                self.danjuTime.append(self.tickArray[-3])
                self.danjuTime.append(self.tickArray[-2])
                self.danjuTime.append(self.tickArray[-1])
                self.danjuPrice.append(self.priceArray[-3])
                self.danjuPrice.append(self.priceArray[-2])
                self.danjuPrice.append(self.priceArray[-1])
            else:
                # danjuTime 리스트에서 마지막 두개와 비교하여, 불일치시 추가
                #if self.tickArray[-4] != self.danjuTime[-3] and self.tickArray[-4] != self.danjuTime[-2] and self.tickArray[-4] != self.danjuTime[-1]:
                #    self.danjuTime.append(self.tickArray[-3])
                if self.tickArray[-3] != self.danjuTime[-3] and self.tickArray[-3] != self.danjuTime[-2] and self.tickArray[-3] != self.danjuTime[-1]:
                    self.danjuTime.append(self.tickArray[-3])
                    self.danjuPrice.append(self.priceArray[-3])
                if self.tickArray[-2] != self.danjuTime[-3] and self.tickArray[-2] != self.danjuTime[-2] and self.tickArray[-2] != self.danjuTime[-1]:
                    self.danjuTime.append(self.tickArray[-2])
                    self.danjuPrice.append(self.priceArray[-2])
                self.danjuTime.append(self.tickArray[-1])
                self.danjuPrice.append(self.priceArray[-1])
        #return result
