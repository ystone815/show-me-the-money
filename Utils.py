import datetime
import time
import math
from PyQt5.QtGui import *
from enum import Enum
from Global import *

# 전역함수
def getTsec(t: str):
    t = str(t)
    if len(t) == 5:
        t = f"0{t}"
    tsec = 3600 * (int(t[0:2]) - 9) + 60 * int(t[2:4]) + int(t[4:6])  # second 형식으로 변환
    return int(tsec)

def getTday(t: str):
    tday = 10000*int(t[0:4]) + 100*int(t[4:6]) + int(t[6:8])
    return int(tday)

def secToTime(tsec: int):
    h = int(tsec/3600) + 9
    m = int((tsec%3600)/60)
    s = int((tsec%60))
    strH, strM, strS = str(h), str(m), str(s)
    if len(strM) == 1:
        strM = f"0{strM}"
    if len(strS) == 1:
        strS = f"0{strS}"

    t = f"{strH}{strM}{strS}"
    return t

def isWeekend():
    days = ['월', '화', '수', '목', '금', '토', '일']
    day = days[datetime.datetime.today().weekday()]
    if day=='토' or day=='일':
        return 1
    else:
        return 0

def getOCHLAverage(ochl):
    return round((ochl.시가+ochl.종가+ochl.고가+ochl.저가)/4,2)

def getOCHLListMA(ochlList, period, firstOCHL):
    ma = getOCHLAverage(firstOCHL)
    if len(ochlList)>0:
        sum = 0
        calPeriod = min(len(ochlList), period)
        for i in range(calPeriod):
            sum += getOCHLAverage(ochlList[-1-i])   # 최근 데이터 기반으로 계산
        if period > calPeriod:
            sum += (period-calPeriod) * getOCHLAverage(firstOCHL)     # 첫데이터 증폭
        ma = sum / period
        return ma

def getTrueRange(ochlList, 전일종가):
    if len(ochlList) <= 1:
        #return max(ochlList[-1].고가-ochlList[-1].저가, ochlList[-1].고가-전일종가, 전일종가-ochlList[-1].저가)
        return ochlList[-1].고가-ochlList[-1].저가
    else:
        return max(ochlList[-1].고가-ochlList[-1].저가, ochlList[-1].고가-ochlList[-2].종가, ochlList[-2].종가-ochlList[-1].저가)
    
def getTrueRangeRate(ochlList):
    if len(ochlList) <= 1:
        #return max(ochlList[-1].고가-ochlList[-1].저가, ochlList[-1].고가-전일종가, 전일종가-ochlList[-1].저가)
        return round(100*(ochlList[-1].고가-ochlList[-1].저가)/ochlList[-1].시가,2)
    else:
        return round( max( 100*(ochlList[-1].고가-ochlList[-1].저가)/ochlList[-2].종가, 
                        100*(ochlList[-1].고가-ochlList[-2].종가)/ochlList[-2].종가, 
                        100*(ochlList[-2].종가-ochlList[-1].저가)/ochlList[-2].종가 ), 2)

def getMA(list, period, firstVal):
    ma = 0
    if len(list)>0:
        sum = 0
        calPeriod = min(len(list), period)
        for i in range(calPeriod):
            sum += list[-1-i]   # 최근 데이터 기반으로 계산
        if period > calPeriod:
            sum += (period-calPeriod) * firstVal     # 첫데이터 증폭
        #ma = sum / calPeriod
        ma = sum / period
    return ma

def getMAList(list, period, firstVal):
    if len(list)==0:
        return [0]
    else:
        inputList = []
        outputList = []
        for element in list:
            inputList.append(element)
            outputList.append(getMA(inputList, period, firstVal))

    return outputList

# 평균가 계산 (거래대금/거래량)
def getAvgPrice(listMoney, listVolume, period, default, moneyUnit=억):
    if len(listMoney)>0 and len(listVolume)>0:
        sum_money, sum_volume = 0, 0
        calPeriod = min(len(listMoney), period)
        for i in range(calPeriod):
            sum_money   += listMoney[-1-i]      # 최근 데이터 기반으로 계산
            sum_volume  += listVolume[-1-i]      
        #if period > calPeriod:
        #    sum_money   += (period-calPeriod) * listMoney[0]     # 첫데이터 증폭
        #    sum_volume  += (period-calPeriod) * listVolume[0]    
        return safeDivideRounded(sum_money*moneyUnit, sum_volume, default, 0)
    else:
        return default

