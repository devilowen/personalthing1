
from dataclasses import dataclass

W, H = 6, 12
UNKNOWN = -2
CRAB = -10
PUFFER = -11
JELLY = -12

@dataclass
class Move:
    x: int
    y: int
    score: float
    label: str
    kind: str = "normal"

def clone(board):
    return [row[:] for row in board]

def swap(board, x, y):
    b = clone(board)
    b[y][x], b[y][x+1] = b[y][x+1], b[y][x]
    return b

def find_clears(board):
    clear = set()
    for y in range(H):
        x = 0
        while x < W:
            v = board[y][x]
            if v < 0:
                x += 1; continue
            e = x + 1
            while e < W and board[y][e] == v: e += 1
            if e-x >= 3:
                clear.update((xx,y) for xx in range(x,e))
            x = e
    for x in range(W):
        y = 0
        while y < H:
            v = board[y][x]
            if v < 0:
                y += 1; continue
            e = y + 1
            while e < H and board[e][x] == v: e += 1
            if e-y >= 3:
                clear.update((x,yy) for yy in range(y,e))
            y = e
    return clear

def shape_score(clear):
    if not clear: return 0.0
    rows, cols = {}, {}
    for x,y in clear:
        rows[y] = rows.get(y,0)+1
        cols[x] = cols.get(x,0)+1
    n = len(clear)
    long_runs = sum(max(0,v-3) for v in rows.values()) + sum(max(0,v-3) for v in cols.values())
    lines = sum(v>=3 for v in rows.values()) + sum(v>=3 for v in cols.values())
    return n*5.0 + long_runs*5.0 + max(0,lines-1)*22.0

def collapse(board, clear):
    b = clone(board)
    for x in range(W):
        kept = [b[y][x] for y in range(H) if (x,y) not in clear]
        bcol = [UNKNOWN]*(H-len(kept)) + kept
        for y in range(H): b[y][x] = bcol[y]
    return b

def normal_move(board,x,y):
    if not (0<=x<W-1 and 0<=y<H): return board,-1e9,0,"invalid"
    if board[y][x] < 0 or board[y][x+1] < 0: return board,-1e9,0,"invalid"
    b=swap(board,x,y)
    clear=find_clears(b)
    if not clear: return b,-4.0,0,"setup"
    return collapse(b,clear),shape_score(clear),len(clear),"combo"

def puffer_move(board,x,y):
    # A puffer activates when clicked/used; the exact UI action is represented
    # as the swap position in this suggestion engine.
    p = None
    for xx in (x,x+1):
        if board[y][xx] == PUFFER:
            p=(xx,y); break
    if p is None: return None
    px,py=p
    clear={(xx,yy) for yy in range(max(0,py-1),min(H,py+2))
                    for xx in range(max(0,px-1),min(W,px+2))}
    # Adjacent crabs can be destroyed, but their bonus is not awarded by puffer.
    return collapse(board,clear), len(clear)*2.2, len(clear)

def jelly_move(board,x,y):
    a,b=board[y][x],board[y][x+1]
    if a != JELLY and b != JELLY: return None
    color = b if a == JELLY else a
    if color < 0: return None
    clear={(xx,yy) for yy in range(H) for xx in range(W) if board[yy][xx] == color}
    return collapse(board,clear), len(clear)*4.0, len(clear)

def crab_bonus(board,clear,water_level):
    crabs=0
    for x,y in clear:
        if board[y][x] == CRAB: crabs += 1
    # Crab bonus increases sharply as the water approaches the crab.
    return crabs * (18.0 + max(0,min(1,water_level/9.0))*55.0)

def evaluate(board,x,y,water_level=3):
    a,b=board[y][x],board[y][x+1]

    jm=jelly_move(board,x,y)
    if jm:
        nb,score,n=jm
        return nb, score + crab_bonus(board,{(xx,yy) for yy in range(H) for xx in range(W)
                                              if board[yy][xx] == (b if a==JELLY else a)},water_level),n,"jellyfish"

    # Puffer is especially valuable when it is likely to free crabs by moving columns.
    if a==PUFFER or b==PUFFER:
        pm=puffer_move(board,x,y)
        if pm:
            nb,score,n=pm
            return nb, score + (water_level*3.0), n, "puffer"

    nb,score,n,kind=normal_move(board,x,y)
    if score < -1e8: return nb,score,n,kind
    clear=find_clears(swap(board,x,y))
    score += crab_bonus(swap(board,x,y),clear,water_level)
    return nb,score,n,kind

def search(board,depth,water_level,memo):
    if depth<=0: return 0.0,None,""
    key=(tuple(tuple(r) for r in board),depth,water_level)
    if key in memo: return memo[key]
    best=(-1e18,None,"")
    for y in range(H):
        for x in range(W-1):
            nb,immediate,n,kind=evaluate(board,x,y,water_level)
            if immediate < -1e8: continue
            value=immediate
            if depth>1 and n:
                future,_,_=search(nb,depth-1,water_level,memo)
                value += future*0.60
            # Prefer bottom clears when otherwise similar, because upper
            # pieces are less disturbed by a lower clear.
            value += (H-y)*0.08 if n else 0
            if value>best[0]: best=(value,(x,y),kind)
    memo[key]=best
    return best

def best_move(board,depth=2,water_level=3):
    score,pos,kind=search(board,max(1,min(3,int(depth))),water_level,{})
    if pos is None: return None
    x,y=pos
    _,immediate,n,_=evaluate(board,x,y,water_level)
    if kind=="jellyfish":
        label=f"JELLY • clear {n} matching pieces"
    elif kind=="puffer":
        label=f"PUFFER • clear 3×3 area ({n} cells)"
    elif n:
        label=f"{immediate:.0f} score • {n} cells"
    else:
        label="setup / low confidence"
    return Move(x,y,score,label,kind)
