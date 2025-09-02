'''
sFidList = '20;10;12;15;21;121;125;'

for i in range(5):
    sFidList += f"{141+i};"     # 매도거래원 - 141~145
for i in range(5):
    sFidList += f"{161+i};"     # 매도거래원수량 - 161~165
for i in range(5):
    sFidList += f"{151+i};"     # 매수거래원 - 151~155
for i in range(5):    
    sFidList += f"{171+i};"     # 매도거래원수량 - 171~175

print(sFidList)
'''

import datetime

try:
    with open('test_file.txt', "w") as f:
        f.write('test')
        print(f" File writting complete @ {datetime.datetime.now().strftime('%y%m%d_%H%M%S')}")
except Exception as e:
    print(f"File writting error : {e}")