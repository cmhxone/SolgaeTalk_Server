import socket	# 소켓 라이브러리 추가
import threading	# 스레드 라이브러리 추가
import struct	# 구조체 라이브러리 추가
import pymysql	# MySQL 라이브러리 추가

# 소켓 서버의 클래스를 선언한다
class ServerSocket:
	# 서버 소켓의 기본정보를 담는 클래스 멤버 변수선언
	__socket : int	# 서버의 소켓
	__port : int	# 포트 번호
	__host : str	# 호스트 이름 (URL or IP)
	__bufsize : int	# 버퍼 크기
	__running : bool # 실행 상태를 알려주는 변수
	__lock : threading.Lock	# 스레드 싱크로나이즈를 위한 스레드 제어 변수
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
			#print("소켓 생성 완료")
		except socket.error as er:
			#print("소켓 생성 실패")
			exit(-1)

		# 소켓 연동
		try:
			self.__socket.bind((host, port))	# 소켓을 포트, 호스트와 연결한다
			#print("소켓 연동 성공")
		except socket.error as er:
			#print("소켓 연동 실패")
			exit(-1)

		# 소켓 연결 대기
		try:
			self.__socket.listen(5)
			#print("소켓 연결대기 성공")
		except socket.error as er:
			#print("소켓 연결대기 실패")
			exit(-1)

	# 클라이언트로부터 메시지를 읽어오는 함수
	def ProcessMessage(self, clientSocket, addr):

		nickname = str	# 클라이언트의 닉네임을 저장하는 변수
		able = bool	# DB에 존재하는지 확인 후 사용가능한 클라이언트인지를 반환하는 부울 변수

		while self.__running:
			try:
				data = clientSocket.recv(self.__bufsize) # 클라이언트 소켓으로부터 메시지를 전달 받는다

				try:
					message = struct.unpack("I32s512s", data) # 전달받은 메시지의 플래그 값과 메시지를 분석한다
					nickname = message[1].decode().replace("\0", "")	# 메시지를 분석 해 닉네임 값을 저장한다
				
					try:
						# MariaDB 연동
						db = pymysql.connect(host=self.__host, port=3306, user="Solgae", passwd="gntech2152", db="SolgaeTalk", charset="utf8", autocommit=True)
						cursor = db.cursor()
						# 닉네임 값 존재여부 확인
						cursor.execute("SELECT COUNT(*) FROM Accounts WHERE nickname='" + nickname + "'")
						result = cursor.fetchone()
					
						if result[0] != 1:
							able = False
						else:
							able = True
					except Exception as e:
						able = False
						#print(e)

				except:
					self.DestroyClient(clientSocket)
					#print(addr, "과의 접속이 종료되었습니다")
					break

			except ConnectionResetError:	# 클라이언트가 비정상적으로 종료된 경우
				self.DestroyClient(clientSocket)
				db = pymysql.connect(host=self.__host, port=3306, user="Solgae", passwd="gntech2152", db="SolgaeTalk", charset="utf8", autocommit=True)
				cursor = db.cursor()
				cursor.execute("UPDATE Accounts SET online=False WHERE nickname='" + nickname +"'")
				#print(nickname, addr, "과의 접속이 종료되었습니다")
				break

			# 메시지 수신 플래그는 5002, 이 플래그를 전송 받은경우 모든 클라이언트에 메시지를 출력해준다
			if message[0] == 5002:
				#print("[", message[1].decode().replace("\00", "") , "] ", message[2].decode() )
				self.SendMessage(data)

			# 접속 플래그는 1996, 이 플래그를 전송 받은 경우 모든 클라이언트에 접속 메시지를 출력해준다
			elif message[0] == 1996:
				#print(nickname, addr, "에서 정식 클라이언트를 통해 접속하였습니다")
				self.__lock.acquire
				self.__SocketList.append(clientSocket)
				self.SendMessage(data)
				self.__lock.release

			# 접속 종료 플래그는 2015, 이 플래그를 전송 받은 경우 모든 클라이언트에 접속 종료 메시지를 출력해준다
			elif message[0] == 2015:
				#print(nickname, addr, "이 접속종료를 요청하였습니다")
				self.SendMessage(data)
				self.DestroyClient(clientSocket)
				db = pymysql.connect(host=self.__host, port=3306, user="Solgae", passwd="gntech2152", db="SolgaeTalk", charset="utf8", autocommit=True)
				cursor = db.cursor()
				cursor.execute("UPDATE Accounts SET online=False WHERE nickname='" + nickname +"'")
				break

			# 이외의 검증되지 않은 플래그들은 접속을 종료한다
			else:
				self.DestroyClient(clientSocket)
				#print(addr, "과의 접속이 종료되었습니다")
				break
	
	# 클라이언트 소켓을 할당 해제하는 함수
	def DestroyClient(self, clientSocket):
		self.__lock.acquire
		try:
			clientSocket.close()
			self.__SocketList.remove(clientSocket)
		except:
			pass
		self.__lock.release

	# 연결된 클라이언트 소켓에 메시지를 전달하는 함수
	def SendMessage(self, data):
		self.__lock.acquire
		try:
			for socket in self.__SocketList:
				socket.send(data)
		except:
			#print("Sending Failure")
			pass
		self.__lock.release

	# 서버를 실행하는 함수
	def Start(self):
		self.__running = True	# 서버가 실행될때 running 값은 true가 된다

		while self.__running:
			try:
				clientSocket, addr = self.__socket.accept()	# 서버가 실행되는 동안 계속 접속을 받는다
			except KeyboardInterrupt:	# Ctrl+C 키를 이용해 종료한 경우
				self.__running = False
				self.__socket.close()
				#print("서버가 종료되었습니다")
				exit(0)
			
			# 소켓의 접속여부를 확인한다
			if clientSocket in self.__SocketList:
				pass
			else:
				#print(addr, "에서 접속하였습니다")
				# 접속이 완료된 경우 별도의 스레드를 생성하여 메시지 처리를 관할한다
				t = threading.Thread(target=self.ProcessMessage, args=(clientSocket, addr))
				t.daemon = True
				t.start()

	# 서버를 종료하는 함수
	def Stop(self):
		self.__running = False

