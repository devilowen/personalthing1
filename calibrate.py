import json, tkinter as tk
from tkinter import messagebox
from pathlib import Path
P=Path(__file__).resolve().parent/"config.json"
c=json.loads(P.read_text()); b=c["board"]
root=tk.Tk(); root.title("BilgeOverlay calibration"); root.geometry("380x250"); root.resizable(False,False)
es={}
for label,key in (("Top-left X","x"),("Top-left Y","y"),("Board width","width"),("Board height","height")):
    r=tk.Frame(root); r.pack(fill="x",padx=18,pady=7)
    tk.Label(r,text=label,width=18,anchor="w").pack(side="left")
    e=tk.Entry(r,width=12); e.insert(0,str(b[key])); e.pack(side="right"); es[key]=e
tk.Label(root,text="Measure the entire 6 × 12 puzzle grid.").pack(pady=6)
def go():
    try:
        for k in b:b[k]=int(es[k].get())
        P.write_text(json.dumps(c,indent=2)); messagebox.showinfo("Saved","Calibration saved."); root.destroy()
    except ValueError: messagebox.showerror("Error","Use whole numbers.")
tk.Button(root,text="Save",command=go).pack(pady=8)
root.mainloop()
