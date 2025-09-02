from Global import *
from BaseClass import *
from Utils import *

# 파바박 모니터링
class FastData:
    def __init__(self):
        self.lastTick = {"Time":0, "Value":0, "Price":0}
        self.accTick = {"Count":0, "Money":0, 'Power':0}
        self.result = {"PlusTime":[], "PlusCount":[], "PlusMoney":[], "PlusPrice":[], 'PlusMoneyAcc':0, 'PlusCountAcc':0,
                        "MinusTime":[], "MinusCount":[], "MinusMoney":[], "MinusPrice":[], 'MinusMoneyAcc':0, 'MinusCountAcc':0 }

    def updateTick(self, time, value, price, power):
        if (self.lastTick["Value"] > 0 and value > 0) or (self.lastTick["Value"] < 0 and value < 0):
            valuePolarityMatch = True
        else:
            valuePolarityMatch = False

        # 연속 체결
        if time==self.lastTick["Time"] and valuePolarityMatch is True:
            if value > 0: self.accTick["Count"] += 1
            else:         self.accTick["Count"] -= 1
            self.accTick["Money"] += value*price
            self.accTick['Power'] += power
            #self.lastTick["Time"] = time
            self.lastTick["Value"] = value
            self.lastTick["Price"] = price

        # 비연속 체결
        else:
            flag = False
            for cond in 파바박조건:
                if abs(self.accTick["Count"])>=cond['개수'] and abs(self.accTick["Money"])>=cond['대금'] and abs(self.accTick['Power'])>=cond['파워']:
                    flag = True
                    break
            #if(abs(self.accTick["Count"]) >= 파바박개수 and abs(self.accTick["Money"]) >= 파바박대금 and abs(self.accTick['Power'])>= 파바박파워 ):
            if flag==True:
                if self.lastTick["Value"] > 0:
                    #self.result["PlusTime"].append(self.lastTick["Time"])
                    #self.result["PlusCount"].append(self.accTick["Count"])
                    #self.result["PlusMoney"].append(round(self.accTick["Money"]/억, 2))
                    #self.result["PlusPrice"].append(self.lastTick["Price"])
                    self.result["PlusMoneyAcc"] += round(self.accTick["Money"]/억, 2)
                    self.result["PlusCountAcc"] += self.accTick['Count']
                else:
                    #self.result["MinusTime"].append(self.lastTick["Time"])
                    #self.result["MinusCount"].append(self.accTick["Count"])
                    #self.result["MinusMoney"].append(round(self.accTick["Money"]/억, 2))
                    #self.result["MinusPrice"].append(self.lastTick["Price"])
                    self.result['MinusMoneyAcc'] += round(self.accTick["Money"]/억, 2)
                    self.result["MinusCountAcc"] += self.accTick['Count']

            self.lastTick = {"Time":time, "Value":value, "Price":price}

            if value > 0: self.accTick["Count"] = 1
            else:         self.accTick["Count"] = -1
            self.accTick["Money"] = value*price
            self.accTick['Power'] = power

