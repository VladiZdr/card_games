import os
import http.server
import socketserver

#download PythonCode-Pad and add a folder Card_game with both host and html files
#http://x.x.x.x:8000/host.html
#http://x.x.x.x:8000/client.html

# Set the directory to the 'Card_game' folder
directory = os.path.expanduser("~/Documents/Card_game")
os.chdir(directory)

# Start the server
PORT = 8000
Handler = http.server.SimpleHTTPRequestHandler
httpd = socketserver.TCPServer(("", PORT), Handler)

print(f"Serving at port {PORT} from directory: {directory}")
httpd.serve_forever()
