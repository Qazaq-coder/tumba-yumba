from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import base64
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
    encoded_gui = (
        "PCFET0NUWVBFIGh0bWw+PGh0bWw+PGhlYWQ+PHRpdGxlPlR1bWJhIFl1bWJhPC90aXRsZT4"
        "8bGluayBocmVmPSJodHRwczovL2Nkbi5qc2RlbGl2ci5uZXQvbnBtL2Jvb3RzdHJhcEA1Lj"
        "MuMC9kaXN0L2Nzcy9ib290c3RyYXAubWluLmNzcyIgcmVsPSJzdHlsZXNoZWV0Ij48c3R5b"
        "GU+Ym9keXtiYWNrZ3JvdW5kOiMxYTFhMmU7Y29sb3I6d2hpdGU7dGV4dC1hbGlnbjpjZW50"
        "ZXI7Zm9udC1mYW1pbHk6J1NlZ29lIFVJJywgc2Fucy1zZXJpZjtwYWRkaW5nLXRvcDo1MHB"
        "4O31oMXtmb250LXdlaWdodDo3MDA7Y29sb3I6I2ZmOWY0MzttYXJnaW4tYm90dG9tOjEwcH"
        "g7bGV0dGVyLXNwYWNpbmc6MnB4O30ubGFuZy1iYXJ7bWFyZ2luLWJvdHRvbToyNXB4O30ub"
        "GFuZy1idG57bWFyZ2luOjAgNXB4O3BhZGRpbmc6NXB4IDE1cHg7Ym9yZGVyLXJhZGl1czox"
        "MHB4O2ZvbnQtd2VpZ2h0OjYwMDt9LmJvYXJke2JhY2tncm91bmQ6IzE2MjEzZTtib3JkZXI"
        "6NHB4IHNvbGlkICMwZjM0NjA7Ym9yZGVyLXJhZGl1czoyNXB4O3BhZGRpbmc6MzBweDtkaX"
        "NwbGF5OmlubGluZS1ibG9jaztib3gtc2hhZG93OjAgMTVweCAzNXB4IHJnYmEoMCwwLDAsM"
        "C41KTt9LnBpdHt3aWR0aDo4MHB4O2hlaWdodDo4MHB4O2JhY2tncm91bmQ6IzBmMzQ2MDti"
        "b3JkZXI6MnB4IHNvbGlkICNmZjlmNDM7Ym9yZGVyLXJhZGl1czo1MCU7ZGlzcGxheTppbmx"
        "pbmUtYm9sb2NrO21hcmdpbjoxNXB4O2xpbmUtaGVpZ2h0Ojc2cHg7Zm9udC1zaXplOjI2cH"
        "g7Zm9udC13ZWlnaHQ6Ym9sZDtjdXJzb3I6cG9pbnRlcjt0cmFuc2l0aW9uOmFsbCAwLjJzI"
        "GVhc2UtaW4tb3V0O2NvbG9yOiNmZmY7fS5waXQ6aG92ZXtiYWNrZ3JvdW5kOiNmZjlmNDM7"
        "dHJhbnNmb3JtOnNjYWxlKDEuMSk7Ym94LXNoYWRvdzowIDAgMTVweCAjZmY5ZjQzO30ucm9"
        "3LXBpdHN7ZGlzcGxheTppbmxpbmUtYm9sb2NrO3ZlcnRpY2FsLWFsaWduOm1pZGRsZTt9Ln"
        "N0b3Jle3dpZHRoOjEwMHB4O2hlaWdodDoyMTBweDtiYWNrZ3JvdW5kOiNlZTUyNTM7Ym9yZ"
        "GVyOjNweCBzb2xpZCAjZmY5ZjQzO2JvcmRlci1yYWRpdXM6MzBweDtkaXNwbGF5OmlubGlu"
        "ZS1ibG9jazt2ZXJ0aWNhbC1hbGlnbjptaWRkbGU7bGluZS1oZWlnaHQ6MjAwcHg7Zm9udC1"
        "zaXplOjQwcHg7Zm9udC13ZWlnaHQ6Ym9sZDttYXJnaW46MCAyNXB4O30uYWN0aXZlLXBsYX"
        "llcntjb2xvcjojMTBhYzg0O2ZvbnQtd2VpZ2h0OjYwMDtmb250LXNpemU6MjZweDttYXJna"
        "W4tYm90dG9tOjI1cHg7bWluLWhlaWdodDo0MHB4O3RleHQtdHJhbnNmb3JtOnVwcGVyY2Fz"
        "ZTt9LnN0YXRzLWJhcntmb250LXNpemU6MThweDttYXJnaW4tYm90dG9tOjIwcHg7Y29sb3I"
        "6I2M3ZWNlZTtmb250LXdlaWdodDo1MDA7fS5haS1yb3cgLnBpdHtib3JkZXItY29sb3I6Iz"
        "EwYWM4NDtjdXJzb3I6bm90LWFsbG93ZWQ7fS5haS1yb3cgLnBpdDpob3ZlcntiYWNrZ3Jvd"
        "W5kOiMwZjM0NjA7dHJhbnNmb3JtOm5vbmU7Ym94LXNoYWRvdzpub25lO308L3N0eWxlPjwv"
        "aGVhZD48Ym9keT48aDE+VFVNQkEgWVU1QkEgX2MxX2YzMzQ8L2gxPjxkaXYgY2xhc3M9Imx"
        "hbmctYmFyIj48YnV0dG9uIGNsYXNzPSJidG4gYnRuLW91dGxpbmUtbGlnaHQgbGFuZy1idG"
        "4iIG9uY2xpayM0bWFya2VyPSJzZXRMYW5ndWFnZSgna2snKSI+XHUwNDlhXHUwNDF4XHUwN"
        "DF4PC9idXR0b24+PGJ1dHRvbiBjbGFzcz0iYnRuIGJ0bi1vdXRsaW5lLWxpZ2h0IGxhbmct"
        "YnRuIiBvbmNsaWNrPSJzZXRMYW5ndWFnZSgncnUnKSI+XHUwNDJ4XHUwNDJ4XHUwNDF4PC9"
        "idXR0b24+PGJ1dHRvbiBjbGFzcz0iYnRuIGJ0bi1vdXRsaW5lLWxpZ2h0IGxhbmctYnRuIi"
        "BvbmNsaWNrPSJzZXRMYW5ndWFnZSgnZW4nKSI+RU5HPC9idXR0b24+PC9kaXY+PGRpdiBpZ"
        "D0ic3RhdHMiIGNsYXNzPSJzdGF0cy1iYXIiPlhodW9vdiBza2VsYW5vOiAwPC9kaXY+PGRp"
        "diBpZD0ic3RhdHVzIiBjbGFzcz0iYWN0aXZlLXBsYXllciI+WmFncnV6a2EuLi48L2Rpdj4"
        "8ZGl2IGNsYXNzPSJib2FyZCI+PGRpdiBpZD0ic3RvcmUyIiBjbGFzcz0ic3RvcmUiPjA8L2"
        "Rpdj48ZGl2IGNsYXNzPSJyb3ctcGl0cyI+PGRpdiBpZD0icm93MiIgY2xhc3M9ImFpLXJvd"
        "yI+PC9kaXY+PGRpdiBpZD0icm93MSI+PC9kaXY+PC9kaXY+PGRpdiBpZD0ic3RvcmUxIiBj"
        "bGFzcz0ic3RvcmUiPjA8L2Rpdj48L2Rpdj48YnI+PGJ1dHRvbiBpZD0ibmV3LWdhbWUtYnR"
        "uIiBjbGFzcz0iYnRuIGJ0bi1sZyBidG4tb3V0bGluZS13YXJuaW5nIG10LTUgcHgtNSIgb2"
        "5jbGljaz0iaW5pdEdhbWUoKSI+Tm92YXlhIG95dW48L2J1dHRvbj48c2NyaXB0PmxldCBzd"
        "GF0ZT17fTtsZXQgbW92ZUNvdW50PTA7bGV0IGN1cnJlbnRMYW5nPSHydSc7Y29uc3QgdHJh"
        "bnNsYXRpb25zPXtydTp7bG9hZGluZzonXHUwNDI3XHUwNDMxXHUwNDM3XHUwNDM0XHUwNDM"
        "3XHUwNDM3XHUwNDNhXHUwNDMwLi4uJyx5b3VyX3R1cm46J1x1MDQxMlx1MDQzMFx1MDQzOF"
        "x1MDQ0YiBcdTA0NDRcdTA0M2VcdTA0MzQgX2QxX2YzMzInLGFpX3R1cm46J1x1MDQyN1x1M"
        "DQzZFx1MDQzNFx1MDQzOFx1MDQ0MiBcdTA0MTZcdTAwNm9cdTAwNm1cdTAwNnBcdTAwN2Nc"
        "dTAwNzVcdTAwNzRcdTAwNjVcdTAwNzIuLi4gX2UxX2YzMzYnLHdpbignX2MxX2YzODkgXHU"
        "wNDExXHUwNDRiIFx1MDQzZlx1MDQzZVx1MDQzMlx1MDQzNVx1MDQzNFx1MDQzOFx1MDQzYlx"
        "1MDQzOCEnKSxsb3NlKCdcdTBlMTZcdTAwNmZcdTAwNm1cdTAwNnBcdTAwN2NcdTAwNzVcdT"
        "AwNzRcdTAwNjVcdTAwNzIgXHUwNDExXHUwNDRiIFx1MDQzZlx1MDQzZVx1MDQzMlx1MDQzN"
        "Fx1MDQzOFx1MDQzYlx1MDQzZCEnKSxkcmF3KCdcdTBlMWRcdTAwNmZcdTAwNm1cdTAwNnBc"
        "dTAwN2NcdTAwNzVcdTAwNzRcdTAwNjVcdTAwNzIgXHUwNDFkXHUwNDM4XHUwNDQ3XHUwNDR"
        "jXHUwNDRmIScpLG1vdmVzOidcdTA0MjdcdTAwNmZcdTAwNm1cdTAwNnBcdTAwN2NcdTAwNz"
        "VcdTAwNzRcdTAwNjVcdTAwNzIgXHUwNDQzXHUwNDM0XHUwNDM1XHUwNDNiXHUwNDMwXHUwN"
        "TMwXHUwNTNlOiAnLG5ld19nYW1lOidcdTA0MWRcdTAwNmZcdTAwNm1cdTAwNnBcdTAwN2Nc"
        "dTAwNzVcdTAwNzRcdTAwNjVcdTAwNzIgXHUwNDNlXHUwNDM5XHUwNDM0XHUwNDNlXHUwNDN"
        "lXHUwNDNkIn0sa2s6e2xvYWRpbmc6J1x1MDQxNlx1MDQ0Mlx1MDQzY1x1MDQ0Mlx1MDQzNV"
        "x1MDQzYlx1MDQ0Mlx1MDQzNWRlLi4uJyx5b3VyX3R1cm46J1x1MDQyM1x1MDQzNlx1MDQzN"
        "Fx1MDQ0Mlx1MDQzNWxcdTA0MzVcdTAwNmZcdTAwNm1cdTAwNnBcdTAwN2NcdTAwNzVcdTAw"
        "NzRcdTAwNjVcdTAwNzIgXHUwNDM2XHUwNDNlXHUwNDM1XHUwNDM0XHUwNDM1bFx1MDQzNWx"
        "cdTA0MzUgX2QxX2YzMzInLGFpX3R1cm46J1x1MDQxNlx1MDQzZlx1MDQzZVx1MDQzMlx1MD"
        "QzNVx1MDQzNFx1MDQzOFx1MDQzYlx1MDQzOCBcdTA0MzZcdTAwNmYcdTAwNm1cdTAwNnBcd"
        "TAwN2NcdTAwNzVcdTAwNzRcdTAwNjVcdTAwNzIgXHUwNDM2XHUwNDMwXHUwNDQyXHUwNDM5"
        "cl9kZSAuLi4gX2UxX2YzMzYnLHdpbignX2MxX2YzODkgXHUwNDIzXHUwNDM2XHUwNDM0XHU"
        "wNDQyXHUwNDM1bFx1MDQzNWwgXHUwNDM2XHUwNDM1XHUwNDNkXHUwNDM0XHUwNDM1bFx1MD"
        "QzNWxcdTA0MzUhJyksbG9zZShcdTA0MTVcdTAwNmYcdTAwNm1cdTAwNnBcdTAwN2NcdTAw"
        "NzVcdTAwNzRcdTAwNjVcdTAwNzIgXHUwNDM2XHUwNDM1XHUwNDNkXHUwNDM0XHUwNDM1bFx"
        "1MDQzNWxcdTA0MzUhJyksZHJhdygnX2UxX2YzMWQgXHUwNDIyXHUwNDM1XHUwNDNkXHUwMD"
        "ZmXHUwMDZtXHUwMDYwXHUwMDY0XHUwMDY1XHUwMDcyIFx1MDQzZlx1MDQzZVx1MDQzMlx1"
        "MDQzNVx1MDQzNFx1MDQzOFx1MDQzYlx1MDQzOCEnKSxtb3ZlczonXHUwNDE2XHUwNDMwXHU"
