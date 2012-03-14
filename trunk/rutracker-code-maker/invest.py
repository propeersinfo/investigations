import pickle

from fastpic import OnlineImageInfo

img = OnlineImageInfo(1,2)
print img
pickle.dump([img], open("dump", "w"))
print pickle.load(open("dump", "r"))