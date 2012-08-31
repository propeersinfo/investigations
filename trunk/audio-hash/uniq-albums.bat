::@chcp 65001 1>nul
::@SET PYTHONIOENCODING=utf-8
::@SET OUT=%~n0.list
::@rm -f %OUT%
::python %~n0.py %1 %2 %3 %4 %5 %6 %7 %8 %9 > %OUT%
::@type %OUT%

python %~n0.py