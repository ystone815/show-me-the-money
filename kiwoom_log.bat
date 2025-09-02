set root=C:\ProgramData\anaconda3
call %root%\Scripts\activate.bat %root% 
REM call conda env list 
call conda activate py38_32
call cd c:/PySrc/Kiwoom
call python Kiwoom_ystone.py > log_%DATE%_%time:~0,2%_%time:~3,2%_%time:~6,2%.txt
pause

