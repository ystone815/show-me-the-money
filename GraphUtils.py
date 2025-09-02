from Utils import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import pyqtgraph as pg
from Global import *
from Kiwoom_ystone import OCHL

class LineListItem(pg.GraphicsObject):
    def __init__(self, xMin, xMax, valueList, color, lineWidth, lineStyle):
        pg.GraphicsObject.__init__(self)
        self.picture = QPicture()
        self.Period(xMin, xMax, valueList, color, lineWidth, lineStyle)

    def Period(self, xMin, xMax, valueList, color, lineWidth, lineStyle):
        p = QPainter(self.picture)
        p.setPen(pg.mkPen(color=color, width=lineWidth, style=lineStyle))
        for list in valueList:
            p.drawLine(xMin, list, xMax, list)
        p.end()

    def paint(self, p, *args):
        if args is None:
            return
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QRectF(self.picture.boundingRect())

class PeriodChartItemOCHL(pg.GraphicsObject):
    def __init__(self, x, ochl, width, colorP, colorN, bodyP, bodyN):
        pg.GraphicsObject.__init__(self)
        self.picture = QPicture()
        self.Period(x, ochl, width, colorP, colorN, bodyP, bodyN)

    def Period(self, x, ochl, width, colorP, colorN, bodyP, bodyN):
        p = QPainter(self.picture)
        for i, time in enumerate(x):
            if ochl[i].종가 >= ochl[i].시가:
                p.setPen(pg.mkPen(color=colorP))
                p.setBrush(pg.mkBrush(color=bodyP))
                if ochl[i].시가 != ochl[i].저가:
                    p.drawLine(QPointF(time + width / 2, ochl[i].시가), QPointF(time + width / 2, ochl[i].저가))
                if ochl[i].종가 != ochl[i].고가:
                    p.drawLine(QPointF(time + width / 2, ochl[i].종가), QPointF(time + width / 2, ochl[i].고가))
            else:
                p.setPen(pg.mkPen(color=colorN))
                p.setBrush(pg.mkBrush(color=bodyN))
                if ochl[i].시가 != ochl[i].고가:
                    p.drawLine(QPointF(time + width / 2, ochl[i].시가), QPointF(time + width / 2, ochl[i].고가))
                if ochl[i].종가 != ochl[i].저가:
                    p.drawLine(QPointF(time + width / 2, ochl[i].종가), QPointF(time + width / 2, ochl[i].저가))
            p.drawRect(QRectF(time, ochl[i].시가, width, ochl[i].종가-ochl[i].시가))

        p.end()

    def paint(self, p, *args):
        if args is None:
            return
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QRectF(self.picture.boundingRect())

class PeriodChartItem(pg.GraphicsObject):
    def __init__(self, x, o, c, h, l, width, colorP, colorN, bodyP, bodyN):
        pg.GraphicsObject.__init__(self)
        self.picture = QPicture()
        self.Period(x, o, c, h, l, width, colorP, colorN, bodyP, bodyN)

    def Period(self, x, o, c, h, l, width, colorP, colorN, bodyP, bodyN):
        p = QPainter(self.picture)

        for i, time in enumerate(x):
            if c[i] >= o[i]:
                p.setPen(pg.mkPen(color=colorP))
                p.setBrush(pg.mkBrush(color=bodyP))
                if o[i] != l[i]:
                    p.drawLine(QPointF(time + width / 2, o[i]), QPointF(time + width / 2, l[i]))
                if c[i] != h[i]:
                    p.drawLine(QPointF(time + width / 2, c[i]), QPointF(time + width / 2, h[i]))
            else:
                p.setPen(pg.mkPen(color=colorN))
                p.setBrush(pg.mkBrush(color=bodyN))
                if o[i] != h[i]:
                    p.drawLine(QPointF(time + width / 2, o[i]), QPointF(time + width / 2, h[i]))
                if c[i] != l[i]:
                    p.drawLine(QPointF(time + width / 2, c[i]), QPointF(time + width / 2, l[i]))
            p.drawRect(QRectF(time, o[i], width, c[i]-o[i]))

        p.end()

    def paint(self, p, *args):
        if args is None:
            return
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QRectF(self.picture.boundingRect())

class PeriodUSAChartColorItemOCHL(pg.GraphicsObject):
    def __init__(self, x, ochl, width, color_pos, color_neg):
        pg.GraphicsObject.__init__(self)
        self.picture = QPicture()
        self.Period(x, ochl, width, color_pos, color_neg)

    def Period(self, x, ochl, width, color_pos, color_neg):
        p = QPainter(self.picture)
        for i, time in enumerate(x):
            if ochl[i].종가 >= ochl[i].시가:
                p.setPen(pg.mkPen(color=color_pos))
                p.setBrush(pg.mkBrush(color=color_pos))
            else:
                p.setPen(pg.mkPen(color=color_neg))
                p.setBrush(pg.mkBrush(color=color_neg))
            p.drawLine(QPointF(time, ochl[i].시가), QPointF(time + width / 2, ochl[i].시가))
            p.drawLine(QPointF(time + width/2, ochl[i].종가), QPointF(time + width, ochl[i].종가))
            if ochl[i].고가 != ochl[i].저가:
                p.drawLine(QPointF(time+width/2, ochl[i].고가), QPointF(time+width/2, ochl[i].저가))
        p.end()

    def paint(self, p, *args):
        if args is None:
            return
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QRectF(self.picture.boundingRect())

