@rem curl -d "file1=@test.jpg&method=file&check_thumb=size&uploading=1&orig_rotate=0&thumb_size=200" "http://fastpic.ru/upload?api=1" > test.xml

curl -F "file1=@test.jpg" -F "method=file" -F "check_thumb=size" -F "uploading=1" -F "orig_rotate=0" -F "thumb_size=200" "http://fastpic.ru/upload?api=1"