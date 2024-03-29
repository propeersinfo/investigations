# -*- coding: utf-8 -*-
# -*- test-case-name: pytils.test.test_translit -*-
# License: GNU GPL2
# Author: Pythy <the.pythy@gmail.com>
"""
Simple transliteration
"""
import sys

__id__ = __revision__ = "$Id: translit.py 32 2006-10-28 07:10:43Z the.pythy $"
__url__ = "$URL: https://pythy.googlecode.com/svn/trunk/pytils/pytils/translit.py $"

import re

def my_detrans(s):
    if len(s) > 0:
        if s.endswith('y'):
            s = u'%sий' % s[0:-1]
        s = s.replace('kh', u'х')
        s = s.replace('ya', u'я')
        s = s.replace('iy', u'ий')
    return detranslify(s)

def get_value_by_name(variable_name, depth=1):
    """
    Return value of variable by it's name

    @param variable_name: name of variable
    @type variable_name: C{str}

    @param depth: stack depth
    @type depth: C{int}

    @raise RuntimeError: when unable to fetch variable
    """
    try:
        variable_value = sys._getframe(depth).f_locals[variable_name]
    except KeyError:
        raise RuntimeError("Unable to fetch variable %s (depth %d)" %\
                           (variable_name, depth))
    return variable_value

def check_type(variable_name, typ):
    """
    Checks type of variable

    @param variable_name: name of variable
    @type variable_name: C{str}

    @param typ: type checking for
    @type typ: C{type} or C{tuple} of types

    @return: None when check successful

    @raise TypeError: check failed
    """
    variable_value = get_value_by_name(variable_name, 2)
    if not isinstance(variable_value, typ):
        raise TypeError("%s must be %s, not %s" % \
                        (variable_name, str(typ), type(variable_value)))

TRANSTABLE = (
        (u"‘", u"'"),
	(u"’", u"'"),
	(u"«", u'"'),
	(u"»", u'"'),
	(u"–", u"-"),
	(u"…", u"..."),
        (u"№", u"#"),
        ## верхний регистр
        # трехбуквенные замены
        (u"Щ", u"Sch"),
        # при замене русский->английский будет первая замена,
        # т.е. Sch
        # а вот если английский->русский, то вариант SCH и Sch --
        # оба пройдут
        (u"Щ", u"SCH"), 
        # двухбуквенные замены
        (u"Ё", u"Yo"),
        (u"Ё", u"YO"),
        (u"Ж", u"Zh"),
        (u"Ж", u"ZH"),
        (u"Ц", u"Ts"),
        (u"Ц", u"TS"),
        (u"Ч", u"Ch"),
        (u"Ч", u"CH"),
        (u"Ш", u"Sh"),
        (u"Ш", u"SH"),
        (u"Ы", u"Yi"),
        (u"Ы", u"YI"),
        (u"Ю", u"Yu"),
        (u"Ю", u"YU"),
        (u"Я", u"Ya"),
        (u"Я", u"YA"),
        # однобуквенные замены
        (u"А", u"A"),
        (u"Б", u"B"),
        (u"В", u"V"),
        (u"Г", u"G"),
        (u"Д", u"D"),
        (u"Е", u"E"),
        (u"З", u"Z"),
        (u"И", u"I"),
        (u"Й", u"J"),
        (u"К", u"K"),
        (u"Л", u"L"),
        (u"М", u"M"),
        (u"Н", u"N"),
        (u"О", u"O"),
        (u"П", u"P"),
        (u"Р", u"R"),
        (u"С", u"S"),
        (u"Т", u"T"),
        (u"У", u"U"),
        (u"Ф", u"F"),
        (u"Х", u"H"),
        (u"Э", u"E"),
        (u"Ъ", u"`"),
        (u"Ь", u"'"),        
        ## нижний регистр
        # трехбуквенные замены
        (u"щ", u"sch"),
        # двухбуквенные замены
        (u"ё", u"yo"),
        (u"ж", u"zh"),
        (u"ц", u"ts"),
        (u"ч", u"ch"),
        (u"ш", u"sh"),
        (u"ы", u"yi"),
        (u"ю", u"yu"),
        (u"я", u"ya"),
        # однобуквенные замены
        (u"а", u"a"),
        (u"б", u"b"),
        (u"в", u"v"),
        (u"г", u"g"),
        (u"д", u"d"),
        (u"е", u"e"),
        (u"з", u"z"),
        (u"и", u"i"),
        (u"й", u"j"),
        (u"к", u"k"),
        (u"л", u"l"),
        (u"м", u"m"),
        (u"н", u"n"),
        (u"о", u"o"),
        (u"п", u"p"),
        (u"р", u"r"),
        (u"с", u"s"),
        (u"т", u"t"),
        (u"у", u"u"),
        (u"ф", u"f"),
        (u"х", u"h"),
        (u"э", u"e"),
        (u"ъ", u"`"),
        (u"ь", u"'"),
	# для полноты английского алфавит (в slugify)
	# дополняем английскими буквами, которых
	# не в парах
	(u"c", u"c"),
	(u"q", u"q"),
	(u"y", u"y"),
	(u"x", u"x"),
	(u"C", u"C"),
	(u"Q", u"Q"),
	(u"Y", u"Y"),
	(u"X", u"X"),
	(u"1", u"1"),
	(u"2", u"2"),
	(u"3", u"3"),
	(u"4", u"4"),
	(u"5", u"5"),
	(u"6", u"6"),
	(u"7", u"7"),
	(u"8", u"8"),
	(u"9", u"9"),
	(u"0", u"0"),
        )  #: Translation table

