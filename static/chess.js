const socket = io(); // Connect to the server

const chessboard = document.querySelector('.chessboard');
let selectedSquare = null;
let currentPlayer = null; // Current turn from the server
let playerColor = null;   // Your assigned color

// Unicode pieces with color and type encoded
const PIECES = {
    '♜': { color: 'black', type: 'rook' },
    '♞': { color: 'black', type: 'knight' },
    '♝': { color: 'black', type: 'bishop' },
    '♛': { color: 'black', type: 'queen' },
    '♚': { color: 'black', type: 'king' },
    '♟': { color: 'black', type: 'pawn' },
    '♖': { color: 'white', type: 'rook' },
    '♘': { color: 'white', type: 'knight' },
    '♗': { color: 'white', type: 'bishop' },
    '♕': { color: 'white', type: 'queen' },
    '♔': { color: 'white', type: 'king' },
    '♙': { color: 'white', type: 'pawn' }
};

// Fallback initial board (server will override it)
let board = [
    ["♜", "♞", "♝", "♛", "♚", "♝", "♞", "♜"],
    ["♟", "♟", "♟", "♟", "♟", "♟", "♟", "♟"],
    ["", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", ""],
    ["♙", "♙", "♙", "♙", "♙", "♙", "♙", "♙"],
    ["♖", "♘", "♗", "♕", "♔", "♗", "♘", "♖"]
];

// Handle board updates from server
socket.on('update_board', (data) => {
    board = data.board;
    currentPlayer = data.currentPlayer;

    // Set player color only once
    if (data.playerColor && !playerColor) {
        playerColor = data.playerColor;
        console.log("You are playing as:", playerColor);
    }

    renderBoard();

    const toastColor = currentPlayer === 'white' ? '#444' : '#111';
    showToast(`${capitalize(currentPlayer)}'s Turn`, 2000, toastColor);
});

// Render the entire board
function renderBoard() {
    chessboard.innerHTML = '';

    board.forEach((rowArr, r) => {
        rowArr.forEach((piece, c) => {
            const cell = document.createElement('div');
            cell.classList.add((r + c) % 2 ? 'black' : 'white');
            cell.dataset.row = r;
            cell.dataset.col = c;

            if (piece) {
                const span = document.createElement('span');
                span.textContent = piece;
                cell.appendChild(span);
            }

            cell.addEventListener('click', onCellClick);
            chessboard.appendChild(cell);
        });
    });
}

// Handle cell click
function onCellClick(e) {
    if (playerColor !== currentPlayer) {
        showToast("It's not your turn!", 2000, '#aa0000');
        return;
    }

    const cell = e.currentTarget;
    const r = +cell.dataset.row;
    const c = +cell.dataset.col;
    const piece = board[r][c];

    // First click: select a piece
    if (selectedSquare === null) {
        if (piece && PIECES[piece].color === playerColor) {
            clearHighlights();
            cell.classList.add('highlight');
            selectedSquare = { r, c };
        }
        return;
    }

    // Second click: send move attempt
    const { r: fr, c: fc } = selectedSquare;
    const toRow = r;
    const toCol = c;

    socket.emit('make_move', {
        from: fr,
        from_col: fc,
        to: toRow,
        to_col: toCol,
        playerColor: playerColor
    });

    clearHighlights();
    selectedSquare = null;
}

// Utility to capitalize words
function capitalize(word) {
    return word.charAt(0).toUpperCase() + word.slice(1);
}

// Remove all cell highlights
function clearHighlights() {
    document.querySelectorAll('.highlight').forEach(el => el.classList.remove('highlight'));
}

// Now emit the join event
let playerId = localStorage.getItem('playerId');
if (!playerId) {
    playerId = 'player_' + Math.floor(Math.random() * 10000);
    localStorage.setItem('playerId', playerId);
}
socket.emit('join', { playerId });

// Handle game over
socket.on('game_over', data => {
    const msg = `Game Over: ${data.result}. ${data.winner === 'draw' ? 'Draw!' : capitalize(data.winner) + ' wins!'}`;
    showToast(msg, 6000, '#333');
});

// Toast notification system
function showToast(message, duration = 3000, color = '#333') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.style.backgroundColor = color;
    toast.className = 'show';
    setTimeout(() => {
        toast.className = toast.className.replace('show', '');
    }, duration);
}
