import random
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import json

players = []
host = None
next_player_id = 2
game_type = None
selected_cards = []
dealt_cards = {}

#directory = os.path.expanduser("~/path/to/html/files")
#os.chdir(directory)

class GameServerHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        global players, host, next_player_id, game_type, selected_cards, dealt_cards

        if self.path == "/register_host" and not players:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode()
            host_data = json.loads(post_data)

            host_data["id"] = 1
            host = host_data
            players = [host]
            self.respond("Host registered successfully.")

        elif self.path == "/register_player":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode()
            player_data = json.loads(post_data)

            player_data["id"] = next_player_id
            next_player_id += 1
            players.append(player_data)
            self.respond(json.dumps({"id": player_data["id"]}))

        elif self.path == "/submit_cards":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode()
            card_data = json.loads(post_data)
            
            selected_cards = card_data["cards"]
            print(f"Selected cards updated: {selected_cards}")  # Debugging log
            self.respond("Cards submitted successfully.")


        elif self.path == "/start_game":
            if not selected_cards:
                self.respond("No cards selected. Cannot start the game.")
            else:
                # Distribute one random card to each player
                dealt_cards = {player["id"]: random.choice(selected_cards) for player in players}
                self.respond("Game started! Redirecting players...")

        elif self.path == "/end_game":
            dealt_cards.clear()
            self.respond("Game ended. Redirecting players...")

    def do_GET(self):
        global dealt_cards

        if self.path.startswith("/get_dealt_card"):
            # Extract player ID from query parameter
            player_id = int(self.path.split("?id=")[-1])
            card = dealt_cards.get(player_id, "No card assigned")
            self.respond(json.dumps({"card": card}), content_type="application/json")
        elif self.path == "/players":
            self.respond(json.dumps(players), content_type="application/json")
        elif self.path == "/get_selected_cards":
            # Send the selected cards as a JSON response
            self.respond(json.dumps(selected_cards), content_type="application/json")
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