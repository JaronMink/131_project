import sys
import asyncio


async def handle_client_msg(reader, writer):
    data = await reader.read(100)
    message = data.decode()
    print('Recieved: %s' % message)

    writer.close()

def main():
    #while True\\
        #x = 5
    #print('hi')
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
