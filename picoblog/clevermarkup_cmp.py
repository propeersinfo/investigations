import datetime
import clevermarkup_new as new
import clevermarkup as old

piece = '''
hello there hello there hello there hello there hello there hello there hello there hello there hello there
[hi.jpg]
hello there hello there hello there hello there hello there hello there hello there hello there hello there
[some homme.mp3]
hello there hello there hello there hello there hello there hello there hello there hello there hello there
'''

html = piece * 10000

funcs = [new, old, ]
for func in funcs + funcs + funcs:
    t1 = datetime.datetime.now()
    func.markup2html_paragraph(html)
    delta = datetime.datetime.now() - t1
    print ('%s: %d:%03d' % (func.__name__, delta.seconds, delta.microseconds/1000))