# List 끝에서부터 sum 계산
def getListSum(list, period, accFirst:bool):
    sum = 0
    if len(list)>0:
        calPeriod = min(len(list), period)
        for i in range(calPeriod):
            sum += list[-1-i]
        if period > calPeriod and accFirst is True:
            sum += (period - calPeriod) * list[0]  # 첫데이터 증폭

    return sum

def getMax(list, period):
    if len(list)==0:
        return 0
    else:
        max = list[0]
        calPeriod = min(len(list), period)
        for i in range(calPeriod):
            if max < list[-1-i]:   # 최근 데이터 기반으로 계산
                max = list[-1-i]
        return max

def getMaxIndex(list):
    if len(list)==0:
        return 0
    else:
        max = 0
        index = 0
        for i, val in enumerate(list):
            if max < val:   # 최근 데이터 기반으로 계산
                max = val
                index = i
        return index

def getDictMaxValue(dict):
    maxVal = 0
    if len(dict)>0:
        for key, value in dict.items():
            maxVal = value if maxVal < value else maxVal

    return maxVal

def getDictMaxKey(dict):
    maxKey = 0
    maxValue = 0
    if len(dict)>0:
        for key, value in dict.items():
            if maxValue < value:
                maxKey = key
                maxValue = value

    return maxKey


def getMin(list, period):
    if len(list)==0:
        return 0
    else:
        returnMin = list[0]
        calPeriod = min(len(list), period)
        for i in range(calPeriod):
            if returnMin > list[-1-i]:   # 최근 데이터 기반으로 계산
                returnMin = list[-1-i]
        return returnMin


def getMid(listMax, listMin, period):
    if len(listMax)==0 or len(listMin)==0:
        return 0
    else:
        return (getMax(listMax, period) + getMin(listMin, period))/2

# 등락율 구하기. base값 대비 몇퍼 차이인지 리턴
def getRate(cur, base, round_digit):
    return ( round( 100*cur/base, round_digit ) - 100 )

def getOCHLLowList(list):
    returnList = []
    if len(list)>0:
        for val in list:
            returnList.append(val.저가)

    return returnList

def getOCHLHighList(list):
    returnList = []
    if len(list) > 0:
        for val in list:
            returnList.append(val.고가)

    return returnList

def getOCHLHighLowList(list):
    return getOCHLHighList(list) + getOCHLLowList(list)

def getOCHLCloseList(list):
    returnList = []
    if len(list) > 0:
        for val in list:
            returnList.append(val.종가)

    return returnList


def getOCHLMin(list):
    if len(list)==0:
        return 0
    else:
        for i, val in enumerate(list):
            if i==0:
                min = val.저가
            else:
                min = val.저가 if min>val.저가 else min
        return min

def getOCHLMax(list):
    if len(list)==0:
        return 0
    else:
        for i, val in enumerate(list):
            if i==0:
                max = val.고가
            else:
                max = val.고가 if max<val.고가 else max
        return max



def getSigma(등락율, 이평, period):
    if len(등락율)==0:
        return 0
    else:
        sigmaVal = 0
        calPeriod = min(len(등락율), period)
        for i in range(calPeriod):
            sigmaVal += (등락율[-1-i] - 이평[-1]) ** 2
        #if period>calPeriod:
        #    sigmaVal += ((등락율[0] - 이평[-1]) ** 2)*(period-calPeriod)
        sigmaVal = round(math.sqrt(float(sigmaVal / period)), 2)
        return sigmaVal

def getSigmaList(등락율, 이평, period, zeroBase):
    if len(등락율)==0:
        return [0]
    else:
        inputList = []
        outputList = []
        for element in 등락율:
            inputList.append(element)
            maList = getMAList(inputList, period, zeroBase)
            outputList.append(getSigma(inputList, maList, period))

    return outputList

