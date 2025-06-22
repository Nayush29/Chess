import copy
from flask import Flask, render_template,request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

# Initial board state
board = [
    ["♜", "♞", "♝", "♛", "♚", "♝", "♞", "♜"],
    ["♟", "♟", "♟", "♟", "♟", "♟", "♟", "♟"],
    ["", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", ""],
    ["♙", "♙", "♙", "♙", "♙", "♙", "♙", "♙"],
    ["♖", "♘", "♗", "♕", "♔", "♗", "♘", "♖"]
]

players = []
current_player = 'white'

white_king_pos = (7, 4)
black_king_pos = (0, 4)

castling_rights = {
    "white_king_moved": False,
    "white_rook_kingside_moved": False,
    "white_rook_queenside_moved": False,
    "black_king_moved": False,
    "black_rook_kingside_moved": False,
    "black_rook_queenside_moved": False
}

last_move = {"from": None, "to": None, "piece": None}


@app.route('/')
def index():
    return render_template('index.html')


# Simple player management
player_sessions = {}  # sid -> color
player_ids = {}       # playerId -> color

@socketio.on('join')
def on_join(data=None):
    sid = request.sid
    player_id = data.get('playerId') if data else None

    if not player_id:
        emit('error', {'message': 'Missing player ID'})
        return

    print(f"[JOIN] playerId={player_id}, sid={sid}")

    # If already joined, reject
    if player_id in player_ids:
        emit('error', {'message': 'Player already joined'})
        return

    # Assign available color
    assigned_colors = set(player_ids.values())
    if 'white' not in assigned_colors:
        player_color = 'white'
    elif 'black' not in assigned_colors:
        player_color = 'black'
    else:
        emit('error', {'message': 'Game is full'})
        return

    # Save session info
    player_ids[player_id] = player_color
    player_sessions[sid] = {
        'playerId': player_id,
        'color': player_color
    }

    emit('update_board', {
        'board': board,
        'currentPlayer': current_player,
        'playerColor': player_color
    })

    emit('player_joined', {
        'playerId': player_id,
        'color': player_color
    }, broadcast=True, include_self=False)


@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    session = player_sessions.pop(sid, None)

    if session:
        player_id = session['playerId']
        print(f"[DISCONNECT] sid={sid}, playerId={player_id}")
        player_ids.pop(player_id, None)

        emit('player_left', {
            'playerId': player_id
        }, broadcast=True)

@socketio.on('make_move')
def on_move(data):
    global current_player, white_king_pos, black_king_pos, last_move

    fr, fc = data['from'], data['from_col']
    tr, tc = data['to'], data['to_col']
    player_color = data['playerColor']
    piece = board[fr][fc]

    if not piece or player_color != current_player or not is_legal_move(piece, fr, fc, tr, tc, player_color):
        return

    # Simulate the move
    captured = board[tr][tc]
    board[tr][tc], board[fr][fc] = piece, ''
    old_king_pos = white_king_pos if player_color == 'white' else black_king_pos
    new_king_pos = (tr, tc) if piece in ['♔', '♚'] else old_king_pos

    if piece == '♔':
        white_king_pos = new_king_pos
    elif piece == '♚':
        black_king_pos = new_king_pos

    if is_in_check(player_color):
        # Illegal move, undo
        board[fr][fc], board[tr][tc] = piece, captured
        if piece == '♔':
            white_king_pos = old_king_pos
        elif piece == '♚':
            black_king_pos = old_king_pos
        return

    # Handle en passant
    if piece in ['♙', '♟'] and captured == '' and fc != tc:
        board[fr][tc] = ''

    # Handle castling
    if piece in ['♔', '♚'] and abs(tc - fc) == 2:
        if tc == 6:  # kingside
            board[tr][5] = board[tr][7]
            board[tr][7] = ''
        elif tc == 2:  # queenside
            board[tr][3] = board[tr][0]
            board[tr][0] = ''

    # Update castling rights
    if piece == '♔':
        castling_rights['white_king_moved'] = True
    elif piece == '♚':
        castling_rights['black_king_moved'] = True
    elif piece == '♖' and fr == 7:
        if fc == 0:
            castling_rights['white_rook_queenside_moved'] = True
        elif fc == 7:
            castling_rights['white_rook_kingside_moved'] = True
    elif piece == '♜' and fr == 0:
        if fc == 0:
            castling_rights['black_rook_queenside_moved'] = True
        elif fc == 7:
            castling_rights['black_rook_kingside_moved'] = True

    # Pawn promotion
    if piece == '♙' and tr == 0:
        board[tr][tc] = '♕'
    elif piece == '♟' and tr == 7:
        board[tr][tc] = '♛'

    last_move = {"from": (fr, fc), "to": (tr, tc), "piece": piece}
    current_player = 'black' if current_player == 'white' else 'white'

    is_mate, is_stalemate = check_game_over()

    emit('update_board', {
        'board': board,
        'currentPlayer': current_player
    }, broadcast=True)

    if is_mate or is_stalemate:
        emit('game_over', {
            'result': 'checkmate' if is_mate else 'stalemate',
            'winner': ('white' if current_player == 'black' else 'black') if is_mate else 'draw'
        }, broadcast=True)


def is_legal_move(piece, fr, fc, tr, tc, current_player):
    if not (0 <= tr < 8 and 0 <= tc < 8):
        return False

    if fr == tr and fc == tc:
        return False

    piece_color = get_color(piece)
    if piece_color != current_player:
        return False

    target = board[tr][tc]
    if target and get_color(target) == piece_color:
        return False

    dr, dc = tr - fr, tc - fc

    if piece == '♙':
        if fr == 6 and dr == -2 and dc == 0 and board[5][fc] == '' and board[4][fc] == '':
            return True
        if dr == -1 and dc == 0 and board[tr][tc] == '':
            return True
        if dr == -1 and abs(dc) == 1 and target != '':
            return True
        if dr == -1 and abs(dc) == 1 and target == '' and last_move['piece'] == '♟':
            lfr, lfc = last_move['from']
            ltr, ltc = last_move['to']
            if lfr == 1 and ltr == 3 and ltc == tc and fr == 3:
                return True
        return False

    if piece == '♟':
        if fr == 1 and dr == 2 and dc == 0 and board[2][fc] == '' and board[3][fc] == '':
            return True
        if dr == 1 and dc == 0 and board[tr][tc] == '':
            return True
        if dr == 1 and abs(dc) == 1 and target != '':
            return True
        if dr == 1 and abs(dc) == 1 and target == '' and last_move['piece'] == '♙':
            lfr, lfc = last_move['from']
            ltr, ltc = last_move['to']
            if lfr == 6 and ltr == 4 and ltc == tc and fr == 4:
                return True
        return False

    if piece in ['♖', '♜']:
        return (dr == 0 or dc == 0) and is_clear_path(fr, fc, tr, tc)

    if piece in ['♘', '♞']:
        return (abs(dr), abs(dc)) in [(2, 1), (1, 2)]

    if piece in ['♗', '♝']:
        return abs(dr) == abs(dc) and is_clear_path(fr, fc, tr, tc)

    if piece in ['♕', '♛']:
        return (abs(dr) == abs(dc) or dr == 0 or dc == 0) and is_clear_path(fr, fc, tr, tc)

    if piece in ['♔', '♚']:
        if abs(dr) <= 1 and abs(dc) <= 1:
            return True
        if current_player == 'white' and fr == 7 and fc == 4:
            if tc == 6 and not castling_rights['white_king_moved'] and not castling_rights['white_rook_kingside_moved'] and \
               board[7][5] == board[7][6] == '':
                return True
            if tc == 2 and not castling_rights['white_king_moved'] and not castling_rights['white_rook_queenside_moved'] and \
               board[7][1] == board[7][2] == board[7][3] == '':
                return True
        if current_player == 'black' and fr == 0 and fc == 4:
            if tc == 6 and not castling_rights['black_king_moved'] and not castling_rights['black_rook_kingside_moved'] and \
               board[0][5] == board[0][6] == '':
                return True
            if tc == 2 and not castling_rights['black_king_moved'] and not castling_rights['black_rook_queenside_moved'] and \
               board[0][1] == board[0][2] == board[0][3] == '':
                return True
        return False

    return False


def is_clear_path(fr, fc, tr, tc):
    dr = (tr - fr) and ((tr - fr) // abs(tr - fr))
    dc = (tc - fc) and ((tc - fc) // abs(tc - fc))
    r, c = fr + dr, fc + dc
    while (r, c) != (tr, tc):
        if board[r][c] != '':
            return False
        r += dr
        c += dc
    return True


def is_in_check(color):
    king_pos = white_king_pos if color == 'white' else black_king_pos
    enemy = 'black' if color == 'white' else 'white'
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p and get_color(p) == enemy:
                if is_legal_move(p, r, c, king_pos[0], king_pos[1], enemy):
                    return True
    return False


def check_game_over():
    king_pos = white_king_pos if current_player == 'white' else black_king_pos
    legal_moves = generate_legal_moves(current_player, king_pos)
    if not legal_moves:
        if is_in_check(current_player):
            return True, False  # Checkmate
        else:
            return False, True  # Stalemate
    return False, False


def generate_legal_moves(color, king_pos):
    moves = []
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece and get_color(piece) == color:
                for tr in range(8):
                    for tc in range(8):
                        if is_legal_move(piece, r, c, tr, tc, color):
                            b_copy = copy.deepcopy(board)
                            captured = b_copy[tr][tc]
                            b_copy[tr][tc], b_copy[r][c] = piece, ''
                            k_pos = (tr, tc) if piece in ['♔', '♚'] else king_pos
                            if not is_in_check_simulated(b_copy, k_pos, color):
                                moves.append(((r, c), (tr, tc)))
    return moves


def is_in_check_simulated(test_board, king_pos, color):
    enemy_color = 'black' if color == 'white' else 'white'
    for r in range(8):
        for c in range(8):
            p = test_board[r][c]
            if p and get_color(p) == enemy_color:
                if is_legal_move(p, r, c, king_pos[0], king_pos[1], enemy_color):
                    return True
    return False


def get_color(p):
    return 'white' if p in ['♙', '♖', '♘', '♗', '♕', '♔'] else 'black'


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
