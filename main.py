from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import random

app = FastAPI(title="Tumba Yumba Engine")

class GameState(BaseModel):
    board: list
    current_player: int
    game_over: bool = False
    winner: int = None

def init_board():
    return [4, 4, 4, 4, 4, 4, 0, 4, 4, 4, 4, 4, 4, 0]

@app.get("/new_game", response_model=GameState)
def new_game():
    return GameState(board=init_board(), current_player=1)

def execute_move(board: list, player: int, pit_index: int):
    stones = board[pit_index]
    board[pit_index] = 0
    
    if stones == 1:
        target = (pit_index + 1) % 14
        if (player == 1 and target == 13) or (player == 2 and target == 6):
            target = (target + 1) % 14
        board[target] += 1
        last_pit = target
    else:
        board[pit_index] = 1
        stones -= 1
        current_pit = pit_index
        while stones > 0:
            current_pit = (current_pit + 1) % 14
            if player == 1 and current_pit == 13: continue
            if player == 2 and current_pit == 6: continue
            board[current_pit] += 1
            stones -= 1
        last_pit = current_pit

    extra_turn = False
    if (player == 1 and last_pit == 6) or (player == 2 and last_pit == 13):
        extra_turn = True

    if not extra_turn:
        if player == 1 and (7 <= last_pit <= 12) and (board[last_pit] % 2 == 0):
            board[6] += board[last_pit]
            board[last_pit] = 0
        elif player == 2 and (0 <= last_pit <= 5) and (board[last_pit] % 2 == 0):
            board[13] += board[last_pit]
            board[last_pit] = 0

        if player == 1 and (0 <= last_pit <= 5) and (board[last_pit] == 1):
            opposite = 12 - last_pit
            if board[opposite] > 0:
                board[6] += board[last_pit] + board[opposite]
                board[last_pit] = 0
                board[opposite] = 0
        elif player == 2 and (7 <= last_pit <= 12) and (board[last_pit] == 1):
            opposite = 12 - last_pit
            if board[opposite] > 0:
                board[13] += board[last_pit] + board[opposite]
                board[last_pit] = 0
                board[opposite] = 0
                
        next_player = 2 if player == 1 else 1
    else:
        next_player = player

    if sum(board[0:6]) == 0 or sum(board[7:13]) == 0:
        board[6] += sum(board[0:6])
        board[13] += sum(board[7:13])
        for i in range(14):
            if i != 6 and i != 13: board[i] = 0
        game_over = True
        if board[6] > board[13]: winner = 1
        elif board[13] > board[6]: winner = 2
        else: winner = 0

    return board, next_player, game_over, winner

@app.post("/make_move", response_model=GameState)
def make_move(state: GameState, pit_index: int):
    board = state.board
    player = state.current_player
    
    if player == 1 and not (0 <= pit_index <= 5):
        raise HTTPException(status_code=400, detail="Ход только из лунок 0-5")
    if board[pit_index] == 0:
        raise HTTPException(status_code=400, detail="Лунка пуста")

    board, next_player, game_over, winner = execute_move(board, player, pit_index)
    
    while next_player == 2 and not game_over:
        valid_pits = [i for i in range(7, 13) if board[i] > 0]
        if not valid_pits: break
        
        best_pit = None
        for pit in valid_pits:
            stones = board[pit]
            if stones == 1 and pit == 12:
                best_pit = pit
                break
            elif stones > 1 and (pit + stones - 1) % 14 == 13:
                best_pit = pit
                break
        
        if best_pit is None:
            best_pit = random.choice(valid_pits)
            
        board, next_player, game_over, winner = execute_move(board, 2, best_pit)

    return GameState(board=board, current_player=next_player, game_over=game_over, winner=winner)

@app.get("/", response_class=HTMLResponse)
def get_gui():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Tumba Yumba</title>
        <link href="https://jsdelivr.net" rel="stylesheet">
        <style>
            body { background: #1a1a2e; color: white; text-align: center; font-family: 'Segoe UI', sans-serif; padding-top: 50px; }
            h1 { font-weight: 700; color: #ff9f43; margin-bottom: 30px; letter-spacing: 2px; }
            .board { background: #16213e; border: 4px solid #0f3460; border-radius: 25px; padding: 30px; display: inline-block; box-shadow: 0 15px 35px rgba(0,0,0,0.5); }
            .pit { width: 80px; height: 80px; background: #0f3460; border: 2px solid #ff9f43; border-radius: 50%; display: inline-block; margin: 15px; line-height: 76px; font-size: 26px; font-weight: bold; cursor: pointer; transition: all 0.2s ease-in-out; color: #fff; }
            .pit:hover { background: #ff9f43; transform: scale(1.1); box-shadow: 0 0 15px #ff9f43; }
            .row-pits { display: inline-block; vertical-align: middle; }
            .store { width: 100px; height: 210px; background: #ee5253; border: 3px solid #ff9f43; border-radius: 30px; display: inline-block; vertical-align: middle; line-height: 200px; font-size: 40px; font-weight: bold; margin: 0 25px; }
            .active-player { color: #10ac84; font-weight: 600; font-size: 26px; margin-bottom: 25px; min-height: 40px; text-transform: uppercase; }
            .ai-row .pit { border-color: #10ac84; cursor: not-allowed; }
            .ai-row .pit:hover { background: #0f3460; transform: none; box-shadow: none; }
        </style>
    </head>
    <body>
        <h1>TUMBA YUMBA 🌴</h1>
        <div id="status" class="active-player">Загрузка...</div>
        <div class="board">
            <div id="store2" class="store" title="Казна ИИ">0</div>
            <div class="row-pits">
                <div id="row2" class="ai-row"></div>
                <div id="row1"></div>
            </div>
            <div id="store1" class="store" title="Ваша Казна">0</div>
        </div>
        <br><button class="btn btn-lg btn-outline-warning mt-5 px-5" onclick="initGame()">Новая игра</button>
        <script>
            let state = {};
            async function initGame() {
                const res = await fetch('/new_game');
                state = await res.json();
                render();
            }
            async function move(idx) {
                if (state.current_player !== 1 || state.game_over) return;
                const res = await fetch('/make_move?pit_index=' + idx, {
                    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(state)
                });
                if(res.ok) { state = await res.json(); render(); }
                else { alert((await res.json()).detail); }
            }
            function render() {
                document.getElementById('store1').innerText = state.board.at(6);
                document.getElementById('store2').innerText = state.board.at(13);
                let r1 = "", r2 = "";
                for(let i=0; i<6; i++) {
                    r1 += '<div class="pit" onclick="move(' + i + ')">' + state.board.at(i) + '</div>';
                }
                for(let i=12; i>=7; i--) {
                    r2 += '<div class="pit">' + state.board.at(i) + '</div>';
                }
                document.getElementById('row1').innerHTML = r1;
                document.getElementById('row2').innerHTML = r2;
                if(state.game_over) {
                    if (state.winner === 1) document.getElementById('status').innerText = "🎉 Вы победили!";
                    else if (state.winner === 2) document.getElementById('status').innerText = "🤖 Победил Компьютер!";
                    else document.getElementById('status').innerText = "🤝 Ничья!";
                } else {
                    document.getElementById('status').innerText = state.current_player === 1 ? "Ваш ход 🟢" : "Ходит Компьютер... 🤖";
                }
            }
            initGame();
        </script>
    </body>
    </html>
    """
