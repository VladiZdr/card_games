from http.server import HTTPServer, SimpleHTTPRequestHandler
import json

# Global data
players = []  # List of connected players
host = None  # Host information
next_player_id = 2  # Unique ID starts at 2 (Player 1 is reserved for the host)


class GameServerHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        global players, host, next_player_id

        if self.path == "/register_host":
            # Register the host
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode()
            host_data = json.loads(post_data)

            host_data["id"] = 1  # Host is always Player 1
            host = host_data
            players = [host]  # Reset the players list with the host
            print(f"Host registered: {host}")
            
            # Respond to the host
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Host registered successfully.")

        elif self.path == "/register_player":
            # Register a new player
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode()
            player_data = json.loads(post_data)

            player_data["id"] = next_player_id
            next_player_id += 1
            players.append(player_data)
            print(f"Player registered: {player_data}")

            # Respond to the player with their ID
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({"id": player_data["id"]}).encode())

    def do_GET(self):
        if self.path == "/players":
            # Serve the list of players to the host or players
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(players).encode())
        else:
            # Serve static files (host.html and player.html)
            super().do_GET()


# Start the server
HOST, PORT = "0.0.0.0", 8000
print(f"Starting server on {HOST}:{PORT}")
server = HTTPServer((HOST, PORT), GameServerHandler)
server.serve_forever()
