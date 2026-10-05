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
    # Стартовая расстановка турецкой Мангалы: 6 лунок игрока по 4, казна (0), 6 лунок ИИ по 4, казна (0)
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

    game_over = False
    winner = None
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
        raise HTTPException(status_code=400, detail="Error")
    if board[pit_index] == 0:
        raise HTTPException(status_code=400, detail="Empty")

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
    <!DOCTYPE html><html><head><title>Tumba Yumba</title>
    <link href="https://jsdelivr.net" rel="stylesheet">
    <style>
        body{background:#1a1a2e;color:white;text-align:center;font-family:sans-serif;padding-top:40px;}
        h1{font-weight:700;color:#ff9f43;margin-bottom:10px;letter-spacing:2px;}
        .lang-bar{margin-bottom:20px;}
        .lang-btn{margin:0 5px;padding:5px 15px;border-radius:10px;font-weight:600;}
        .board{background:#16213e;border:4px solid #0f3460;border-radius:25px;padding:25px;display:inline-block;box-shadow:0 15px 35px rgba(0,0,0,0.5);}
        .pit{width:75px;height:75px;background:#0f3460;border:2px solid #ff9f43;border-radius:50%;display:inline-block;margin:12px;line-height:71px;font-size:24px;font-weight:bold;cursor:pointer;transition:all 0.2s ease-in-out;color:#fff;}
        .pit:hover{background:#ff9f43;transform:scale(1.1);box-shadow:0 0 15px #ff9f43;}
        .row-pits{display:inline-block;vertical-align:middle;}
        .store{width:90px;height:200px;background:#ee5253;border:3px solid #ff9f43;border-radius:25px;display:inline-block;vertical-align:middle;line-height:190px;font-size:38px;font-weight:bold;margin:0 20px;}
        .active-player{color:#10ac84;font-weight:600;font-size:24px;margin-bottom:20px;min-height:35px;text-transform:uppercase;}
        .stats-bar{font-size:18px;margin-bottom:15px;color:#c7ecee;font-weight:500;}
        .ai-row .pit{border-color:#10ac84;cursor:not-allowed;}
        .ai-row .pit:hover{background:#0f3460;transform:none;box-shadow:none;}
    </style></head><body>
    <h1>TUMBA YUMBA 🌴</h1>
    <div class="lang-bar">
        <button class="btn btn-outline-light lang-btn" onclick="setLanguage('kk')">ҚАЗ</button>
        <button class="btn btn-outline-light lang-btn" onclick="setLanguage('ru')">РУС</button>
        <button class="btn btn-outline-light lang-btn" onclick="setLanguage('en')">ENG</button>
    </div>
    <div id="stats" class="stats-bar">Ходов сделано: 0</div>
    <div id="status" class="active-player">Загрузка...</div>
    <div class="board">
        <div id="store2" class="store">0</div>
        <div class="row-pits"><div id="row2" class="ai-row"></div><div id="row1"></div></div>
        <div id="store1" class="store">0</div>
    </div><br>
    <button id="new-game-btn" class="btn btn-lg btn-outline-warning mt-4 px-5" onclick="initGame()">Новая игра</button>
    <script>
        let state={};let moveCount=0;let currentLang='ru';
        const translations={
            ru:{loading:'Загрузка...',your_turn:'Ваш ход 🟢',ai_turn:'Ходит Компьютер... 🤖',win:'🎉 Вы победили!',lose:'🤖 Победил Компьютер!',draw:'🤝 Ничья!',moves:'Ходов сделано: ',new_game:'Новая игра'},
            kk:{loading:'Жүктелуде...',your_turn:'Сіздің жүрісіңіз 🟢',ai_turn:'Компьютер жүріп жатыр... 🤖',win:'🎉 Сіз жеңдіңіз!',lose:'🤖 Компьютер жеңді!',draw:'🤝 Тең ойын!',moves:'Жасалған жүрістер: ',new_game:'Жаңа ойын'},
            en:{loading:'Loading...',your_turn:'Your turn 🟢',ai_turn:'Computer thinking... 🤖',win:'🎉 You won!',lose:'🤖 Computer won!',draw:'🤝 Draw!',moves:'Moves made: ',new_game:'New Game'}
        };
        function setLanguage(l){currentLang=l;render();}
        async function initGame(){const r=await fetch('/new_game');state=await r.json();moveCount=0;render();}
        async function move(i){
            if(state.current_player !== 1 || state.game_over)return;
            const r=await fetch('/make_move?pit_index='+i,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(state)});
            if(r.ok){state=await r.json();moveCount++;render();}
        }
        function render(){
            if(!state.board)return;const t=translations[currentLang];
            document.getElementById('stats').innerText=t.moves+moveCount;
            document.getElementById('new-game-btn').innerText=t.new_game;
            document.getElementById('store1').innerText=state.board[6];
            document.getElementById('store2').innerText=state.board[13];
            let r1='',r2='';
            for(let i=0;i<6;i++){r1+='<div class="pit" onclick="move('+i+')">'+state.board[i]+'</div>';}
            for(let i=12;i>=7;i--){r2+='<div class="pit">'+state.board[i]+'</div>';}
            document.getElementById('row1').innerHTML=r1;document.getElementById('row2').innerHTML=r2;
            if(state.game_over){
                if(state.winner===1)document.getElementById('status').innerText=t.win;
                else if(state.winner===2)document.getElementById('status').innerText=t.lose;
                else document.getElementById('status').innerText=t.draw;
            }else{document.getElementById('status').innerText=state.current_player===1?t.your_turn:t.ai_turn;}
        }
        initGame();
    </script></body></html>
    """
