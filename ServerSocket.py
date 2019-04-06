import socket	# 소켓 라이브러리 추가
import threading	# 스레드 라이브러리 추가
import struct	# 구조체 라이브러리 추가

# 소켓 서버의 클래스를 선언한다
class ServerSocket:
	# 서버 소켓의 기본정보를 담는 클래스 멤버 변수선언
	__socket = int	# 서버의 소켓
	__port = int	# 포트 번호
	__host  = str	# 호스트 이름 (URL or IP)
	__bufsize = int	# 버퍼 크기
	__running = bool # 실행 상태를 알려주는 변수
	__lock = threading.Lock()	# 스레드 싱크로나이즈를 위한 스레드 제어 변수
	__SocketList = []	# 접속한 클라이언트의 소켓을 저장할 배열

	# 클래스 생성자 (인자값으로 포트, 호스트주소, 버퍼크기를 전달)
	def __init__(self, port, host, bufsize):
		self.__port = port
		self.__host = host
		self.__bufsize = bufsize
		self.__running = False	# 생성 시 실행 상태를 false 로 만들어주자
		self.__lock = threading.Lock()

		# 소켓 생성
		try:
			self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)	# 서버 소켓을 생성한다
			print("소켓 생성 완료")
		except socket.error as er:
			print("소켓 생성 실패")
			exit(-1)

		# 소켓 연동
		try:
			self.__socket.bind((host, port))	# 소켓을 포트, 호스트와 연결한다
			print("소켓 연동 성공")
		except socket.error as er:
			print("소켓 연동 실패")
			exit(-1)

		# 소켓 연결 대기
		try:
			self.__socket.listen(5)
			print("소켓 연결대기 성공")
		except socket.error as er:
			print("소켓 연결대기 실패")
			exit(-1)

	# 클라이언트로부터 메시지를 읽어오는 함수
	def ProcessMessage(self, clientSocket, addr):
		while self.__running:
			try:
				data = clientSocket.recv(self.__bufsize) # 클라이언트 소켓으로부터 메시지를 전달 받는다
				print(data)
			except ConnectionResetError:	# 클라이언트가 비정상적으로 종료된 경우
				print(addr, "과의 접속이 종료되었습니다");
				break;
			

	# 서버를 실행하는 함수
	def Start(self):
		self.__running = True	# 서버가 실행될때 running 값은 true가 된다

		while self.__running:
			try:
				clientSocket, addr = self.__socket.accept()	# 서버가 실행되는 동안 계속 접속을 받는다
			except KeyboardInterrupt:	# Ctrl+C 키를 이용해 종료한 경우
				self.__running = False
				self.__socket.close()
				print("서버가 종료되었습니다")
				exit(0)
			
			# 소켓의 접속여부를 확인한다
			if clientSocket in self.__SocketList:
				pass
			else:
				self.__lock.acquire
				self.__SocketList.append(clientSocket)
				self.__lock.release
				print(addr, "에서 접속하였습니다")
				# 접속이 완료된 경우 별도의 스레드를 생성하여 메시지 처리를 관할한다
				t = threading.Thread(target=self.ProcessMessage, args=(clientSocket, addr))
				t.daemon = True
				t.start()

	# 서버를 종료하는 함수
	def Stop(self):
		self.__running = False

