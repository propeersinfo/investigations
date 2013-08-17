def rewrite_tag(old_tag):
    new_tag = old_tag.strip()
    new_tag = replaces.get(new_tag, new_tag)
    new_tag = new_tag.replace(' ', '-')
    return new_tag

replaces = {
'aida vedisheva':		'vedisheva',
'alexander zatsepin':	'zatsepin',
'alla pugachova':		'pugachova',
'azerbayjan':			'azerbaijan',
'boris rychkov':		'rychkov',
'david goloschekin':	'goloschekin',
'disco band':			'disco-petrenko',
'dj jankie':			'jan-kit',
'edita pyekha':			'pyekha',
'evgeny gevorgyan':		'gevorgyan',
'gennadiy gladkov':		'gladkov',
'igor brill':			'brill',
'igor nazaruk':			'nazaruk',
'imants kalnins':		'kalnins',
'isaac shwartz':		'shwartz',
'jaan-kuman':			'kuman',
'jaan kuman':			'kuman',
'konstantin orbelian':	'orbelyan',
'maria codrianu':		'codrianu',
'muslim magomayev':		'magomayev',
'polad bulbuloglu':		'bulbuloglu',
'raimonds pauls':		'pauls',
'shake':				'shake',
'tonis magi':			'magi',
'twist\'n\'beat':		'shake',
'uno naissoo':			'naissoo',
'vainshtein':			'weinstein',
'melodia':              'melodiya',
}