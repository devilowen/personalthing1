
import ctypes,json,sys,os
from pathlib import Path
from dpi_awareness import DPI_AWARE  # Must run before Tkinter is initialized
import tkinter as tk
from tkinter import ttk,messagebox
from vision import capture_board,classify,CRAB,PUFFER,JELLY
from solver import best_move,W,H

# In a PyInstaller one-file EXE, bundled resources live in sys._MEIPASS.
# Keep writable settings in the user's AppData folder, not the temporary bundle.
RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
APP_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / "BilgeOverlay"
CONFIG = APP_DIR / "config.json"
DEFAULT_CONFIG = RESOURCE_DIR / "config.json"

def load():
    APP_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG.exists():
        if DEFAULT_CONFIG.exists():
            CONFIG.write_text(DEFAULT_CONFIG.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            raise FileNotFoundError(f"Default config not found: {DEFAULT_CONFIG}")
    return json.loads(CONFIG.read_text(encoding="utf-8"))

def save(c):
    APP_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(c, indent=2), encoding="utf-8")
def pressed(vk): return bool(ctypes.windll.user32.GetAsyncKeyState(vk)&0x8000)

class App:
    def __init__(self):
        self.cfg=load(); self.running=True; self.paused=False; self.visible=True; self.keys={}; self.last=None
        self.root=tk.Tk(); self.root.title("BilgeOverlay — DPI-aware"); self.root.geometry("410x255"); self.root.resizable(False,False)
        self.status=tk.StringVar(value="Scanning…")
        if not DPI_AWARE:
            self.status.set("DPI awareness fallback active; mixed-monitor scaling may need recalibration.")
        ttk.Label(self.root,text="BilgeOverlay",font=("Segoe UI",14,"bold")).pack(pady=(10,3))
        ttk.Label(self.root,textvariable=self.status,wraplength=365).pack(pady=5)
        ttk.Label(self.root,text="DPI-aware physical-pixel coordinates").pack(pady=2)
        ttk.Label(self.root,text="F8 pause • F9 overlay • F10 settings • Esc quit").pack(pady=5)
        ttk.Button(self.root,text="Calibration / Settings",command=self.settings).pack(pady=3)
        ttk.Button(self.root,text="Quit",command=self.quit).pack(pady=3)

        self.ov=tk.Toplevel(self.root); self.ov.overrideredirect(True); self.ov.attributes("-topmost",True)
        self.canvas=tk.Canvas(self.ov,bg="#010101",highlightthickness=0); self.canvas.pack(fill="both",expand=True)
        try:self.ov.attributes("-transparentcolor","#010101")
        except tk.TclError:pass
        self.reposition(); self.root.after(60,self.hotkeys); self.root.after(180,self.scan)

    def reposition(self):
        b=self.cfg["board"]; self.ov.geometry(f'{b["width"]}x{b["height"]}+{b["x"]}+{b["y"]}')

    def draw(self,m):
        self.canvas.delete("all")
        if not self.visible or not m:return
        b=self.cfg["board"]; cw=b["width"]/W; ch=b["height"]/H
        self.canvas.create_rectangle(m.x*cw+2,m.y*ch+2,(m.x+2)*cw-2,(m.y+1)*ch-2,outline="#00ff66",width=4)
        self.canvas.create_text(7,7,anchor="nw",text=f"{m.kind.upper()}: SWAP {m.x+1}-{m.x+2} / ROW {m.y+1}",fill="white",font=("Segoe UI",10,"bold"))

    def scan(self):
        if not self.running:return
        if not self.paused:
            try:
                board,conf=classify(capture_board(self.cfg))
                water=int(self.cfg.get("water_level",3))
                if conf>=self.cfg.get("confidence_threshold",.55):
                    m=best_move(board,self.cfg.get("search_depth",2),water); self.last=m; self.draw(m)
                    self.status.set((f"{m.kind.upper()}: row {m.y+1}, cols {m.x+1}-{m.x+2} | {m.label} | "
                                     f"recognition {conf:.0%} | water {water}") if m
                                    else f"No clear found | recognition {conf:.0%}")
                else:
                    self.last=None; self.draw(None); self.status.set(f"LOW CONFIDENCE — recalibrate | {conf:.0%}")
            except Exception as e:self.status.set("Capture error: "+str(e))
        self.root.after(max(60,int(self.cfg.get("scan_interval_ms",180))),self.scan)

    def hotkeys(self):
        for vk,act in ((0x77,"pause"),(0x78,"overlay"),(0x79,"settings"),(0x1b,"quit")):
            d=pressed(vk)
            if d and not self.keys.get(vk,False):
                if act=="pause":self.paused=not self.paused
                elif act=="overlay":self.visible=not self.visible;self.draw(self.last)
                elif act=="settings":self.settings()
                else:self.quit()
            self.keys[vk]=d
        if self.running:self.root.after(60,self.hotkeys)

    def settings(self):
        w=tk.Toplevel(self.root); w.title("Calibration / Settings — physical pixels"); w.resizable(False,False)
        ttk.Label(w,text="Coordinates are physical screen pixels. If game resolution/UI scale changes, recalibrate the board rectangle.",wraplength=360).pack(padx=12,pady=(10,4))
        fields=[("Board X (physical px)","x"),("Board Y (physical px)","y"),("Board width (px)","width"),("Board height (px)","height"),
                ("Search depth 1-3","depth"),("Recognition 0-1","confidence"),("Water level 0-12","water")]
        es={}
        for label,key in fields:
            r=ttk.Frame(w);r.pack(fill="x",padx=12,pady=3);ttk.Label(r,text=label,width=21).pack(side="left")
            e=ttk.Entry(r,width=12)
            if key in ("x","y","width","height"):val=self.cfg["board"][key]
            elif key=="depth":val=self.cfg["search_depth"]
            elif key=="confidence":val=self.cfg["confidence_threshold"]
            else:val=self.cfg.get("water_level",3)
            e.insert(0,str(val));e.pack(side="right");es[key]=e
        def apply():
            try:
                for k in ("x","y","width","height"):self.cfg["board"][k]=int(es[k].get())
                self.cfg["search_depth"]=max(1,min(3,int(es["depth"].get())))
                self.cfg["confidence_threshold"]=max(0,min(1,float(es["confidence"].get())))
                self.cfg["water_level"]=max(0,min(12,int(es["water"].get())))
                save(self.cfg);self.reposition();w.destroy()
            except ValueError:messagebox.showerror("Invalid","Please enter valid numbers.")
        ttk.Button(w,text="Save",command=apply).pack(pady=8)

    def quit(self):
        self.running=False
        try:self.ov.destroy()
        except:pass
        self.root.destroy()

if __name__=="__main__":
    App().root.mainloop()
