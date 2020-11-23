import ServerSocket
import threading

# 메인 실행부분
#server = ServerSocket.ServerSocket(#Port, #Host, 1024)
serverThread = threading.Thread(target=server.Start(), args=())
serverThread.daemon = True
serverThread.start()
