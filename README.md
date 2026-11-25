# keystrokes-app

Small Windows overlay that shows the keys you press (including combos like `Ctrl + Shift + T`) as keycaps on screen. Useful for presentations, screen recordings, or checking key combos on a 60% keyboard.

## Run

```
pip install pynput
python keys.py
```

Close it with `Ctrl+C` in the terminal.

## Configure

Edit the constants at the top of `keys.py`:

- `SCALE`: overall size
- `SIDE`: `"left"`, `"center"` or `"right"`
- `MAX` / `LIFE`: number of visible rows / seconds until a key fades out
- `BG`, `CAP`, `EDGE`, `FG`: colors
