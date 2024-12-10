from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import json

#directory = os.path.expanduser("~/Documents/Card_game")
#os.chdir(directory)

players = []
host = None
next_player_id = 2
game_type = None
selected_cards = []


class GameServerHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        global players, host, next_player_id, game_type, selected_cards

        if self.path == "/register_host":
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

        elif self.path == "/select_game":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode()
            game_data = json.loads(post_data)

            game_type = game_data["game"]
            self.respond(f"Game selected: {game_type}")

        elif self.path == "/submit_cards":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode()
            card_data = json.loads(post_data)

            selected_cards = card_data["cards"]
            self.respond(f"Cards selected: {', '.join(selected_cards)}")

        elif self.path == "/start_game":
            if not selected_cards:
                self.respond("No cards selected. Cannot start the game.")
            else:
                # Example: Distribute one card to each player
                for i, player in enumerate(players):
                    player["card"] = selected_cards[i % len(selected_cards)]
                self.respond("Game started! Cards distributed.")

    def do_GET(self):
        if self.path == "/players":
            self.respond(json.dumps(players), content_type="application/json")
        elif self.path == "/get_selected_cards":
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
