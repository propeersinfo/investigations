:: convert opera articles (html) to my markup

::cls
rm markdown/*
python html2markdown.py
::cat markdown/*