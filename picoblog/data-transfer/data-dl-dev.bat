@echo off

cls
rm -f bulkloader-*
rm -f *.dat

call:handle_kind Article
call:handle_kind ArticleTag
call:handle_kind Comment
call:handle_kind Slug

echo.&goto:eof

:: handle one DB kind
:handle_kind
rm -f %1.dat
echo "anypassword" | C:\Python26\python.exe -u C:\Python\gae\appcfg.py download_data --url=http://localhost/_ah/remote_api --kind=%1 --email=anyemail --filename=%1.dat --passin --bandwidth_limit=100000000
goto:eof