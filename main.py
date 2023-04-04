from itertools import count
import json
from pickle import TRUE
from time import time
import requests
import datetime 
import tweepy
import mysql.connector
import time

class rStop:
    def __init__(self, route_id, stop_id):
        self.stop_id = stop_id
        self.route_id = route_id
    def __hash__(self):
        return hash((self.route_id, self.stop_id))

    def __eq__(self, other):
        return (self.route_id, self.stop_id) == (other.route_id, other.stop_id)
class vehicle:
    def __init__(self, vehicle_id, passenger_load):
        self.vehicle_id = vehicle_id
        self.passenger_load = passenger_load


def busAtNextStop (x, y):
    url = "https://transloc-api-1-2.p.rapidapi.com/arrival-estimates.json"
    querystring = {"agencies":"1323","routes":x,"stops":y,"callback":"call"}
    response = requests.request("GET", url, headers=headers, params=querystring)
    data = json.loads(response.text)
    data=data['data']
    if(data):
        data=data[0]
        data=data['arrivals']
        data = data[0]
        vehicle_id = data['vehicle_id']
        return vehicle_id
    
    return -1

def timeUntilStop (x, y):
    url = "https://transloc-api-1-2.p.rapidapi.com/arrival-estimates.json"
    querystring = {"agencies":"1323","routes":x,"stops":y,"callback":"call"}
    response = requests.request("GET", url, headers=headers, params=querystring)
    data = json.loads(response.text)
    data=data['data']
    data=data[0]
    data=data['arrivals']
    data = data[0]
    stop = datetime.strptime(data['arrival_at'][:19],'%Y-%m-%dT%H:%M:%S')
    curr = datetime.now()
    return stop-curr

def getrstop():    
    url = 'https://transloc-api-1-2.p.rapidapi.com/routes.json'
    querystring = {"agencies":"1323","callback":"call"}
    response = requests.request("GET", url, headers=headers, params=querystring)
    data = json.loads(response.text)
    data=data['data']['1323']
    for i in range(22):
        data1 = data[i]
        route=data1['route_id']
        data1 = data1['stops']
        for j in data1:
            curbusses[str(route)+str(j)] = -1    
    print (json.dumps(curbusses))


def logCapacity(busNum):
    url = 'https://transloc-api-1-2.p.rapidapi.com/vehicles.json'
    querystring = {"agencies":"1323","callback":"call"}
    response = requests.request("GET", url, headers=headers, params=querystring)
    data = json.loads(response.text)
    data = data['data']['1323']
    counter=0
    for i in range(len(data)):
        if data[i]['vehicle_id'] == str(busNum):
            return (data[i]['passenger_load'])
            


def checkStop(x):
    nextbus = busAtNextStop(x.route_id, x.stop_id)
    if(nextbus!=-1):
        currbus = curbusses.get(str(x.route_id)+str(x.stop_id))
        if nextbus != currbus:
            curbusses[str(x.route_id)+str(x.stop_id)]=nextbus
            fill = logCapacity(nextbus)
            insert_stmt = (
                "INSERT INTO confirmedstops "
                "VALUES (%s, %s, now(), %s, %s)"
            )
            data = (x.stop_id, nextbus, x.route_id, fill)
            cursor.execute(insert_stmt, data)
            cnx.commit()
            #nextbus is the vehicle that stops
            print("Stop Detected: Route "+str(x.route_id)+", Stop "+str(x.stop_id))

def checkAll():
    print ("Starting check for stops")
    for i in curbusses:
        rt = int(i[:7])
        st = int(i[7:])
        x=rStop(rt, st)
        checkStop(x)
    print ("Done checking for stops")

def busAtNextStopBetter (f, x):
    data=f
    if(data):
        data=data[0]
        data=data['arrivals']
        data = data[0]
        vehicle_id = data['vehicle_id']
        return vehicle_id
    
    return -1

def checkStopBetter(data, x):
    nextbus = busAtNextStop(x.route_id, x.stop_id)
    if(nextbus!=-1):
        currbus = curbusses.get(str(x.route_id)+str(x.stop_id))
        if nextbus != currbus:
            curbusses[str(x.route_id)+str(x.stop_id)]=nextbus
            insert_stmt = (
                "INSERT INTO confirmedstops "
                "VALUES (%s, %s, now(), %s)"
            )
            data = (x.stop_id, nextbus, x.route_id)
            cursor.execute(insert_stmt, data)
            cnx.commit()
            print("Stop Detected: Route "+str(x.route_id)+", Stop "+str(x.stop_id))

def checkAllBetter():
    url = "https://transloc-api-1-2.p.rapidapi.com/arrival-estimates.json"
    querystring = {"agencies":"1323","callback":"call"}
    response = requests.request("GET", url, headers=headers, params=querystring)
    data = json.loads(response.text)
    for i in curbusses:
        rt = int(i[:7])
        st = int(i[7:])
        x=rStop(rt, st)
        checkStopBetter(data, x)

