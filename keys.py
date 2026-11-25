"""Show pressed key combos as keycaps in a click-through overlay (Windows). Run: python keys.py"""
import ctypes, queue, time, tkinter as tk, tkinter.font as tkf
from pynput import keyboard

MAX, LIFE = 4, 2  # rows shown, seconds until a key fully fades
MODS = {"ctrl": "Ctrl", "shift": "Shift", "alt": "Alt", "cmd": "Win", "alt_gr": "AltGr"}
BG, TRANS = "#161616", "#010101"  # panel color, color keyed out as transparent
CAP, EDGE, FG = "#454545", "#222222", "#ffffff"  # keycap face, keycap edge, text (all fade toward BG)
SCALE = 1.5  # overall size: 0.8 smaller, 1.5 bigger
SIDE = "left"  # screen side: "left", "center" or "right"
s = lambda v: int(v * SCALE)
CAP_H, GAP, PAD, W = s(44), s(14), s(14), s(560)
H = MAX * (CAP_H + GAP) + PAD
q, held = queue.Queue(), []  # held: modifiers currently down, in press order


def mod_of(key):  # ctrl_l -> "ctrl"
    name = getattr(key, "name", "") or ""
    base = name.rsplit("_", 1)[0] if name.endswith(("_l", "_r")) else name
    return base if base in MODS else None


def label(key):
    if isinstance(key, keyboard.KeyCode):
        vk = key.vk or 0
        if 65 <= vk <= 90 or 48 <= vk <= 57:  # stable under Ctrl (char becomes control code)
            return chr(vk)
        return (key.char or f"vk{vk}").upper()
    return key.name.replace("_", " ").title()


def on_press(key):
    m = mod_of(key)
    if m:
        if m not in held:
            held.append(m)
        q.put([MODS[x] for x in held])
    else:
        q.put([MODS[x] for x in held] + [label(key)])


def on_release(key):
    m = mod_of(key)
    if m in held:
        held.remove(m)


root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True, "-transparentcolor", TRANS)
c = tk.Canvas(root, width=W, height=H, bg=TRANS, highlightthickness=0)
c.pack()
font = tkf.Font(family="Segoe UI", size=s(14), weight="bold")
sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
wx = {"left": 20, "center": (sw - W) // 2, "right": sw - W - 20}[SIDE]
root.geometry(f"{W}x{H}+{wx}+{sh - H - 60}")
root.withdraw()

# click-through: WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW
root.update()
hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
ex = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
ctypes.windll.user32.SetWindowLongW(hwnd, -20, ex | 0x80000 | 0x20 | 0x80)

ents = []  # {"parts": [...], "t": press time, "y": animated top of the row}


def blend(col, f):  # col faded toward the panel color; f=1 full, 0 invisible
    a, b = [[int(x[i:i + 2], 16) for i in (1, 3, 5)] for x in (col, BG)]
    return "#%02x%02x%02x" % tuple(int(q_ + (p - q_) * f) for p, q_ in zip(a, b))


def rr(x1, y1, x2, y2, r, **kw):  # rounded rectangle
    p = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2, x2 - r, y2,
         x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    c.create_polygon(p, smooth=True, **kw)


def poll():
    now = time.time()
    step, bottom = CAP_H + GAP, H - 4
    while not q.empty():
        ents.append({"parts": q.get(), "t": now, "y": None})
    del ents[:-MAX]
    ents[:] = [e for e in ents if now - e["t"] < LIFE]
    if not ents:
        root.withdraw()
        root.after(30, poll)
        return
    sp = s(8)  # space between keys of one combo
    widths = [[max(CAP_H + s(4), font.measure(p) + s(26)) for p in e["parts"]] for e in ents]
    rowsw = [sum(w) + sp * (len(w) - 1) for w in widths]
    for rank, e in enumerate(reversed(ents)):  # rank 0 = newest, sits on the bottom row
        slot = bottom - PAD - CAP_H - rank * step
        e["y"] = slot + s(12) if e["y"] is None else e["y"] + (slot - e["y"]) * 0.35  # rises into place
    pw_ = max(rowsw) + 2 * PAD  # panel width
    px = {"left": 4, "center": (W - pw_) // 2, "right": W - 4 - pw_}[SIDE]
    c.delete("all")
    rr(px, min(e["y"] for e in ents) - PAD, px + pw_, bottom, s(16), fill=BG)
    for rank, (e, w, rw) in enumerate(zip(reversed(ents), reversed(widths), reversed(rowsw))):
        f = max(0.0, min(1 - (now - e["t"]) / LIFE, 1 - 0.2 * rank))
        x = {"left": px + PAD, "center": px + (pw_ - rw) // 2, "right": px + pw_ - PAD - rw}[SIDE]
        y = e["y"]
        for part, pw in zip(e["parts"], w):
            rr(x, y, x + pw, y + CAP_H, s(10), fill=blend(EDGE, f))  # edge gives the keycap depth
            rr(x + s(3), y + s(2), x + pw - s(3), y + CAP_H - s(6), s(8), fill=blend(CAP, f))
            c.create_text(x + pw / 2, y + (CAP_H - s(4)) / 2, text=part, font=font, fill=blend(FG, f))
            x += pw + sp
    root.deiconify()
    root.after(30, poll)


keyboard.Listener(on_press=on_press, on_release=on_release).start()
poll()
root.mainloop()
