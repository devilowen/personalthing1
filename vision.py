
from dpi_awareness import DPI_AWARE  # set Windows DPI mode before Pillow captures
from PIL import ImageGrab
import colorsys, math

W,H=6,12
UNKNOWN=-2
CRAB=-10
PUFFER=-11
JELLY=-12

def hsv(rgb):
    r,g,b=[v/255.0 for v in rgb]
    return colorsys.rgb_to_hsv(r,g,b)

def capture_board(cfg):
    b=cfg["board"]
    # With per-monitor DPI awareness enabled, bbox coordinates are physical pixels.
    # all_screens=True permits rectangles on secondary monitors / negative X offsets.
    bbox=(int(b["x"]),int(b["y"]),int(b["x"]+b["width"]),int(b["y"]+b["height"]))
    img=ImageGrab.grab(bbox=bbox, all_screens=True)
    if img.width != int(b["width"]) or img.height != int(b["height"]):
        raise RuntimeError(
            f"Capture size mismatch ({img.width}x{img.height}); expected "
            f"{b['width']}x{b['height']}. Recheck physical-pixel board settings."
        )
    return img

def cell_features(crop,x,y,cw,ch):
    cx,cy=int((x+.5)*cw),int((y+.5)*ch)
    pts=[]
    for fx,fy in ((0,0),(-.18,0),(.18,0),(0,-.18),(0,.18),(-.18,-.18),(.18,.18)):
        px=crop.getpixel((int(cx+fx*cw),int(cy+fy*ch)))[:3]
        pts.append(px)
    avg=tuple(sum(p[i] for p in pts)//len(pts) for i in range(3))
    h,s,v=hsv(avg)
    # Center-versus-edge contrast is useful for round special pieces.
    center=crop.getpixel((cx,cy))[:3]
    edge=crop.getpixel((int(x*cw+cw*.15),int(y*ch+ch*.15)))[:3]
    contrast=sum(abs(center[i]-edge[i]) for i in range(3))/765.0
    return avg,(h,s,v),contrast

def classify(crop):
    cw,ch=crop.width/W,crop.height/H
    raw=[]
    for y in range(H):
        for x in range(W):
            raw.append(cell_features(crop,x,y,cw,ch))

    feats=[r[1] for r in raw]
    candidates=[f for f in feats if f[1]>.20 and f[2]>.18]
    if not candidates:
        return [[UNKNOWN]*W for _ in range(H)],0.0

    centers=[]
    for f in candidates:
        if all(min(abs(f[0]-c[0]),1-abs(f[0]-c[0]))+abs(f[1]-c[1])>.16 for c in centers):
            centers.append(f)
        if len(centers)>=6: break
    while len(centers)<min(6,len(candidates)):
        centers.append(candidates[len(centers)])

    for _ in range(7):
        groups=[[] for _ in centers]
        for f in feats:
            ds=[min(abs(f[0]-c[0]),1-abs(f[0]-c[0]))*2+abs(f[1]-c[1])+.25*abs(f[2]-c[2]) for c in centers]
            groups[ds.index(min(ds))].append(f)
        centers=[tuple(sum(p[k] for p in g)/len(g) for k in range(3)) if g else centers[i]
                 for i,g in enumerate(groups)]

    board=[]; confs=[]
    for i,(rgb,f,contrast) in enumerate(raw):
        ds=[min(abs(f[0]-c[0]),1-abs(f[0]-c[0]))*2+abs(f[1]-c[1])+.25*abs(f[2]-c[2]) for c in centers]
        d=min(ds); idx=ds.index(d)
        conf=max(0,min(1,1-d/.75))

        # Special-piece heuristics. These are deliberately conservative.
        r,g,b=rgb
        special=None
        # Jellyfish tend to have a bright/high-contrast cyan/purple/white core.
        if contrast>.16 and ((b>r*1.25 and b>g*1.05) or (r>g*1.25 and b>g*1.10)):
            special=JELLY
        # Pufferfish tend to be warm/orange and highly contrasted.
        if contrast>.20 and r>g*1.15 and g>b*1.15 and r>110:
            special=PUFFER
        # Crabs are commonly red/brown and visually more uniform.
        if s_gt := (f[1]>.25 and r>g*1.35 and r>b*1.25 and contrast<.18):
            special=CRAB

        if special is not None and conf>.28:
            val=special
        elif f[1]>=.18 and conf>=.30:
            val=idx
        else:
            val=UNKNOWN
        board.append(val); confs.append(conf)

    return [board[y*W:(y+1)*W] for y in range(H)],sum(confs)/len(confs)
