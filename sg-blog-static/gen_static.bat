rm -f html\*
rm -f html\special\*
rm -f html\tag\*

SET PYTHONPATH=%PYTHONPATH%;C:\Python\gae
SET PYTHONPATH=%PYTHONPATH%;C:\Python\gae\lib\webob_1_1_1
SET PYTHONPATH=%PYTHONPATH%;C:\Python\gae\lib\django_0_96
SET PYTHONPATH=%PYTHONPATH%;C:\Python\gae\lib\simplejson

python gen_static.py

:: review result
browser.bat "http://localhost/"
