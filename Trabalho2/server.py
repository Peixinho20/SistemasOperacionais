import socket
import threading
import random

class GameServer:
    def __init__(self, host, port, rows, cols, num_treasures, num_obstacles, num_rooms):
        self.host = host
        self.port = port
        self.map = [[None for _ in range(cols)] for _ in range(rows)]
        self.players = {}
        self.rooms = {i: self.create_room(5, 5, 5) for i in range(num_rooms)}
        self.lock = threading.Lock()  # Proteção para região crítica
        self.populate_map(num_treasures, num_obstacles, num_rooms)

    def create_room(self, rows, cols, num_treasures):
        room_map = [[None for _ in range(cols)] for _ in range(rows)]
        for _ in range(num_treasures):
            x, y = self.get_open_cell(room_map)
            room_map[x][y] = "T"
        return room_map

    def populate_map(self, num_treasures, num_obstacles, num_rooms):
        # Adiciona tesouros
        for _ in range(num_treasures):
            x, y = self.get_open_cell(self.map)
            self.map[x][y] = "T"
        
        # Adiciona obstáculos
        for _ in range(num_obstacles):
            x, y = self.get_open_cell(self.map)
            self.map[x][y] = "X"
        
        # Adiciona entradas para salas de tesouro
        for _ in range(num_rooms):
            x, y = self.get_open_cell(self.map)
            self.map[x][y] = "R"
        
        self.display_map()

    def display_map(self):
        print("\nMapa Principal:")
        for row in self.map:
            print(" ".join(cell if cell else "." for cell in row))
        print() # Linha para separar as atualizações    

    def get_open_cell(self, grid):
        while True:
            x = random.randint(0, len(grid) - 1)
            y = random.randint(0, len(grid[0]) - 1)
            if grid[x][y] is None:
                return x, y

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(5)
        print("Server started!")

        while True:
            conn, addr = server.accept()
            threading.Thread(target=self.handle_client, args=(conn, addr)).start()
    
    def process_player_action(self, player_id, action, conn):
        with self.lock:  # Proteção para a região crítica
            player = self.players[player_id]
            if action.startswith("MOVE"):
                try:
                    _, dx, dy = action.split()
                    dx, dy = int(dx), int(dy)
                except ValueError:
                    conn.sendall(b"Invalid MOVE command! MOVE dx dy")
                x, y = player["pos"]
                new_x, new_y = x + dx, y + dy

                # Verifica se a nova posição está dentro do mapa
                if not (0 <= new_x < len(self.map) and 0 <= new_y < len(self.map[0])):
                    conn.sendall(b"Invalid move: Out of bounds!")
                    return

                # Verifica se a célula está ocupada
                cell = self.map[new_x][new_y]
                if cell in ("X", f"P{player_id}"):
                    conn.sendall(b"Invalid move: Obstacle or player!")
                    return

                # Ações para diferentes tipos de célula
                if cell == "T":  # Tesouro
                    player["treasures"] += 1
                    conn.sendall(b"Treasure collected!")
                elif cell == "R":  # Sala de tesouro
                    conn.sendall(b"Entered a treasure room!")
                else:  # Movimento normal
                    conn.sendall(b"Moved!")

                # Atualiza o mapa e a posição do jogador
                self.map[x][y] = None
                self.map[new_x][new_y] = f"P{player_id}"
                player["pos"] = (new_x, new_y)
                
                self.display_map()

            elif action == "STATUS":
                # Retorna o status do jogador
                status = f"Position: {player['pos']}, Treasures: {player['treasures']}"
                conn.sendall(status.encode())

            elif action == "QUIT":
                # Ação de saída
                conn.sendall(b"Goodbye!")
                raise ConnectionAbortedError  # Para sinalizar ao loop do cliente

            else:
                conn.sendall(b"Invalid action!")
    
    def handle_client(self, conn, addr):
        print(f"Player connected from {addr}")
    
        # Recebe o nome do jogador
        player_name = conn.recv(1024).decode().strip()
        player_id = player_name if player_name else f"Player{addr[1]}"  # Fallback caso o nome esteja vazio

        with self.lock:
            x, y = self.get_open_cell(self.map)
            self.players[player_id] = {"pos": (x, y), "treasures": 0}
            self.map[x][y] = f"{player_id}"

        self.display_map() #exibição do mapa atualizado 
        
        conn.sendall(b"Welcome to the game! Type commands like MOVE dx dy or STATUS.\n")
        
        try:
            while True:
                data = conn.recv(1024).decode().strip()
                self.process_player_action(player_id, data, conn)
        except (ConnectionAbortedError, ConnectionResetError):
            print(f"Player {player_id} disconnected.")
        except Exception as e:
            print(f"Error with player {player_id}: {e}")
        finally:
            # Limpa o jogador ao desconectar
            with self.lock:
                x, y = self.players[player_id]["pos"]
                self.map[x][y] = None
                del self.players[player_id]
                
            self.display_map()
            conn.close()

if __name__ == "__main__":
    server = GameServer("127.0.0.1", 65432, 10, 10, 20, 3, 2)
    server.start()
