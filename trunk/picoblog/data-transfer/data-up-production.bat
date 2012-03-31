::C:\Python26\python.exe -u C:\Python\gae\appcfg.py upload_data --url=http://www.sovietgroove.com/_ah/remote_api %KINDS% --email=zeencd@gmail.com --filename=out.dat ..

@echo off

cls

call:handle_kind Article
call:handle_kind ArticleTag
call:handle_kind Comment
call:handle_kind Slug

echo.&goto:eof

:: handle one DB kind
:handle_kind
C:\Python26\python.exe C:\Python\gae\appcfg.py upload_data --num_threads=1 --url=http://www.sovietgroove.com/_ah/remote_api --kind=%1 --email=zeencd@gmail.com --filename=%1.dat ..
goto:eof