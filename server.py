import sys
import asyncio
import logging
import time

#key is the client id
cache = {}
currentServer = -1


ALFORD = 0
BALL = 1
HAMILTON = 2
HOLIDAY = 3
WELSH = 4
loop = None

def getConnectedServers():
    global currentServer
    if currentServer == ALFORD:
        return [HAMILTON, WELSH]
    elif currentServer == BALL:
        return [HOLIDAY, WELSH]
    elif currentServer == HAMILTON:
        return [ALFORD, HOLIDAY]
    elif currentServer == HOLIDAY:
        return [HAMILTON, BALL]
    elif currentServer == WELSH:
        return [ALFORD, BALL]
    else:
        errorExitOne('error, unidentified server number')


def errorExitNum(msg, num):
    print(msg, file=sys.stderr)
    exit(num)

def errorExitOne(msg):
    errorExitNum(msg, 1)

def serverToString(server):
    if server == ALFORD:
        return 'Alford'
    elif server == BALL:
        return 'Ball'
    elif server == HAMILTON:
        return 'Hamilton'
    elif server == HOLIDAY:
        return 'Holiday'
    elif server == WELSH:
        return 'Welsh'
    else:
        return 'Error, incorrect server'

def isValidFloodMessage(message):
    parsedMessage = message.split()
    if parsedMessage[0] != 'FLOOD' or len(parsedMessage) != 7:
        return False
    return True

def isValidIAMAT(message):
    parsedMessage = message.split()
    if parsedMessage[0] != 'IAMAT' or len(parsedMessage) != 4:
        return False
    return True

class Location:
    def __init__(self, id, latitude, longitude, posixTime, recievedTime, server):
        self.id = id
        self.latitude = latitude
        self.longitude = longitude
        self.posixTime = posixTime
        self.receivedTime = recievedTime
        self.receivedServer = server

    def toATMessage(self):
        timeDiff = float(self.receivedTime) - float(self.posixTime)
        if timeDiff > 0:
            timeDiff = "+%f" % timeDiff

        return ("AT %s %s %s %s%s %s" %(serverToString(self.receivedServer), timeDiff, self.id, self.longitude, self.latitude, self.posixTime))

    def toString(self):
        return('%s %s %s %s %s %s' % (self.id, self.latitude, self.longitude, self.posixTime, self.receivedTime, self.receivedServer));

    def toFloodMsg(self):
        return ('FLOOD %s' % self.toString())

    @staticmethod
    def floodToLocation(msg):
        parsedString = msg.split()
        return Location(parsedString[1], parsedString[2], parsedString[3], parsedString[4], parsedString[5], parsedString[6])

    @staticmethod
    def stringToLocation(string):
        parsedString = string.split()
        return Location(parsedString[0], parsedString[1], parsedString[2], parsedString[3], parsedString[4], parsedString[5])
    #@staticmethod
    #def ATMessageToLocation(ATmessage):
    #    parsedMessage = ATmessage.split()
    #    id = parsedMessage[3]
    #    latitude, longitude = seperateLongAndLat(parsedMessage[4])
    #    receivedTime = parsedMessage[5]
    #    server = parsedMessage[1]



def seperateLongAndLat(longAndLat):
    seenPlusOrMinus = 0
    for i, c in enumerate(longAndLat):
        if c == '+' or c=='-':
            seenPlusOrMinus = seenPlusOrMinus + 1
        if seenPlusOrMinus == 2:
            return (longAndLat[:i], longAndLat[i:])



def getLocationFromIAMAT(command):
    parsedCommand = command.split()
    id = parsedCommand[1]
    longAndLat = parsedCommand[2]
    longitude, latitude = seperateLongAndLat(longAndLat)
    posixTime = parsedCommand[3]

    return Location(id, latitude, longitude, posixTime, time.time(), currentServer)

