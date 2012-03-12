@echo off

cls
rm -f bulkloader-*

call:handle_kind Article
call:handle_kind ArticleTag
call:handle_kind Comment
call:handle_kind Slug

echo.&goto:eof

:: handle one DB kind
:handle_kind
rm -f %1.dat
C:\Python26\python.exe -u C:\Python\gae\appcfg.py download_data --url=http://localhost/_ah/remote_api --kind=%1 --email=zeencd@gmail.com --filename=%1.dat
goto:eof