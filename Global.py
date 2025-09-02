import datetime
import time

# 참고 : symbol types = o, t, t1, t2, t3, s, p, h, star, +, d, x

개장마진 = 0 # 0 or 10000 - 1시간
만 = 10000

SKIP_LOGIN = 0
SINGLE_BUY_MONEY = 100000
INIT_LOAD_DATE = '20210122'
INIT_LOAD_NUM = '30'
INIT_MIN_ACC_MONEY = '10'
INIT_MIN_PURE_MONEY = '5'
TICK_ARRAY_DEPTH = 5  # 단주모니터링을 위한 Array Depth
DATA_FULL_SIZE = 100  # 데이터가 계속 추가되다 크기가 DATA_FULL_SIZE되면 자동 저장을 실시한다.
MIN_DANJU_NUM = 50  # 최소단주 체결량
MIN_DANJU_MONEY = 100*만
MIN_DANJU_INTERVAL = 30  # 최소단주 간격(초)
MIN_DANJU_FILTER = 2    # N개이상만 단주로 체크
NUM_TABLE = 1  # Table 개수 (조건식)
NUM_TABLE_ROW = 2000
WIDTH_TABLE_ROW = 12
NUM_TOP_LIST = 500
NUM_GRAPH = 6
NUM_DAYGRAPH = 2
#NUM_SECTORGRAPH = 1
NUM_PRINT_DAYGRAPH = 180    # 일봉 출력 개수
NUM_LOAD_DATE = 240     # 일봉데이터 얻어올때 일자 개수
NUM_CHECKBOX = 4
FONT_SIZE_MINUTE_GRAPH = 8
고가눌림목_개수 = 10  # 고가대비 눌림목
TABLE_UPDATE_PERIOD = 10  # 10초마다 table 업데이트 (데몬이 아니고, 틱 받을때 판단)
일분 = 60
PERIOD_UNIT = 180  # 주기적 정보 저장 단위. 초
WHOLE_DAY_SEC = 25200
MARKET_CLOSE_SEC = 23800
전동거_보정상수 = WHOLE_DAY_SEC / PERIOD_UNIT     # 6.5시간 / PERIOD_UNIT
WHOLE_DAY_PERIOD_NUM = round(WHOLE_DAY_SEC / PERIOD_UNIT)
DAYCHART_WIDTH = 0.5
CHART_WIDTH_MARGIN = 0.6
MAIN_TABLE_WIDTH = 600
MINUTE_GRAPH_WIDTH = 1300
TODAY = datetime.datetime.now().strftime("%Y%m%d")  # 실시간 데이터는 날짜 정보가 없음, 날짜 정보 추가용
DIR_NAME = './../키움데이터/당일데이터'
LOAD_DIR_NAME = './../키움데이터/복기데이터'
REAL_DATA_PATH = f"{LOAD_DIR_NAME}/{TODAY}"
DAY_DIR_NAME = './../키움데이터/일봉데이터'
STOCK_COUNT_PATH = './../키움데이터/유통주식수'
조건식_파일 = './조건식.csv'
TRAIN_DIR_NAME = 'Train_Datas'
USER_COND_FILE = 'USER_CONFIG.txt'
CODE_LIST_FILE = 'CODE_LIST.txt'
TRADE_DATA_FILE = "./TRADE_DATA.txt"
SECTOR_FILE = "섹터.txt"
TYPE_FILE = "종목타입.csv"
PROFILE_FILE = 'profile.txt'
PROFILE_EN = 0
종목타입_기본 = '잡주'
시각_동시호가 = 153000 + 개장마진
MARKET_OPEN_TIME = 90000 + 개장마진
MARKET_SELL_TIME = 151500  + 개장마진
MARKET_PRECLOSE_TIME = 152100 + 개장마진
MARKET_SECTOR_CLOSE_TIME = 시각_동시호가
MARKET_CLOSE_TIME = 153900  + 개장마진 # 마감 동시호가 고려하여 39분
데이터정리_시각 = 152500 + 개장마진
일봉로드_시각 = 154500 + 개장마진
CURRENT_TIME = f"{time.localtime().tm_hour}{time.localtime().tm_min}{time.localtime().tm_sec}"
GRAPH_YAXIS_WIDTH = 40
장악력_계산시작 = 90000 + 개장마진
만원 = 10000
억 = 만원 * 만원
백만원 = 100*만원
큰돈기준 = 5000*만원

파바박조건 = [   {'개수':1, '대금':2*억, '파워':0.02},
                {'개수':5, '대금':0.5*억, '파워':0.02},
                {'개수':1, '대금':100*만원, '파워':0.1}
                ]
