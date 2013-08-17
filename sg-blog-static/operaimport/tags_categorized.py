# -*- coding: utf-8 -*-

from operaimport.tag_data import tag_data


class dict_of_lists(dict):
    def __init__(self):
        super(dict_of_lists, self).__init__()
    def append(self, key, value):
        if self.has_key(key):
            assert isinstance(self[key], list)
            self[key].append(value)
        else:
            self[key] = [ value ]


tag_info_by_tag_name = dict()
tag_info_by_category = dict_of_lists()
for cat, rows in tag_data.items():
    for row in rows:
        name = original_name = row['tag']
        #assert name
        #name = rewrite_tag(name)
        #cat = row[1]
        #assert cat
        title = row.get('title', None)
        if not title: title = name
        title_ru = row.get('title_ru', None)
        tag_info = {
            'name':     name,
            'category': cat,
            'title':    title,
            'title_ru': title_ru,
            'descr_en': row['descr_en'] if row.has_key('descr_en') else None,
            'descr_ru': row['descr_ru'] if row.has_key('descr_ru') else None,
        }
        #print 'names: "%s" => "%s"' % (original_name, name)

        if not tag_info_by_tag_name.has_key(name):
            #assert not tag_info_by_tag_name.has_key(name), 'duplicate definition for tag %s, prob. because of %s' % (name, original_name)
            #if name == 'shake':
            #    print 'setting for tag %s' % name
            tag_info_by_tag_name[name] = tag_info
            tag_info_by_category.append(tag_info['category'], tag_info)
            #if tag_info_by_category.has_key(cat):
            #    tag_info_by_category[cat].append(tag_info)
            #else:
            #    tag_info_by_category[cat] = [tag_info ]

# return hash category_name -> tag_info
def get_used_tags_categories():
    tags_by_cat = dict()
    uncategorized = []

    from gen_static import BlogMeta

    blog_meta = BlogMeta.instance()
    for tag_name in blog_meta.articles_by_tags.keys():
        #tag_name = rewrite_tag(tag_name)
        tag_info = tag_info_by_tag_name.get(tag_name)
        if tag_info:
            cat = tag_info['category']
            if tags_by_cat.has_key(cat):
                tags_by_cat[cat].append(tag_info)
            else:
                tags_by_cat[cat] = [ tag_info ]
        else:
            #raise Exception('tag_name not categorized: %s' % (tag_name,))
            uncategorized.append(tag_name)

    return tags_by_cat, uncategorized

def get_region_tags():
    tags = [ row['tag'] for row in tag_data['region'] ]
    return list(set(tags))

def get_tag_for_related_articles(tag_names):
    for cat in [ 'series', 'ensemble', 'jazz', 'composer', 'vocalist', 'modern', 'genre' ]:
        tag_names_2 = [ ti['name'] for ti in tag_info_by_category[cat] ]
        intersection = list(set(tag_names) & set(tag_names_2))
        if len(intersection):
            return intersection[0]
    return None

def get_about_text(tag_name):
    tag_info = tag_info_by_tag_name.get(tag_name, None)
    if tag_info:
        descr = tag_info.get('descr_en', None)
        title = tag_info.get('title', None)
        if descr and title:
            descr = descr[0].lower() + descr[1:]
            return '<b>%s</b> is %s' % (title, descr)
        else:
            def_abouts = {
                'composer': '%s is a soviet composer.',
                'vocalist': '%s is a soviet singer.',
                'series':   '%s is a series of vinyl records released at Melodiya.'
            }
            about = def_abouts.get(tag_info['category'], None)
            if about:
                title = tag_info['title']
                if tag_info.has_key('title_ru') and tag_info['title_ru']:
                    title = '%s (%s)' % (tag_info['title'], tag_info['title_ru'])
                return about % title
    return None