async def flood(message, destinationServer, loop):

    log = logging.getLogger('log')

    try:
        reader, writer = await asyncio.open_connection('127.0.0.1', 8889 + destinationServer,
                            loop=loop)
        log.debug('SENT FLOOD TO %s:%s' % (serverToString(destinationServer), message))
        print('Sent Flood to %s:%s' % (serverToString(destinationServer), message))
        writer.write(message.encode())
        await writer.drain()

    except Exception:
        log.error('ERROR, CANNOT CONNECT TO SERVER %s. FAILED MESSAGE: %s' % (serverToString(destinationServer), message))
        print('ERROR, CANNOT CONNECT TO SERVER %s. FAILED MESSAGE: %s' % (serverToString(destinationServer), message), file=sys.stderr)
    finally:
        writer.close()

    writer.close

def floodConnectedServers(location):
    for server in getConnectedServers():
        task = asyncio.ensure_future(flood(location.toFloodMsg(), server, loop))

async def handle_client_msg(reader, writer):
    global cache

    data = await reader.read(100)
    message = data.decode()

    #log things
    addr = writer.get_extra_info('peername')
    log = logging.getLogger('log')

    #if valid IAMAT, create location, add location to cache, send to other servers, send AT back to client
    if isValidIAMAT(message):
        log.debug('RECEIVED FROM %s:%s' % (addr, message))
        print('Recieved Command: %s' % message)
        location = getLocationFromIAMAT(message)
        cache[location.id] = location
        writer.write(location.toATMessage().encode())
        await  writer.drain()

        #add to other servers
        floodConnectedServers(location)

        log.debug('SENT TO %s:%s' % (addr, location.toATMessage()))
        print('Sent to Client: %s' % location.toATMessage())
    elif isValidFloodMessage(message):
        location = Location.floodToLocation(message)
        if location.id not in cache or (location.id in cache and location.posixTime > cache[location.id].posixTime):
            cache[location.id] = location
            floodConnectedServers(location)
            log.debug('FLOOD RECIEVED FROM OTHER SERVER %s: %s' % (addr, message))
            print('FLOOD RECIEVED FROM OTHER SERVER %s: %s' % (addr, message))

        else:
            log.debug('REDUNANT FLOOD RECIEVED FROM OTHER SERVER %s: %s' % (addr, message))
            print('REDUNANT FLOOD RECIEVED FROM OTHER SERVER %s: %s' % (addr, message))

    else:
        log.debug('RECEIVED INVALID COMMAND FROM %s:%s' % (addr, message))
        print('Error, received an invalid command: %s' % (message) , file=sys.stderr)

        writer.write(('? %s' % message).encode())
        await  writer.drain()

        log.debug('SENT TO %s:%s' % (addr, message))

    writer.close()



def configureLogging():
    global currentServer


    logging.basicConfig(
        filename='%s.log' % serverToString(currentServer),
        level=logging.DEBUG
    )


def setUpServerNumber():
    global currentServer
    if len(sys.argv) < 2:
        errorExitOne('Error, must contain server name as arguement')
    if len(sys.argv) > 2 :
        errorExitOne('Error, only one argument is allowed as a server name')

    serverStr = sys.argv[1]

    if(serverStr.upper() == 'ALFORD'):
        currentServer = ALFORD
    elif (serverStr.upper() == 'BALL'):
        currentServer = BALL
    elif (serverStr.upper() == 'HOLIDAY'):
        currentServer = HOLIDAY
    elif (serverStr.upper() == 'HAMILTON'):
        currentServer = HAMILTON
    elif(serverStr.upper() == 'WELSH'):
        currentServer = WELSH
    else:
        errorExitOne('Error, server must be one of the following:\n\tAlford\n\tBall\n\tHoliday\n\tHamilton\n\tWelsh')



def main():
    #while True\\
        #x = 5
    #print('hi')
    global currentServer
    setUpServerNumber()
    #message = 'IAMAT g.w +342.323-2.32123 43242.3434'
    #location = getLocationFromIAMAT(message)

    configureLogging()

    basePort = 8889
    global loop
    loop = asyncio.get_event_loop()
    coroutine = asyncio.start_server(handle_client_msg, '127.0.0.1', 8889 + currentServer, loop=loop)
    server = loop.run_until_complete(coroutine)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    #close socket
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()

if __name__ == '__main__':
    main()
