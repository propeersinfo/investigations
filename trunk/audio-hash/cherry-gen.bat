SET PYTHONIOENCODING=utf-8
rm -rf static_site/*
python cherry.py static
cp -R themes/static static_site