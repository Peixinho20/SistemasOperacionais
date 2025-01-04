import socket
import threading

class GameClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = True  # Flag para controle da thread

    def connect(self):
        self.conn.connect((self.host, self.port))
        name = input("Enter your player name: ")
        self.conn.sendall(name.encode())
        print(self.conn.recv(1024).decode())

        # Inicia uma thread para escutar mensagens do servidor
        threading.Thread(target=self.listen_to_server, daemon=True).start()

    def listen_to_server(self):
        """Escuta atualizações do servidor em tempo real."""
        while self.running:
            try:
                message = self.conn.recv(1024).decode()
                if message.startswith("MAP_UPDATE"):
                    print("\n--- Game Map Updated ---")
                    print(message.split("\n", 1)[1])  # Exibe o mapa atualizado
                else:
                    print(f"\nServer: {message}")
            except ConnectionError:
                print("Connection lost to the server.")
                self.running = False
                break
    
    def listen_for_updates(self):
        while True:
            try:
                message = self.conn.recv(1024).decode()
                if message.startswith("MAP_UPDATE"):
                    print("\nMapa Atualizado:")
                    print(message[10:])  # Exibe o mapa atualizado
                else:
                    print("Server:", message)
            except ConnectionResetError:
                print("Disconnected from server.")
                break

    def send_command(self, command):
        """Envia comandos para o servidor."""
        try:
            self.conn.sendall(command.encode())
        except BrokenPipeError:
            print("Unable to send command. Connection closed.")
            self.running = False

    def close(self):
        """Encerra a conexão com o servidor."""
        self.running = False
        self.conn.sendall(b"QUIT")
        self.conn.close()

    def start_game(self):
        """Gerencia as interações do jogador com o jogo."""
        print("Use 'W', 'A', 'S', 'D' to move, and 'Q' to quit.")
        
        while self.running:
            cmd = input("Enter command: ").strip().upper()
            if cmd == "W":
                self.send_command("MOVE -1 0")  # Move para cima
            elif cmd == "S":
                self.send_command("MOVE 1 0")  # Move para baixo
            elif cmd == "A":
                self.send_command("MOVE 0 -1")  # Move para a esquerda
            elif cmd == "D":
                self.send_command("MOVE 0 1")  # Move para a direita
            elif cmd == "Q":
                self.send_command("QUIT")
                print("Exiting game...")
                break
            else:
                print("Invalid command! Use 'W', 'A', 'S', 'D' or 'Q'.")
        
        self.close()

if __name__ == "__main__":
    client = GameClient("127.0.0.1", 65432)
    client.connect()
    client.start_game()

