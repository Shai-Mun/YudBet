__author__ = 'Yossi'
import datetime,sys

cnt =0
print (str(datetime.datetime.now())[:19],"start count lines")
while True:
    try:
        a= input()
        cnt+=1
        print (str(datetime.datetime.now())[:19], "so far cnt = " + str(cnt))

    except:
        break
print (str(datetime.datetime.now())[:19], "There were " + str(cnt) + " lines")