# opacity는 값이 낮을수록 투명함
class PeriodHighLightItem(pg.GraphicsObject):
    def __init__(self, x:list, flag, width, h, l, _color, opacity):
        pg.GraphicsObject.__init__(self)
        self.picture = QPicture()
        self.Period(x, flag, width, h, l, _color, opacity)

    def Period(self, x, flag, width, h, l, _color, opacity):
        p = QPainter(self.picture)
        for i, time in enumerate(x):
            if flag[i] is True:
                p.setPen(pg.mkPen(color=_color))
                p.setBrush(pg.mkBrush(color=_color))
                p.setOpacity(opacity)   # 0~1.0
                p.drawRect(QRectF(time, l, width, h-l))
        p.end()

    def paint(self, p, *args):
        if args is None:
            return
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QRectF(self.picture.boundingRect())

class PeriodHighLightWithMaxItem(pg.GraphicsObject):
    def __init__(self, x, val, max, width, h, l, color, opacity):
        pg.GraphicsObject.__init__(self)
        self.picture = QPicture()
        self.Period(x, val, max, width, h, l, color, opacity)

    def Period(self, x, val, max, width, h, l, color, opacity):
        p = QPainter(self.picture)
        for i, time in enumerate(x):
            if val[i] <= max:
                p.setPen(pg.mkPen(color=color))
                p.setBrush(pg.mkBrush(color=color))
                p.setOpacity(opacity)   # 0 ~ 1.0
                p.drawRect(QRectF(time, l, width, h-l))
        p.end()

    def paint(self, p, *args):
        if args is None:
            return
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QRectF(self.picture.boundingRect())

class PeriodHighLightWithMinItem(pg.GraphicsObject):
    def __init__(self, x, val, min, width, h, l, color, opacity):
        pg.GraphicsObject.__init__(self)
        self.picture = QPicture()
        self.Period(x, val, min, width, h, l, color, opacity)

    def Period(self, x, val, min, width, h, l, color, opacity):
        p = QPainter(self.picture)
        for i, time in enumerate(x):
            if val[i] >= min:
                p.setPen(pg.mkPen(color=color))
                p.setBrush(pg.mkBrush(color=color))
                p.setOpacity(opacity)   # 0~1.0
                p.drawRect(QRectF(time, l, width, h-l))
        p.end()

    def paint(self, p, *args):
        if args is None:
            return
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QRectF(self.picture.boundingRect())

class PeriodBarItem(pg.GraphicsObject):
    def __init__(self, x, value, width, colorP, bodyP, colorN, bodyN):
        pg.GraphicsObject.__init__(self)
        self.picture = QPicture()
        self.Period(x, value, width, colorP, bodyP, colorN, bodyN)

    def Period(self, x, value, width, colorP, bodyP, colorN, bodyN):
        p = QPainter(self.picture)
        for i, time in enumerate(x):
            if value[i] >= 0:
                p.setPen(pg.mkPen(color=colorP))
                p.setBrush(pg.mkBrush(color=bodyP))
            else:
                p.setPen(pg.mkPen(color=colorN))
                p.setBrush(pg.mkBrush(color=bodyN))
            p.drawRect(QRectF(time, 0, width, value[i]))
        p.end()

    def paint(self, p, *args):
        if args is None:
            return
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QRectF(self.picture.boundingRect())

## 
class ScatterItem(pg.GraphicsObject):
    def __init__(self, x, value, width, colorP, bodyP, colorN, bodyN):
        pg.GraphicsObject.__init__(self)
        self.picture = QPicture()
        self.Period(x, value, width, colorP, bodyP, colorN, bodyN)

    def Period(self, x, value, width, colorP, bodyP, colorN, bodyN):
        p = QPainter(self.picture)
        for i, time in enumerate(x):
            if value[i] >= 0:
                p.setPen(pg.mkPen(color=colorP))
                p.setBrush(pg.mkBrush(color=bodyP))
            else:
                p.setPen(pg.mkPen(color=colorN))
                p.setBrush(pg.mkBrush(color=bodyN))
            p.drawRect(QRectF(time, 0, width, value[i]))
        p.end()

    def paint(self, p, *args):
        if args is None:
            return
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QRectF(self.picture.boundingRect())


# 매물대 그릴때 쓰는 바차트
# Input으로 받는 list는 [가격, percent값]
# 가격순으로 정렬되어 있어야 함
class HorizontalBarItem(pg.GraphicsObject):
    def __init__(self, lists, widthMax, lineColor, bodyColor):
        pg.GraphicsObject.__init__(self)
        self.picture = QPicture()
        self.Period(lists, widthMax, lineColor, bodyColor)

    def Period(self, lists, widthMax, lineColor, bodyColor):
        p = QPainter(self.picture)
        listLen = len(lists)
        for i, list in enumerate(lists):
            if i<listLen-1:
                height = lists[i+1][0] - lists[i][0]
            p.setPen(pg.mkPen(color=lineColor))
            p.setBrush(pg.mkBrush(color=bodyColor))
            p.drawRect(QRectF(0, list[0], int(widthMax*list[1]), int(height)))
        p.end()

    def paint(self, p, *args):
        if args is None:
            return
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QRectF(self.picture.boundingRect())

