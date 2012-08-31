::chcp 65001 1>nul
::SET PYTHONIOENCODING=utf-8
::SET OUT=%~n0.log
::rm -f %OUT%
::python %~n0.py > %OUT%
::@type %OUT%
::tail -F %OUT%

python %~n0.py