def getBBHighList(list, period, zeroBase):
    if len(list)==0:
        return [0]
    else:
        maList = getMAList(list, period, zeroBase)
        sigmaList = getSigmaList(list, maList, period, zeroBase)
        BBHighList = []
        for index in range(len(maList)):
            BBHighList.append(round(maList[index]+2*sigmaList[index],2))

    return BBHighList

def getBBLowList(list, period, zeroBase):
    if len(list)==0:
        return [0]
    else:
        maList = getMAList(list, period, zeroBase)
        sigmaList = getSigmaList(list, maList, period, zeroBase)
        BBLowList = []
        for index in range(len(maList)):
            BBLowList.append(round(maList[index]-2*sigmaList[index],2))

    return BBLowList

def getListDelta(list, period):
    if len(list) == 0:
        return 0
    elif len(list) == 1:
        return list[-1]
    elif len(list) <= period:
        return list[-1] - list[0]
    else:
        return list[-1] - list[-1-period]

def getOCHLCloseDelta(list):
    if len(list) > 1:
        return (list[-1].종가-list[-2].종가)
    else:
        return list[-1].종가

def getLowBelowMA(저가, 이평):
    if len(이평)==0:
        return 0
    else:
        returnLow = 저가[-1]
        token = 1
        for i in range(len(이평)):
            if 저가[-1-i] > 이평[-1-i]:
                if token == 0:
                    break
                else:
                    continue
            else:
                if 저가[-1-i] < returnLow:
                    returnLow = 저가[-1-i]
                token = 0
        return returnLow


def getHighAboveMA(고가, 저가, 이평):
    if len(이평)==0:
        return 0
    else:
        returnHigh = 고가[-1]
        for i in range(len(이평)):
            if 고가[-1 - i] > returnHigh:
                returnHigh = 고가[-1 - i]
            if 저가[-1-i] < 이평[-1-i]:
                break

        return returnHigh

def getPrevHighList(고가, 저가, 종가, 이평):
    if len(이평)==0:
        return []
    else:
        returnHighList = []
        returnHigh = -1
        for i in range(len(이평)):
            if 고가[-1-i] > 이평[-1-i]:
                #if 고가[-1 - i] > returnHigh :
                if (고가[-1 - i] > returnHigh):
                    returnHigh = 고가[-1-i]
            else:
                if (저가[-1-i] < 이평[-1-i] or i== len(이평)-1) and returnHigh > 0:
                    if len(returnHighList) == 0:
                        returnHighList.append(returnHigh)
                    else:
                        if returnHigh > max(returnHighList):
                            returnHighList.append(returnHigh)
                    returnHigh = -1
        if len(returnHighList):
            if returnHighList[-1] != 고가[-1]:
                returnHighList.append(고가[-1])
        else:
            returnHighList.append(고가[-1])
            
        return returnHighList

def getBackgroundColor(val, maxVal):
    red = QColor(255, 0, 0)
    blue = QColor(0, 128, 255)
    alpha = min(abs(val) / maxVal, 1.0)

    if val >= 0:
        red.setAlphaF(alpha)
        return red
    else:
        blue.setAlphaF(alpha)
        return blue

def listDivide(list, value, roundPosition):
    if len(list)==0:
        return []
    else:
        returnList = []
        for element in list:
            returnList.append(round(element/value, roundPosition))

        return returnList

def safeDivide(divident, divisor, defaultValue):
    if divisor==0:
        return defaultValue
    else:
        return divident / divisor

def safeDivideRounded(divident, divisor, defaultValue, roundNum):
    if divisor==0:
        return defaultValue
    else:
        return round(divident / divisor, roundNum)


def checkListMin(list, minVal):
    if len(list)==0:
        return False
    else:
        returnValue = False
        for val in list:
            if val>= minVal:
                returnValue = True
        return returnValue

# 박스에서 특정 위치 가격 얻기
def getBoxValue(low, high, pos):
    return ( (high - low) * pos + low )

