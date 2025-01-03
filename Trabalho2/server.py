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
        self.connections = []  # Lista de conexões ativas
        self.populate_map(num_treasures, num_obstacles, num_rooms)

    def create_room(self, rows, cols, num_treasures):
        room_map = [[None for _ in range(cols)] for _ in range(rows)]
        for _ in range(num_treasures):
            x, y = self.get_open_cell(room_map)
            room_map[x][y] = "T"
        return room_map

    def populate_map(self, num_treasures, num_obstacles, num_rooms):
        for _ in range(num_treasures):
            x, y = self.get_open_cell(self.map)
            self.map[x][y] = "T"
        
        for _ in range(num_obstacles):
            x, y = self.get_open_cell(self.map)
            self.map[x][y] = "X"
        
        for _ in range(num_rooms):
            x, y = self.get_open_cell(self.map)
            self.map[x][y] = "R"
        
        self.broadcast_map()  # Envia o mapa inicial para todos os clientes

    def get_open_cell(self, grid):
        while True:
            x = random.randint(0, len(grid) - 1)
            y = random.randint(0, len(grid[0]) - 1)
            if grid[x][y] is None:
                return x, y

    def broadcast_map(self):
        # Converte o mapa para string e envia para todos os clientes
        with self.lock:
            map_string = "\n".join(" ".join(cell if cell else "." for cell in row) for row in self.map)
            for conn in self.connections:
                try:
                    conn.sendall(f"MAP_UPDATE\n{map_string}\n".encode())
                except:
                    # Remove clientes desconectados
                    self.connections.remove(conn)

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(5)
        print("Server started!")

        while True:
            conn, addr = server.accept()
            self.connections.append(conn)  # Armazena a conexão ativa
            threading.Thread(target=self.handle_client, args=(conn, addr)).start()

    def process_player_action(self, player_id, action, conn):
        with self.lock:
            player = self.players[player_id]
            if action.startswith("MOVE"):
                try:
                    _, dx, dy = action.split()
                    dx, dy = int(dx), int(dy)
                except ValueError:
                    conn.sendall(b"Invalid MOVE command! MOVE dx dy")
                    return

                x, y = player["pos"]
                new_x, new_y = x + dx, y + dy

                if not (0 <= new_x < len(self.map) and 0 <= new_y < len(self.map[0])):
                    conn.sendall(b"Invalid move: Out of bounds!")
                    return

                cell = self.map[new_x][new_y]
                if cell in ("X", f"P{player_id}"):
                    conn.sendall(b"Invalid move: Obstacle or player!")
                    return

                if cell == "T":
                    player["treasures"] += 1
                    conn.sendall(b"Treasure collected!")
                elif cell == "R":
                    conn.sendall(b"Entered a treasure room!")
                else:
                    conn.sendall(b"Moved!")

                self.map[x][y] = None
                self.map[new_x][new_y] = f"P{player_id}"
                player["pos"] = (new_x, new_y)

                self.broadcast_map()  # Envia atualização do mapa para todos

            elif action == "STATUS":
                status = f"Position: {player['pos']}, Treasures: {player['treasures']}"
                conn.sendall(status.encode())

            elif action == "QUIT":
                conn.sendall(b"Goodbye!")
                raise ConnectionAbortedError

            else:
                conn.sendall(b"Invalid action!")

    def handle_client(self, conn, addr):
        print(f"Player connected from {addr}")
    
        player_name = conn.recv(1024).decode().strip()
        player_id = player_name if player_name else f"Player{addr[1]}"

        with self.lock:
            x, y = self.get_open_cell(self.map)
            self.players[player_id] = {"pos": (x, y), "treasures": 0}
            self.map[x][y] = f"{player_id}"

        self.broadcast_map()  # Atualiza o mapa para todos

        conn.sendall(b"Welcome to the game! Type commands like MOVE dx dy or STATUS.\n")
        
        try:
            while True:
                data = conn.recv(1024).decode().strip()
                self.process_player_action(player_id, data, conn)
        except (ConnectionAbortedError, ConnectionResetError):
            print(f"Player {player_id} disconnected.")
        finally:
            with self.lock:
                x, y = self.players[player_id]["pos"]
                self.map[x][y] = None
                del self.players[player_id]
                
            self.broadcast_map()  # Atualiza o mapa para todos
            conn.close()

if __name__ == "__main__":
    server = GameServer("127.0.0.1", 65432, 10, 10, 20, 3, 2)
    server.start()

