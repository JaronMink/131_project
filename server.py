import sys
import asyncio
import logging


async def handle_client_msg(reader, writer):
    global log_file
    data = await reader.read(100)
    message = data.decode()
    #print('Recieved: %s' % message)
    log = logging.getLogger('log')
    log.debug(message)
    
    writer.close()

def configureLogging(serverNum):
    if serverNum == 0:
        name = 'Alford.log'

    logging.basicConfig(
        filename=name,
        level=logging.DEBUG
    )


ALFORD = 0
BALL = 1
HAMILTON = 2
HOLIDAY = 3
WELSH = 4

def main():
    #while True\\
        #x = 5
    #print('hi')
    configureLogging(ALFORD)


    loop = asyncio.get_event_loop()
    coroutine = asyncio.start_server(handle_client_msg, '127.0.0.1', 8889, loop=loop)
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