class PeriodMoneyBarTypeItem(pg.GraphicsObject):
    def __init__(self, x, value, positive, width):
        pg.GraphicsObject.__init__(self)
        self.picture = QPicture()
        self.Period(x, value, positive, width)

    def Period(self, x, value, positive, width):
        p = QPainter(self.picture)
        for i, time in enumerate(x):
            if positive[i] is True:
                p.setPen(pg.mkPen(color=COLOR_RED))
                p.setBrush(pg.mkBrush(color=COLOR_RED))
            else:
                p.setPen(pg.mkPen(color=COLOR_BLUE))
                p.setBrush(pg.mkBrush(color=COLOR_BLUE))
            p.drawRect(QRectF(time, 0, width, value[i]))
        p.end()

    def paint(self, p, *args):
        if args is None:
            return
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QRectF(self.picture.boundingRect())

class PeriodCurveItem(pg.GraphicsObject):
    def __init__(self, x, value, color, lineStyle, width=1):
        pg.GraphicsObject.__init__(self)
        self.picture = QPicture()
        self.Period(x, value, color, lineStyle, width)

    def Period(self, x, value, color, lineStyle, width):
        p = QPainter(self.picture)
        p.setPen(pg.mkPen(color=color, width=width, style=lineStyle))
        for i, time in enumerate(x):
            if i > 0:
                p.drawLine(QPointF(x[i-1], value[i-1]), QPointF(x[i], value[i]) )
        p.end()

    def paint(self, p, *args):
        if args is None:
            return
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QRectF(self.picture.boundingRect())

class PeriodCurveItemWithThreshold(pg.GraphicsObject):
    def __init__(self, x, value, color, lineStyle, threshold, color2):
        pg.GraphicsObject.__init__(self)
        self.picture = QPicture()
        self.Period(x, value, color, lineStyle, threshold, color2)

    def Period(self, x, value, color, lineStyle, threshold, color2):
        p = QPainter(self.picture)
        p.setPen(pg.mkPen(color=color, width=1, style=lineStyle))
        #p.setBrush(pg.mkBrush(fillLevel=threshold, brush=(50,50,200,100)))
        for i, time in enumerate(x):
            #if value[i] > threshold:
                #p.setPen(pg.mkPen(color=color, width=2, style=lineStyle))
            if i > 0:
                p.drawLine(QPointF(x[i-1], value[i-1]), QPointF(x[i], value[i]) )
        p.setPen(pg.mkPen(color=color2, width=3, style=lineStyle))
        for i, time in enumerate(x):
            if value[i] > threshold:
               p.drawLine(QPointF(x[i], threshold), QPointF(x[i], value[i]) )

        p.end()

#p7.plot(y, fillLevel=-0.3, brush=(50,50,200,100))

    def paint(self, p, *args):
        if args is None:
            return
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QRectF(self.picture.boundingRect())

class PeriodCurveOffsetItem(pg.GraphicsObject):
    def __init__(self, x, value, xOffset, color, lineStyle):
        pg.GraphicsObject.__init__(self)
        self.picture = QPicture()
        self.Period(x, value, xOffset, color, lineStyle)

    def Period(self, x, value, xOffset, color, lineStyle):
        p = QPainter(self.picture)
        p.setPen(pg.mkPen(color=color, width=1, style=lineStyle))
        for i, time in enumerate(x):
            if i > 0:
                p.drawLine(QPointF(x[i-1]+xOffset, value[i-1]), QPointF(x[i]+xOffset, value[i]) )
        p.end()

    def paint(self, p, *args):
        if args is None:
            return
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QRectF(self.picture.boundingRect())

class PeriodTextItem(pg.GraphicsObject):
    def __init__(self, x, value, flag, _color, vScale):
        pg.GraphicsObject.__init__(self)
        self.picture = QPicture()
        self.Period(x, value, flag, _color, vScale)

    def Period(self, x, value, flag, _color, vScale):
        p = QPainter(self.picture)
        p.setPen(pg.mkPen(color=_color, width=5))
        for i, time in enumerate(x):
            if flag[i] is True:
                p.drawText(QPointF(x[i], value[i]*vScale), '▼')
                #p.drawPoint(QPointF(x[i], value[i]*vScale))
        p.end()

    def paint(self, p, *args):
        if args is None:
            return
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QRectF(self.picture.boundingRect())

class LegendItem(pg.TextItem):
    def __init__(self, text, color, x, y, size):
        pg.TextItem.__init__(self)
        self.setFont(QFont(text, pointSize=size, weight=-1, italic=False))
        self.setColor(color)
        self.setText(text)
        self.setPos(x, y)
