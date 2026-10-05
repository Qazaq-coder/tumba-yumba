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

    return board, next_player, False, None

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
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()
