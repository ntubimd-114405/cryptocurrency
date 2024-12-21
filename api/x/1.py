from fetch import *
from sql import *
#預計一天一次
if __name__ == "__main__":
    for i in get_x():
        h=get_html(i[0])
        insert_xpost(i[0],h,i[1])
