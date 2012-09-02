SET PYTHONIOENCODING=utf-8

:: clean
attrib -r "static_site\*" /S /D
rm -rf static_site/*

:: generate
python cherry.py static

:: copy stuff
cp -R themes\static static_site
attrib -r "static_site\*" /S /D
rm -rf static_site\static\.svn
rm -rf static_site\static\fonts\.svn