def initstop(x):
    nextbus = busAtNextStop(x.route_id, x.stop_id)
    if(nextbus!=-1):
        currbus = curbusses.get(str(x.route_id)+str(x.stop_id))
        if nextbus != currbus:
            curbusses[str(x.route_id)+str(x.stop_id)]=nextbus
            print("Stop Initialized: Route "+str(x.route_id)+", Stop "+str(x.stop_id))

def initAll():
    print ("Starting stop initialization")
    for i in curbusses:
        rt = int(i[:7])
        st = int(i[7:])
        x=rStop(rt, st)
        initstop(x)
    print ("Done initializing stops")

def holder():
    cnx1 = mysql.connector.connect(user='app', password='password',
                              host='localhost',
                              database='rubusbot')

    cursor1=cnx1.cursor()
    
    for h in range(24):
        for r in routeList:
            insert_stmt = (
                    "call rubusbot.stopdata_per_hour(%s, %s);"
            )
            data = (r, h)
            cursor1.execute(insert_stmt, data)
        cnx1.commit()
    cursor1.close()

def report():
    cnx2 = mysql.connector.connect(user='app', password='password',
                              host='localhost',
                              database='rubusbot')

    cursor2=cnx2.cursor()
    
    
    
    holder()
    
    daydict = {
        0: 'monday',
        1:'tuesday',
        2:'wednesday',
        3:'thursday',
        4:'friday',
        5:'saturday',
        6:'sunday'
    }
    dayweek = daydict[datetime.datetime.today().weekday()]
    dayweek = 'wednesday'
    cursor2.execute('select count(*) from stop_data s inner join expectedf e on s.route_id=e.route_id and s.hour=e.hour where '+dayweek+'!=0 and s.stops>=(60/e.'+dayweek+');')
    top = cursor2.fetchone()[0]
    cursor2.execute('select count(*) from stop_data s inner join expectedf e on s.route_id=e.route_id and s.hour=e.hour where '+dayweek+'!=0;')
    bottom = cursor2.fetchone()[0]
    pct=100*(top/bottom)
    date = datetime.datetime.today().strftime('%Y-%m-%d')
    date = '2022-09-28'
    cursor2.execute('SET GLOBAL connect_timeout=6000;')
    time.sleep(1)
    cursor2.execute("call rubusbot.getAllTravelTimes('"+date+"');")
    time.sleep(1)
    results = cursor2.fetchall()
 
    
    
    CA_B = str(results[0][0])[2:7]
    CA_L = str(results[1][0])[2:7]
    CA_CD = str(results[2][0])[2:7]
    B_CA = str(results[3][0])[2:7]
    L_CA = str(results[4][0])[2:7]
    CD_CA = str(results[5][0])[2:7]
    L_B = str(results[6][0])[2:7]
    B_L = str(results[7][0])[2:7]

    cnx2.commit()
    cursor2.close()
    return(
    """Bus Stats: """+date+"""
Routes On Time: """+str(pct)[:4]+"""%
Travel Times Between Campuses: 
College Ave-Busch: """+CA_B+"""
College Ave-Livi: """+CA_L+"""
College Ave-C/D: """+CA_CD+"""
Busch-College Ave: """+B_CA+"""
Livi-College Ave: """+L_CA+"""
C/D-College Ave: """+CD_CA+"""
Livi-Busch: """+L_B+""" 
Busch-Livi: """+B_L+""""""
)

while(1==1):
    headers = {
    'x-rapidapi-host': "transloc-api-1-2.p.rapidapi.com",
    'x-rapidapi-key': ""
    }
    auth = tweepy.OAuthHandler("", "")
    auth.set_access_token("", "")
    api = tweepy.API(auth)



    curbusses = json.load(open(r'currbuslist.json'))
    routeNameList = json.load(open(r'routeList.json'))
    stopNameList = json.load(open(r'stopList.json'))    

    routeList=routeNameList.keys()

    cnx = mysql.connector.connect(user='app', password='password',
                              host='localhost',
                              database='rubusbot')

    cursor=cnx.cursor()

    
    
    
    
    
    print('waiting for midnight')
    while(datetime.datetime.today().time().hour>12):
        time.sleep(1)
    print('its midnight, starting collection')
    initAll()
    print('initialized, starting to check times')
    while(int(datetime.datetime.today().time().hour)<23 or int(datetime.datetime.today().time().minute)<45):
        try:
            checkAll()
        except:
            print("error checking stops, trying again in 1 minute")
        time.sleep(60)
    print('11:45, time to report\n\n\n')
    api.update_status(report())
    cnx.close()
