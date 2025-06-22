♟ Flask Socket.IO Chess Game

A simple real-time multiplayer chess game built with Flask, Socket.IO, and Vanilla JS for the frontend. This app allows two players to play chess over the web, handling key rules like castling, en passant, and pawn promotion.

📦 Features

Real-time two-player chess

Legal move validation (including special rules):

Castling (with tracking of king and rook movement)

En passant

Pawn promotion

Check, checkmate, and stalemate detection

Auto-updated board state for all connected players

Session and color assignment per player

🏗 Project Structure

.

├── app.py              # Main server logic (Flask + Socket.IO)

├── templates/
│   └── index.html      # Frontend for the chess board

├── static/
│   └── (Optional CSS/JS)

├── requirements.txt    # Required Python packages

└── README.md

🚀 Getting Started

Prerequisites

Python 3.7+

pip

Installation

Clone the repository:

git clone https://github.com/yourusername/flask-chess-game.git

cd flask-chess-game

Install dependencies:

pip install -r requirements.txt

If requirements.txt doesn't exist yet, you can manually install:

pip install flask flask-socketio

Run the server:

python app.py

Open the browser:

Navigate to http://localhost:5000

👥 Multiplayer Flow

Each player joins with a playerId (sent via Socket.IO)

First player gets white, second gets black

Any additional connections are rejected once both players have joined

🔄 Socket.IO Events

Event	Direction	Description

join	Client → Server	Player requests to join game

update_board	Server → Client	Board state update

make_move	Client → Server	Player attempts a move

player_joined	Server → Client	Notification of other player joining

player_left	Server → Client	Notification of player disconnect

game_over	Server → Client	Triggered on checkmate or stalemate


🧠 Chess Rules Implemented

Piece movement for all pieces

Turn-based enforcement

Check and checkmate

Stalemate

Castling (both sides)

En passant

Promotion to queen

❗ Limitations

No move history or undo

No AI or single-player mode

Basic HTML interface (no drag-drop or advanced UI)

Promotion is hardcoded to queen

📜 License
This project is licensed under the MIT License. Feel free to use, modify, and distribute it.