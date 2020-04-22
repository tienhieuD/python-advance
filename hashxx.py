import sys
import datetime

if __name__ == "__main__":
    before = datetime.datetime.now()
    s = 0
    for i in range(int(len(sys.argv) > 1 and sys.argv[1] or 1)):
        s += i**i
    # print("s: %s" % s)
    # print(sys.argv)
    print(datetime.datetime.now() - before)

# class Cake(object):
#     def __init__(self):
#         self.name = 'Donut'
#         self.color = 'Yellow'
#         self.is_good = True

#     def __getitem__(self, key):
#         return getattr(self, key)
# # print(1)

# cake = Cake()

# print(cake.name)  # Donut
# print(cake['name'])  # TypeError: 'Cake' object is not subscriptable
