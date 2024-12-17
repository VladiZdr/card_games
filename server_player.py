import random
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import json
from threading import Lock
from urllib.parse import urlparse, parse_qs

# Players
players = []
host = None
next_player_id = 2
belot_id = 0
# controll game state
game_type = None
game_lock = Lock()
game_on = False
belot_on = False
liar_on = False
liar_new_game = False
# cards
played_cards = []
selected_cards = []
player_hands = {}
left_belot_deck = []
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
liar_deck = []
left_liar_deck = []

#directory = os.path.expanduser("~/Documents/Card_game")
#os.chdir(directory)
    
class GameServerHandler(SimpleHTTPRequestHandler):
    
    def do_POST(self):
        global players, host, next_player_id, game_type, selected_cards, game_on, belot_on, left_cards, belot_id, left_belot_deck, liar_on, liar_deck, left_liar_deck

        if self.path == "/register_host":
            if players:
                self.respond("Already registered")
                return
            
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode()
            host_data = json.loads(post_data)

            host_data["id"] = 1
            host = host_data
            players = [host]
            self.respond("Host registered successfully.")

        elif self.path == "/register_player":
            
            # Register a new player
            global next_player_id  
            new_player = {"id": next_player_id}
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
                    belot_id = 0
                    played_cards.clear()
                    player_hands.clear()
                    belot_on = True  # Update belot_on safely
                    left_belot_deck = belot_deck.copy()
                    random.shuffle(left_belot_deck)
                self.respond(json.dumps({"belot_on": belot_on}), content_type="application/json")
            

        elif self.path == "/start_liar":
            with game_lock:
                liar_on = True
                num_players = len(players)
                liar_deck.clear()
                ascii_range = list(range(128, 229))  # ASCII values from 128 to 228 (Up to 20 players)
                for i in range(num_players * 2):
                    liar_deck.append(f"A{chr(ascii_range[i % len(ascii_range)])}")
                for i in range(num_players * 3):
                    liar_deck.append(f"2{chr(ascii_range[i % len(ascii_range)])}")

            self.respond(json.dumps({"liar_on": liar_on}), content_type="application/json")


        # Play a card
        elif self.path.startswith("/play_card"):
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length))
            player_id = str(post_data.get("id"))  # Ensure player_id is treated as string
            card = post_data.get("card")

            with game_lock:
                # Log for debugging
                print(f"Received play_card request: player_id={player_id}, card={card}")
                print(f"Current player_hands: {player_hands}")
                
                if player_id not in player_hands:
                    # Player ID not found in the system
                    self.respond(json.dumps({"success": False, "error": "Player not found"}))
                elif card not in player_hands[player_id]:
                    # Card not in the player's hand
                    self.respond(json.dumps({"success": False, "error": "Card not in hand"}))
                else:
                    # Valid request, process the card
                    player_hands[player_id].remove(card)
                    played_cards.append(card)
                    # Log updated state
                    print(f"Card played: {card}, updated hand: {player_hands[player_id]}")
                    print(f"Played cards: {played_cards}")
                    self.respond(json.dumps({"success": True, "newHand": player_hands[player_id]}))

        elif self.path == "/reset_belot":
            with game_lock:
                played_cards.clear()
            self.respond(json.dumps({"success": True}))
                    
        elif self.path == "/end_game":
            with game_lock:
                players = []
                next_player_id = 2
                game_on = False
            self.respond("Game ended. Redirecting players...")
        elif self.path == "/end_belot":
            with game_lock:
                players = []
                next_player_id = 2
                belot_on = False
            self.respond("Game ended. Redirecting players...")
        elif self.path == "/end_liar":
            with game_lock:
                players = []
                next_player_id = 2
                liar_on = False
                left_liar_deck = []
            self.respond("Game ended. Redirecting players...")

    def do_GET(self): 
        global left_cards, left_belot_deck, player_hands, played_cards, belot_id, liar_deck, liar_new_game, left_liar_deck
        
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

        elif self.path.startswith("/belot_on"):
            with game_lock:
                try:
                    self.respond(json.dumps(belot_on), content_type="application/json")
                except Exception as e:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(f"Error checking game status: {str(e)}".encode())

        elif self.path.startswith("/liar_on"):
            with game_lock:
                try:
                    self.respond(json.dumps({"liar_on": liar_on}), content_type="application/json")
                except Exception as e:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(f"Error checking game status: {str(e)}".encode())  

        elif self.path.startswith("/liar_new_game"):
            with game_lock:
                liar_new_game = True
                left_liar_deck = liar_deck.copy()
                random.shuffle(left_liar_deck)
                self.respond(json.dumps({"liar_new_game": liar_new_game}), content_type="application/json")

        elif self.path.startswith("/liar_hand"):
            with game_lock:
                if not left_liar_deck:
                    liar_new_game = False
                    self.respond("No more cards")
                    return
                self.respond(json.dumps({"hand":[left_liar_deck.pop() for _ in range(5)]}), content_type="application/json")

        elif self.path.startswith("/get_belot_id"):
            with game_lock:
                belot_id += 1
                self.respond(json.dumps({"id": belot_id}), content_type="application/json")

        # Deal first 5 cards
        elif self.path.startswith("/get_belot_hand1"):
            played_cards.clear()
            query = parse_qs(urlparse(self.path).query)
            player_id = query.get('id', [None])[0]
            if not player_id:
                self.respond(json.dumps({"error": "Player ID is required"}), content_type="application/json")
                return

            with game_lock:
                # Reset deck if it's the first request or manually reset
                if not left_belot_deck:
                    left_belot_deck = belot_deck.copy()
                    random.shuffle(left_belot_deck)
                    player_hands.clear()
                
                # Ensure each player gets a unique hand
                if player_id in player_hands:
                    # Clear the existing hand for the player
                    player_hands[player_id].clear()

                # Check if there are enough cards to deal
                if len(left_belot_deck) < 5:
                    self.respond(json.dumps({"error": "Not enough cards to deal"}), content_type="application/json")
                    return

                # Deal 5 new cards to the player
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

        # Get played cards
        elif self.path == "/get_played_cards":
            self.respond(json.dumps({"playedCards": played_cards}))
        
        elif self.path == "/won_hand":
            self.respond(json.dumps({"wonCards": played_cards}))
            played_cards.clear()

        # End games -> go back to menus
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
                    self.respond(json.dumps({"belot_on":  belot_on}), content_type="application/json")
                except Exception as e:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(f"Error checking game status: {str(e)}".encode())

        elif self.path.startswith("/liar_off"):
            with game_lock:
                try:
                    self.respond(json.dumps({"liar_on":  liar_on}), content_type="application/json")
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