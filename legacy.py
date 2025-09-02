
# 만들어 놓고 안쓰던 QThread
class MainTimer(QThread):
    def __init__(self, parent:MyWindow):
        super().__init__(parent)
        self.parent = parent
    #self.timerSort = QTimer(self)
    #self.timerSort.start(TIMER_PERIOD)
    #self.timerSort.timeout.connect(self.timeout)
    #self.timerPhase = 0
    #while True:
    #    self.timeout()
    #    time.sleep(3.6)
    def run(self):
        while True:
            self.parent.timeout()
            time.sleep(3.6)
        
