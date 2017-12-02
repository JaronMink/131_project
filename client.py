import asyncio
import time
import sys
import json

currentServer = -1
ALFORD = 0
BALL = 1
HOLIDAY = 2
HAMILTON = 3
WELSH = 4

def errorExitNum(msg, num):
    print(msg, file=sys.stderr)
    exit(num)

def errorExitOne(msg):
    errorExitNum(msg, 1)

async def tcp_echo_client(message, loop):
    global currentServer

    reader, writer = await asyncio.open_connection('127.0.0.1', 8889 + currentServer,
                                                   loop=loop)

    #print('Send: %r' % message)
    writer.write(message.encode())

    data = await reader.read()
    jsonBody = json.loads(data.decode())
    print('Received: %r' % jsonBody)

    writer.close()


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

    setUpServerNumber()
    loop = asyncio.get_event_loop()
    print("send message below")
    try:
        while True:
            option = input("press Enter to send location to server")
            if option == 'w':
                message = 'WHATSAT jaron.cs.ucla.edu 10 5'
            else:
                message = 'IAMAT jaron.cs.ucla.edu +34.068930-118.445127 %f' %  time.time()
            loop.run_until_complete(tcp_echo_client(message, loop))
    except KeyboardInterrupt:
        pass
    loop.close()


if __name__ == '__main__':
    main()