#파바박개수 = 1
#파바박대금 = 3000*만원
#파바박파워 = 0.05

일초기준 = [[5000*만원, 0.2], [10*억, 0.1]]

큰호가기준 = 3*억

기준봉_거래대금 = 500  # 억
세력봉_거래대금 = 500  # 억
상한가_거래대금 = 100  # 억
주도주_거래대금 = 1000 # 억
주도주_등락율 = 5 # %
주도주_회전율 = 10


악재갭하락 = 0.92 # 갭하락판단기준
시가총액_대형주 = 40000
시가총액_중형주 = 10000
시가총액_소형주 = 4000
회전율_대형주 = 5
상한가_기준 = 29.5
형님대금_기준 = 0.1 # 매도호가합대비10%

TIMER_PERIOD = 3600 # ms 단위
TIMER_PERIOD_SEC = 3.6 # ms 단위

강한놈조건 = {'거래대금':100, '고가등락율':0.10, '종가등락율':0.10, '기간':10}
분봉_거래대금_기준 = [30,50]
분봉_순거래대금_기준 = [5,10]

COLOR_RED = (255, 0, 0)
COLOR_RED_ALPHA100 = (255, 0, 0, 100)
COLOR_RED_ALPHA150 = (255, 0, 0, 150)
COLOR_RED_ALPHA200 = (255, 0, 0, 200)
COLOR_BROWN = (128, 64, 64)
COLOR_BROWN_ALPHA100 = (128, 64, 64, 100)
COLOR_BLUE = (0, 0, 255)
COLOR_BLUE_ALPHA100 = (0, 0, 255, 100)
COLOR_BLUE_ALPHA150 = (0, 0, 255, 150)
COLOR_BLUE_ALPHA200 = (0, 0, 255, 200)
COLOR_BLACK = (0, 0, 0)
COLOR_BLACK_ALPHA100 = (0, 0, 0, 100)
COLOR_BLACK_ALPHA150 = (0, 0, 0, 150)
COLOR_BLACK_ALPHA200 = (0, 0, 0, 200)
COLOR_DARK_GREEN = (0, 128, 0)
COLOR_DARK_GREEN_ALPHA100 = (0, 128, 0, 100)
COLOR_PURPLE = (128, 0, 255)
COLOR_PURPLE_ALPHA100 = (128, 0, 255, 100)
COLOR_IVORY = (255,255,245)    # 아이보리
COLOR_YELLOW = (255, 255, 0)
COLOR_YELLOW_ALPHA100 = (255, 255, 0, 100)
COLOR_TRANS = (0,0,0,0)
COLOR_GRAY = (192,192,192)
LEGEND_OFFSET = (0, 0)
WIDTH_EDIT_BOX = 70
WIDTH_TABLE_EDIT_BOX = 40
MINUTE_CHART_MARGIN = 0.09
MINUTE_GRAPH_MARGIN = 0.01
TOP_LIST_KEY = ['거래량증가 상위', '누적거래대금 상위', '순대금 상위',
                '순장악력 상위', '프로그램장악력 상위',
                '회전율 상위', '순회전율 상위', '프로그램회전율 상위']

CHECK_BOX_KEY = ['이평선', '볼밴', '박스권', '고점대비', '고점후저점', '평균가', '파바박', 'SuperTrend']
CHECK_BOX_KEY_SUB = [ 
                     '누적거래대금', '구간거래대금', '구간거래량증가', 
                     '순대금', '매수매도대금', 
                     '파바박대금', '구간파바박개수', '매수매도파바박개수',
                     '순매수율', '순매수율누적', '구간회전율', '순회전율', 
                     '구간평균가등락율',
                     '순장악력', '매수매도파워', '순매수파워', '구간순매수파워', '순형님대금', '호가대금',
                     '가격변동율', '순대금변동', '순거래량박스권', '가격박스권'
                     ]
LABEL_EDIT_KEY = ['분봉초', '랜덤복기개수', '복기날짜', '종목명']
LABEL_EDIT_INIT = [str(PERIOD_UNIT), str(INIT_LOAD_NUM), str(INIT_LOAD_DATE), '']
TABLE_LABEL_EDIT_KEY = ['최소대금', '최소거래증가율', '최소분봉대금', '일고가갱신', '최소P장악력',
                        '최소시가총액', '최소순회전율', '구간순회전율', '구간P회전율']

##### Periodic Data에서, 구간OCHL저장할 키들
##### RealData의 변수 이름과 맞아야 함 
구간OCHL_KEYS = ["매도호가합", "매수호가합", "매도호가비율", 
               "순대금", "순회전율", "순큰돈대금", "순큰돈횟수", "순장악력",
               "현재가", "체강", "매수파워", "매도파워", "순매수파워", '파바박대금', '순형님대금',
               "키움증권", '매도호가합', '매수호가합', '매도호가대금', '매수호가대금', '현재가',
               "가격박스권","순거래량박스권",
               ]

