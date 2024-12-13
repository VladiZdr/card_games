import random
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import json
from threading import Lock

game_lock = Lock()
players = []
host = None
next_player_id = 2
game_type = None
selected_cards = []
game_on = False
left_cards = []

#directory = os.path.expanduser("~/Documents/Card_game")
#os.chdir(directory)

class GameServerHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        global players, host, next_player_id, game_type, selected_cards, game_on

        if self.path == "/register_host" and not players:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode()
            host_data = json.loads(post_data)

            host_data["id"] = 1
            host = host_data
            players = [host]
            self.respond("Host registered successfully.")

        elif self.path == "/register_player":
            # Extract the client's IP address from the connection
            ip_address = self.client_address[0]

            # Check if the IP is already registered
            if any(player['ip'] == ip_address for player in players):
                # Respond with the existing player's ID
                existing_player = next(player for player in players if player['ip'] == ip_address)
                self.respond(json.dumps({"id": existing_player["id"]}))
            else:
                # Register a new player
                global next_player_id
                new_player = {"id": next_player_id, "ip": ip_address}
                next_player_id += 1
                players.append(new_player)
                self.respond(json.dumps({"id": new_player["id"]}))


        elif self.path == "/submit_cards":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode()
            card_data = json.loads(post_data)
            
            selected_cards = card_data["cards"]
            print(f"Selected cards updated: {selected_cards}")  # Debugging log
            self.respond("Cards submitted successfully.")

        elif self.path == "/start_game":
            with game_lock:
                game_on = True  # Update game_on safely
                left_cards = selected_cards
            self.respond("Game started!")
                
        
        elif self.path == "/end_game":
            with game_lock:
                game_on = False
            self.respond("Game ended. Redirecting players...")

    def do_GET(self): 

        if self.path == "/players":
            self.respond(json.dumps(players), content_type="application/json")
        elif self.path == "/get_selected_cards":
            self.respond(json.dumps(selected_cards), content_type="application/json")

        elif self.path.startswith("/game_on"):
            with game_lock:
                try:
                    self.respond(json.dumps(game_on), content_type="application/json")
                except Exception as e:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(f"Error checking game status: {str(e)}".encode())

        elif self.path.startswith("/game_off"):
            with game_lock:
                try:
                    self.respond(json.dumps(game_on), content_type="application/json")
                except Exception as e:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(f"Error checking game status: {str(e)}".encode())

        else:
            super().do_GET()

    def respond(self, message, content_type="text/plain"):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(message.encode())


HOST, PORT = "0.0.0.0", 8000
server = HTTPServer((HOST, PORT), GameServerHandler)
print(f"Serving on http://{HOST}:{PORT}")
server.serve_forever()