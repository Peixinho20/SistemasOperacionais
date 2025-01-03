import socket
#import keyboard

class GameClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.conn.connect((self.host, self.port))
        name = input("Enter your player name: ")
        self.conn.sendall(name.encode())
        print(self.conn.recv(1024).decode())

    def send_command(self, command):
        self.conn.sendall(command.encode())
        response = self.conn.recv(1024).decode()
        print(response)

    def close(self):
        self.conn.sendall(b"EXIT")
        self.conn.close()
    
    def start_game(self):
        print("Use 'W', 'A', 'S', 'D' to move, and 'Q' to quit.")
        
        while True:
            cmd = input("Enter command: ").strip().upper()
            if cmd == "W":
                self.send_command("MOVE -1 0")
            elif cmd == "S":
                self.send_command("MOVE 1 0")
            elif cmd == "A":
                self.send_command("MOVE 0 -1")
            elif cmd == "D":
                self.send_command("MOVE 0 1")
            elif cmd == "Q":
                self.send_command("QUIT")
                print("Exiting game...")
                break
            else:
                print("Invalid command! Use 'W', 'A', 'S', 'D', or 'Q'.")
    
if __name__ == "__main__":
    client = GameClient("127.0.0.1", 65432)
    client.connect()
    client.start_game()
    client.close()