RU_ALPHABET = [x[0] for x in TRANSTABLE] #: Russian alphabet that we can translate
EN_ALPHABET = [x[1] for x in TRANSTABLE] #: English alphabet that we can detransliterate
ALPHABET = RU_ALPHABET + EN_ALPHABET #: Alphabet that we can (de)transliterate


def translify(in_string):
    """
    Translify russian text

    @param in_string: input string
    @type in_string: C{unicode}
    
    @return: transliterated string
    @rtype: C{str}

    @raise TypeError: when in_string is not C{unicode}
    @raise ValueError: when string doesn't transliterate completely
    """
    check_type('in_string', unicode)

    translit = in_string
    for symb_in, symb_out in TRANSTABLE:
        translit = translit.replace(symb_in, symb_out)

    try:
        translit = str(translit)
    except UnicodeEncodeError:
        raise ValueError("Unicode string doesn't transliterate completely, " + \
                         "is it russian?")

    return translit

def detranslify(in_string):
    """
    Detranslify

    @param in_string: input string
    @type in_string: C{basestring}
    
    @return: detransliterated string
    @rtype: C{str}

    @raise TypeError: when in_string neither C{str}, no C{unicode}
    @raise ValueError: if in_string is C{str}, but it isn't ascii
    """
    check_type('in_string', basestring)

    # в unicode
    try:
        russian = unicode(in_string)
    except UnicodeDecodeError:
        raise ValueError("We expects when in_string is str type," + \
                         "it is an ascii, but now it isn't. Use unicode " + \
                         "in this case.")

    for symb_out, symb_in in TRANSTABLE:
        russian = russian.replace(symb_in, symb_out)

    return russian

def slugify(in_string):
    """
    Prepare string for slug (i.e. URL or file/dir name)

    @param in_string: input string
    @type in_string: C{basestring}

    @return: slug-string
    @rtype: C{str}

    @raise TypeError: when in_string isn't C{unicode} or C{str}
    @raise ValueError: if in_string is C{str}, but it isn't ascii
    """
    check_type('in_string', basestring)
    try:
        u_in_string = unicode(in_string)
    except UnicodeDecodeError:
        raise ValueError("We expects when in_string is str type," + \
                         "it is an ascii, but now it isn't. Use unicode " + \
                         "in this case.")
    


    # convert & to "and"
    u_in_string = re.sub('\&amp\;|\&', ' and ', u_in_string)
    # replace spaces by hyphen
    u_in_string = re.sub('[-\s]+', '-', u_in_string)
    # remove symbols that not in alphabet
    u_in_string = u''.join([symb for symb  in u_in_string if symb in ALPHABET])
    # translify it
    out_string = translify(u_in_string)
    # remove non-alpha
    return re.sub('[^\w\s-]', '', out_string).strip().lower()
        
def dirify(in_string):
    """
    Alias for L{slugify}
    """
    slugify(in_string)

