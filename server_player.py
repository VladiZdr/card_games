import random
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import json
from threading import Lock
from urllib.parse import urlparse, parse_qs

game_lock = Lock()
players = []
host = None
next_player_id = 2
game_type = None
selected_cards = []
game_on = False
belot_on = False
left_cards = []
full_deck = [
"2 Spades", "3 Spades", "4 Spades", "5 Spades", "6 Spades", "7 Spades", "8 Spades", "9 Spades", "10 Spades", "J  Spades", "D Spades", "K Spades", "A Spades", 
"2 Hearts", "3 Hearts", "4 Hearts", "5 Hearts", "6 Hearts", "7 Hearts", "8 Hearts", "9 Hearts", "10 Hearts", "J  Hearts", "D Hearts", "K Hearts", "A Hearts", 
"2 Diamonds", "3 Diamonds", "4 Diamonds", "5 Diamonds", "6 Diamonds", "7 Diamonds", "8 Diamonds", "9 Diamonds", "10 Diamonds", "J  Diamonds", "D Diamonds", "K Diamonds", "A Diamonds", 
"2 Clubs", "3 Clubs", "4 Clubs", "5 Clubs", "6 Clubs", "7 Clubs", "8 Clubs", "9 Clubs", "10 Clubs", "J  Clubs", "D Clubs", "K Clubs", "A Clubs"
]
belot_deck = [
    "7♣", "8♣", "9♣", "10♣", "J♣", "Q♣", "K♣", "A♣",
    "7♦", "8♦", "9♦", "10♦", "J♦", "Q♦", "K♦", "A♦",
    "7♥", "8♥", "9♥", "10♥", "J♥", "Q♥", "K♥", "A♥",
    "7♠", "8♠", "9♠", "10♠", "J♠", "Q♠", "K♠", "A♠",
]

# Player hands
player_hands = {}
left_belot_deck = [] 

#directory = os.path.expanduser("~/Documents/Card_game")
#os.chdir(directory)

def reset_belot_deck():
    global left_belot_deck
    left_belot_deck = belot_deck.copy()
    random.shuffle(left_belot_deck)

class GameServerHandler(SimpleHTTPRequestHandler):
    
    def do_POST(self):
        global players, host, next_player_id, game_type, selected_cards, game_on, belot_on, left_cards

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
            if len(selected_cards) >= len(players):
                with game_lock:
                    game_on = True  # Update game_on safely
                    left_cards = selected_cards.copy()
                self.respond(json.dumps({"game_on": True}), content_type="application/json")
            else:
                self.respond(json.dumps({"game_on": False, "message": "Not enough cards selected for all players."}), content_type="application/json")
        
        elif self.path == "/start_belot":
            #if 4 == len(players):
                with game_lock:
                    belot_on = True  # Update belot_on safely
                self.respond(json.dumps({"belot_on": True}), content_type="application/json")
            #else:
                #self.respond(json.dumps({"belot_on": False, "message": "Not enough players."}), content_type="application/json")

        elif self.path == "/reset_belot":
            self.respond("Reseting belot hands")
                    
        elif self.path == "/end_game":
            with game_lock:
                game_on = False
            self.respond("Game ended. Redirecting players...")
        elif self.path == "/end_belot":
            with game_lock:
                belot_on = False
            self.respond("Game ended. Redirecting players...")

    def do_GET(self): 
        global left_cards
        
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
        elif self.path.startswith("/belot_on"):
            with game_lock:
                try:
                    self.respond(json.dumps(belot_on), content_type="application/json")
                except Exception as e:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(f"Error checking game status: {str(e)}".encode())            
        
        
        elif self.path.startswith("/get_dealt_card"):
            with game_lock:  # Ensure thread-safety
                if left_cards:  # Check if there are cards left
                    # Select a random card and remove it from the list
                    dealt_card = random.choice(left_cards)
                    left_cards.remove(dealt_card)
                    self.respond(json.dumps({"card": dealt_card}), content_type="application/json")
                else:
                    # If no cards are left, respond with an error message
                    self.respond(json.dumps({"error": "No cards left to deal."}), content_type="application/json")

        elif self.path.startswith("/get_belot_hand1"):
            query = parse_qs(urlparse(self.path).query)
            player_id = query.get('id', [None])[0]
            if not player_id:
                self.respond(json.dumps({"error": "Player ID is required"}), content_type="application/json")
                return

            with game_lock:
                # Reset deck if it's the first request or manually reset
                if not left_belot_deck:
                    reset_belot_deck()
                
                # Ensure each player gets a unique hand
                if player_id not in player_hands:
                    if len(left_belot_deck) < 5:
                        self.respond(json.dumps({"error": "Not enough cards to deal"}), content_type="application/json")
                        return
                    
                    player_hands[player_id] = [left_belot_deck.pop() for _ in range(5)]

            self.respond(json.dumps({"hand": player_hands[player_id]}), content_type="application/json")

        # Endpoint to deal 3 additional cards
        elif self.path.startswith("/get_belot_hand2"):
            query = parse_qs(urlparse(self.path).query)
            player_id = query.get('id', [None])[0]
            if not player_id:
                self.respond(json.dumps({"error": "Player ID is required"}), content_type="application/json")
                return

            with game_lock:
                if player_id not in player_hands or len(left_belot_deck) < 3:
                    self.respond(json.dumps({"error": "Cannot deal additional cards"}), content_type="application/json")
                    return

                player_hands[player_id].extend([left_belot_deck.pop() for _ in range(3)])

            self.respond(json.dumps({"hand": player_hands[player_id]}), content_type="application/json")

        # Endpoint to reset the deck and clear player hands
        elif self.path == "/reset_belot":
            with game_lock:
                reset_belot_deck()
                player_hands.clear()

            self.respond(json.dumps({"message": "Belot deck reset"}), content_type="application/json")


        elif self.path.startswith("/game_off"):
            with game_lock:
                try:
                    self.respond(json.dumps(game_on), content_type="application/json")
                except Exception as e:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(f"Error checking game status: {str(e)}".encode())
        elif self.path.startswith("/belot_off"):
            with game_lock:
                try:
                    self.respond(json.dumps(belot_on), content_type="application/json")
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