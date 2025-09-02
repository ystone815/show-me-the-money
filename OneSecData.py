from Global import *
from BaseClass import *
from Utils import *

# 파바박 모니터링
class OneSecData:
    def __init__(self):
        self.lastTickTime = 0
        self.tickDataPlus  = {"Price":0, 'Money':0, 'Power':0}
        self.tickDataMinus = {"Price":0, 'Money':0, 'Power':0}
        self.result = {"PlusTime":[], "PlusMoney":[], "PlusPrice":[], 'PlusMoneyAcc':0,
                        "MinusTime":[], "MinusMoney":[], "MinusPrice":[], 'MinusMoneyAcc':0 }

    def updateTick(self, time, value, price, power):
        if self.lastTickTime == time: 
            if value > 0:
                self.tickDataPlus['Price'] = price
                self.tickDataPlus['Money'] += value*price
                self.tickDataPlus['Power'] += power
            else:
                self.tickDataMinus['Price'] = price
                self.tickDataMinus['Money'] += value*price
                self.tickDataMinus['Power'] += power
        else:         
            flag = False
            for cond in 일초기준:
                if abs(self.tickDataPlus['Money'])>=cond[0] and abs(self.tickDataPlus['Power'])>=cond[1]:
                    flag = True
                    break
            if flag:
                self.result["PlusTime"].append(self.lastTickTime)
                self.result["PlusMoney"].append(round(self.tickDataPlus["Money"]/억, 2))
                self.result["PlusPrice"].append(self.tickDataPlus['Price'])
                self.result["PlusMoneyAcc"] += round(self.tickDataPlus["Money"]/억, 2)

            flag = False     
            for cond in 일초기준:
                if abs(self.tickDataMinus['Money'])>=cond[0] and abs(self.tickDataMinus['Power'])>=cond[1]:
                    flag = 1
                    break
            if flag:
                self.result["MinusTime"].append(self.lastTickTime)
                self.result["MinusMoney"].append(round(self.tickDataMinus["Money"]/억, 2))
                self.result["MinusPrice"].append(self.tickDataMinus["Price"])
                self.result['MinusMoneyAcc'] += round(self.tickDataMinus["Money"]/억, 2)

            self.lastTickTime = time

            if value > 0:
                self.tickDataPlus['Price'] = price
                self.tickDataPlus['Money'] = value*price
                self.tickDataMinus['Price'] = 0
                self.tickDataMinus['Money'] = 0
            else:
                self.tickDataPlus['Price'] = 0
                self.tickDataPlus['Money'] = 0
                self.tickDataMinus['Price'] = price
                self.tickDataMinus['Money'] = value*price