평균가_KEYS = [1,2,3,5,10]

# 구간 OCHL 내에 KEY가 있어야 함. 
구간변동_KEYS = ["현재가", '순대금']
구간변동율_KEYS = ["현재가"]

##### 구간OCHL에 Key가 있어야 함 #####
구간복합이평_KEYS = [ ["순대금", [1,5,10]], ["파바박대금", [10]], ['순형님대금',[10]], ['현재가', [10]] ]

# 구간변동 / 구간복합이평에 KEY가 있어야 함
구간ATR_KEYS = [ ['현재가', [10]] ]

# 구간변동 / 구간복합이평에 KEY가 있어야 함
구간SPTRD_KEYS = [ ['현재가', [10]] ]
SPTRD_MULTIPLE = 1

##### 구간별로 종가만 저장할 것들 #####
구간VAL_KEYS = ["시각", "현재가","등락율","누적거래량","누적거래대금","순대금","순거래량","순큰돈대금",'파바박대금','파바박개수',
              "순회전율","순큰돈횟수",
              "거래량증가",'순거래량증가',"회전율","프로그램회전율","당일고가","당일저가","순프로그램", '당일고가',
              "매수거래량","매도거래량","매수대금", "매도대금", "매수평균가", "매도평균가",
              '평균가볼밴상단', '평균가볼밴하단', '매수파바박개수', '매도파바박개수',
              "가격박스권","순거래량박스권","매도호가합","매수호가합","순회전율갱신","프로그램갱신",
              "체강", "프로그램장악력", "순장악력", "매수파워", "매도파워", "순매수파워", '순형님대금',
              '박스750', '박스625', '박스500', '박스375', '박스250', '고점후저점', 
              ] + [f'평균가{p}' for p in 평균가_KEYS] + [f'평균가등락율{p}' for p in 평균가_KEYS]

##### 구간VAL에 Key가 있어야 함 #####
구간DELTA_KEYS = [ ["회전율",[1]], ["순회전율",[1]], ["프로그램회전율",[1]],["순거래량",[1]], ["순대금",[1]], ["회전율",[1]],
                 ["순큰돈횟수",[1]], ["누적거래대금",[1]], ["매수거래량",[1]], ["매도거래량",[1]], ['파바박대금', [1]],
                 ["순장악력", [1]], ["매수파워", [1]], ["매도파워", [1]], ["순매수파워", [1]], ["파바박개수", [1]], ["매도파바박개수", [1]], ["매수파바박개수", [1]], 
                 ['순형님대금',[1]], ["매수대금", [1]], ["매도대금", [1]], ["매수대금", [1]], ['거래량증가',[1]], ['순거래량증가',[1]], ['순매수율',[1]], 
                 ] + [[f'평균가등락율{p}', [1]] for p in 평균가_KEYS]

구간DELTA_ACC_KEYS = [['순매수율', [10]],]

##### 구간DELTA에 Key가 있어야 함 (Key, 기준값) #####
구간강조_KEYS = [ ["순회전율",[1]], ['회전율',[1]], ['프로그램회전율',[0.1]], ['순매수파워',[1]], ['누적거래대금',[30]], 
                    ['순대금',[10]], ['파바박대금',[10]], ['순형님대금', [5]], 
                    ['순장악력',[1]], ['파바박개수',[50]], 
                    ['거래량증가',[50]], ['순거래량증가',[10]], ['평균가등락율2',[0.5]] ]

##### 구간VAL에 Key가 있어야 함 #####
# [ ["KEY", [10, 20, ...]], ... ]
구간이평_KEYS = [["현재가", [10, 20, 60]], ["순대금", [10,20]], ["순회전율",[10]], 
                 ["순큰돈횟수", [10, 20]], ["순장악력", [10]], ["순매수파워", [10]],
                ["파바박대금", [10]], ['순형님대금', [10]] ]



#기준봉_KEYS = [ "순회전율", "순대금", "누적거래대금" ]
#기준봉_체크주기 = 180
#조건식_KEYS = ["누적거래대금", "거래량증가", "순회전율", "순대금", "프로그램장악력"]
#조건식_시각들 = [93000, 100000, 103000, 110000, 120000, 130000, 140000, 150000, 154000]
#조건식_체크주기 = 60 # 30초



#buy_list = []
#sell_list = []

#load_data_list = []
MAX_LOAD_DATA = 50

전체섹터_이름 = '전체'