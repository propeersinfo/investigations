import sys

def copy_text(text):
    if sys.platform == 'win32':
        import win32clipboard
        text = str(text) # TODO: it does not work with 2.6 unicode strings
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_TEXT, text)
        win32clipboard.CloseClipboard()
    else:
        raise Exception('no clipboard interaction implemented under platform %s' % sys.platform)