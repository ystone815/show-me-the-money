# 일봉상 스윙치는 매매 상태
class TradeData:
    def __init__(self):
        self.clear()

    def clear(self):
        self.고가240, self.고가120 = 0, 0
#        self.clearRB()

#    def clearRB(self):
#        self.R0, self.R1, self.R2, self.R3, self.RD = 0, 0, 0, 0, 0
#        self.stateRB = STATE_RB_IDLE
        self.lastStandby, self.lastTrade = 0, 0
#        self.RB_평단, self.RB_물량, self.RB_매수일, self.RB_기준일 = 0, 0, "0", "0"

    def update(self, 고가240, 고가120, R0, R1, R2, R3, stateRB, lastStandby, lastTrade, RB_물량, RB_평단, RB_매수일, RB_기준일):
        self.고가240, self.고가120 = 고가240, 고가120
#        self.R0, self.R1, self.R2, self.R3, self.RD = R0, R1, R2, R3, R0-R1
#        self.stateRB = stateRB
        self.lastStandby, self.lastTrade = lastStandby, lastTrade
#        self.RB_평단, self.RB_물량, self.RB_매수일, self.RB_기준일 = RB_평단, RB_물량, RB_매수일, RB_기준일