# 5% 단위 간격 구하기
def getFivePercentList(기준값, 오름차순:bool):
    list = []
    if 오름차순 is True:
        for i in range(-30, 31, 5):
            list.append(int((100+i)*기준값/100))
    else:
        for i in range(30, -31, -5):
            list.append(int((100+i)*기준값/100))
    return list

# 분봉에서 5% 단위로 계산해서 boundary 계산
def getHighBoundary(전일종가, 최대값):
    list = getFivePercentList(전일종가, True)  # 오름차순 (-30->-25->...->30)
    for value in list:
        if value > 전일종가:
            if 최대값 <= value:
                return value
    return 전일종가

def getLowBoundary(전일종가, 최소값):
    list = getFivePercentList(전일종가, False)   # 내림차순 (30->25->...-30)
    for value in list:
        if value < 전일종가:
            if 최소값 >= value:
                return value
    return 전일종가

def fileAppend(fileName, list):
    dataString = ""
    for x in list:
        dataString = f"{dataString}{x},"
    dataString = f"{dataString}\n"

    try:
        with open(fileName, "a") as f:
            f.write(dataString)
            print(f"File Append Complete @ {datetime.datetime.now()} : {fileName} ")
    except Exception as e:
        print(f"File Append error : {e}")

def getChartWidth(periodUnit):
    #return (18*(MINUTE_GRAPH_WIDTH-100)) // (WHOLE_DAY_SEC/periodUnit)
    #return (15*(MINUTE_GRAPH_WIDTH-100)) // (MARKET_CLOSE_SEC/periodUnit)
    if periodUnit == 180:
        return 100
    else:
        return 50
    

def alignAndFloor(val, minVal, align):
    if isinstance(val, list): targetVal = min(val)
    else:                     targetVal = val
    return align * math.floor( min(targetVal, minVal)/align)

def alignAndCeil(val, maxVal, align):
    if isinstance(val, list): targetVal = max(val)
    else:                     targetVal = val

    return align * math.ceil( max(targetVal, maxVal) /align)

def getAlignedMinMax(val, minVal, maxVal, align):
    """
    return aligned min / max
    """
    if isinstance(val, list): inputMaxVal, inputMinVal = max(val), min(val)
    else:                     inputMaxVal, inputMinVal = val, val

    final_min = min(inputMinVal, minVal)
    final_max = max(inputMaxVal, maxVal)

    #if final_min < 0:
    #    if final_min < final_max:
    #        final_min = -final_max
    #    else:
    #        final_max = -final_min

    #ticks = [(val, str(val)) for val in [final_min, math.floor(final_min/2), 0, math.ceil(final_max/2), final_max]]

    return align * math.floor( final_min/align), align*math.ceil( final_max/align )

def getAlignedMinMaxTicks(val, minVal, maxVal, align):
    """
    return aligned min / max
    """
    if isinstance(val, list): inputMaxVal, inputMinVal = max(val), min(val)
    else:                     inputMaxVal, inputMinVal = val, val

    final_min = min(inputMinVal, minVal)
    final_max = max(inputMaxVal, maxVal)

    ticks = [(val, str(val)) for val in [final_min, math.floor(final_min/2), 0, math.ceil(final_max/2), final_max]]

    return align * math.floor( final_min/align), align*math.ceil( final_max/align ), ticks

#def getTicksQuad(minVal, maxVal):
#    return [(val, str(val)) for val in [minVal, math.floor(minVal/2), 0, math.ceil(maxVal/2), maxVal]]

def getTicksQuad(minVal, maxVal):
    return [ (minVal, str(minVal)), (math.floor(minVal/2), ''), (0, '0'), (math.ceil(maxVal/2), ''), (maxVal, str(maxVal)) ]

def getTickSpaces(max_val, min_tick, tick_num):
    space_max = max(math.ceil((max_val/tick_num)/min_tick)*min_tick, 1)
    space_min = max(math.ceil((max_val/(2*tick_num))/min_tick)*min_tick, 1)
    return [space_max, space_min]

# Lower the money by the turnover
def getCalibratedMoney(money, turnover, ceil):
    return money * min( turnover/ceil, 1 )



