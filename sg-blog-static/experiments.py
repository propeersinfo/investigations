from utils import hexdigest, pick_pseudo_random_elements


src_list = [
    "one", "two", "three foo", "bar mag", "time", "xen", "xen", "keen", "mex", "xxxx", "zzz"
]

hash_code_src = ""
for item in src_list:
    hash_code_src = "%s%s" % (hash_code_src, hexdigest(item))
hash_code = hexdigest(hash_code_src)
rnd = pick_pseudo_random_elements(hash_code, src_list, 6)

print "rnd: %s" % rnd
