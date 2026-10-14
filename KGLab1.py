import random
import tkinter as tk
from tkinter import ttk, colorchooser, messagebox


def rgb_to_cmyk(r, g, b):

    r, g, b = r / 255.0, g / 255.0, b / 255.0
    k = 1.0 - max(r, g, b)
    if k >= 1.0:
        return 0.0, 0.0, 0.0, 100.0
    c = (1.0 - r - k) / (1.0 - k)
    m = (1.0 - g - k) / (1.0 - k)
    y = (1.0 - b - k) / (1.0 - k)
    return c * 100.0, m * 100.0, y * 100.0, k * 100.0


def cmyk_to_rgb(c, m, y, k):

    c, m, y, k = c / 100.0, m / 100.0, y / 100.0, k / 100.0
    r = 255.0 * (1.0 - c) * (1.0 - k)
    g = 255.0 * (1.0 - m) * (1.0 - k)
    b = 255.0 * (1.0 - y) * (1.0 - k)
    return r, g, b


def rgb_to_hsv(r, g, b):

    r, g, b = r / 255.0, g / 255.0, b / 255.0
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    v = mx
    s = 0.0 if mx == 0 else d / mx
    if d == 0:
        h = 0.0                                   
    elif mx == r:
        h = 60.0 * (((g - b) / d) % 6)
    elif mx == g:
        h = 60.0 * ((b - r) / d + 2)
    else:
        h = 60.0 * ((r - g) / d + 4)
    return h % 360.0, s * 100.0, v * 100.0


def hsv_to_rgb(h, s, v):
  
    s, v = s / 100.0, v / 100.0
    h = h % 360.0
    c = v * s                               
    x = c * (1 - abs((h / 60.0) % 2 - 1))
    m = v - c
    sector = int(h // 60) % 6
    r, g, b = [(c, x, 0), (x, c, 0), (0, c, x),
               (0, x, c), (x, 0, c), (c, 0, x)][sector]
    return (r + m) * 255.0, (g + m) * 255.0, (b + m) * 255.0


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def to_hex(r, g, b):
    return "#%02x%02x%02x" % (round(clamp(r, 0, 255)),
                              round(clamp(g, 0, 255)),
                              round(clamp(b, 0, 255)))



MODELS = {
    "RGB": [("R", 0, 255, "Красный"), ("G", 0, 255, "Зелёный"), ("B", 0, 255, "Синий")],
    "CMYK": [("C", 0, 100, "Cyan, %"), ("M", 0, 100, "Magenta, %"),
             ("Y", 0, 100, "Yellow, %"), ("K", 0, 100, "Key (чёрный), %")],
    "HSV": [("H", 0, 360, "Оттенок, °"), ("S", 0, 100, "Насыщенность, %"),
            ("V", 0, 100, "Яркость, %")],
}
MODEL_TITLES = {"RGB": "RGB (аддитивная)", "CMYK": "CMYK (субтрактивная)",
                "HSV": "HSV (Hue, Saturation, Value)"}

SV_SIZE = 220         
HUE_W = 24            


class ColorApp:
    def __init__(self, root):
        self.root = root
        root.title("Лабораторная работа №1 — Цветовые модели (CMYK – RGB – HSV)")
        root.resizable(False, False)

        # Текущее состояние: значения во всех трёх моделях
        self.rgb = (0.0, 0.0, 0.0)
        self.cmyk = (0.0, 0.0, 0.0, 100.0)
        self.hsv = (0.0, 0.0, 0.0)

        self.vars = {}        # model -> [StringVar]
        self.scales = {}      # model -> [ttk.Scale]
        self.entries = {}     # model -> [ttk.Entry]
        self._lock = False    # защита от рекурсивных обновлений
        self._last_hue = None

        self._build_ui()
        self.update_from("rgb", (52, 152, 219))   # стартовый цвет

    def _build_ui(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Err.TEntry", fieldbackground="#ffd6d6")

        main = ttk.Frame(self.root, padding=10)
        main.grid(row=0, column=0)

        left = ttk.LabelFrame(main, text="Палитра", padding=8)
        left.grid(row=0, column=0, sticky="n", padx=(0, 10))

        self.sv_canvas = tk.Canvas(left, width=SV_SIZE, height=SV_SIZE,
                                   highlightthickness=1, highlightbackground="#888",
                                   cursor="crosshair")
        self.sv_canvas.grid(row=0, column=0)
        self.sv_img_item = self.sv_canvas.create_image(0, 0, anchor="nw")
        self.sv_marker = self.sv_canvas.create_oval(0, 0, 0, 0, outline="white", width=2)
        self.sv_marker2 = self.sv_canvas.create_oval(0, 0, 0, 0, outline="black", width=1)

        self.hue_canvas = tk.Canvas(left, width=HUE_W, height=SV_SIZE,
                                    highlightthickness=1, highlightbackground="#888",
                                    cursor="sb_v_double_arrow")
        self.hue_canvas.grid(row=0, column=1, padx=(8, 0))
        self._draw_hue_strip()
        self.hue_marker = self.hue_canvas.create_rectangle(0, 0, HUE_W, 0,
                                                           outline="black", width=2)

        self.sv_canvas.bind("<Button-1>", self._on_sv)
        self.sv_canvas.bind("<B1-Motion>", self._on_sv)
        self.hue_canvas.bind("<Button-1>", self._on_hue)
        self.hue_canvas.bind("<B1-Motion>", self._on_hue)

        ttk.Label(left, text="Квадрат: S (→) и V (↑); полоса справа: H",
                  foreground="#666").grid(row=1, column=0, columnspan=2, pady=(4, 8))

        self.preview = tk.Canvas(left, width=SV_SIZE + HUE_W + 8, height=60,
                                 highlightthickness=1, highlightbackground="#888")
        self.preview.grid(row=2, column=0, columnspan=2)
        self.preview_rect = self.preview.create_rectangle(0, 0, 400, 80, width=0)

        hexrow = ttk.Frame(left)
        hexrow.grid(row=3, column=0, columnspan=2, pady=(8, 0), sticky="we")
        ttk.Label(hexrow, text="HEX:").pack(side="left")
        self.hex_var = tk.StringVar()
        self.hex_entry = ttk.Entry(hexrow, textvariable=self.hex_var, width=10)
        self.hex_entry.pack(side="left", padx=4)
        self.hex_entry.bind("<Return>", self._on_hex)
        self.hex_entry.bind("<FocusOut>", self._on_hex)

        btns = ttk.Frame(left)
        btns.grid(row=4, column=0, columnspan=2, pady=(8, 0), sticky="we")
        ttk.Button(btns, text="Системная палитра…", command=self._system_picker).pack(fill="x")
        ttk.Button(btns, text="Случайный цвет", command=self._random).pack(fill="x", pady=(4, 0))

        right = ttk.Frame(main)
        right.grid(row=0, column=1, sticky="n")
        for model in ("RGB", "CMYK", "HSV"):
            self._build_model_frame(right, model)

        self.status = tk.StringVar(value="")
        ttk.Label(main, textvariable=self.status, foreground="#a33",
                  wraplength=700).grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))

    def _build_model_frame(self, parent, model):
        frame = ttk.LabelFrame(parent, text=MODEL_TITLES[model], padding=8)
        frame.pack(fill="x", pady=(0, 8))
        self.vars[model], self.scales[model], self.entries[model] = [], [], []

        for i, (name, lo, hi, hint) in enumerate(MODELS[model]):
            ttk.Label(frame, text=name, width=2, font=("TkDefaultFont", 10, "bold")
                      ).grid(row=i, column=0, sticky="w")
            sc = ttk.Scale(frame, from_=lo, to=hi, orient="horizontal", length=300,
                           command=lambda v, m=model, k=i: self._on_scale(m, k, v))
            sc.grid(row=i, column=1, padx=6, pady=2)
            var = tk.StringVar()
            en = ttk.Entry(frame, textvariable=var, width=8, justify="right")
            en.grid(row=i, column=2)
            en.bind("<Return>", lambda e, m=model, k=i: self._on_entry(m, k))
            en.bind("<FocusOut>", lambda e, m=model, k=i: self._on_entry(m, k))
            ttk.Label(frame, text=hint, foreground="#666", width=18
                      ).grid(row=i, column=3, sticky="w", padx=(6, 0))
            self.scales[model].append(sc)
            self.vars[model].append(var)
            self.entries[model].append(en)

    def _draw_hue_strip(self):
        for y in range(SV_SIZE):
            h = 360.0 * y / (SV_SIZE - 1)
            self.hue_canvas.create_line(0, y, HUE_W, y, fill=to_hex(*hsv_to_rgb(h, 100, 100)))

    def _draw_sv_square(self, hue):
        n = SV_SIZE // 2
        rows = []
        for j in range(n):                       # сверху вниз: V от 100 до 0
            v = 100.0 * (1 - j / (n - 1))
            row = [to_hex(*hsv_to_rgb(hue, 100.0 * i / (n - 1), v)) for i in range(n)]
            rows.append("{" + " ".join(row) + "}")
        img = tk.PhotoImage(width=n, height=n)
        img.put(" ".join(rows))
        self._sv_img = img.zoom(2, 2)            # храним ссылку, иначе соберёт GC
        self.sv_canvas.itemconfigure(self.sv_img_item, image=self._sv_img)

    def _on_scale(self, model, idx, value):
        if self._lock:
            return
        vals = [float(v.get().replace(",", ".")) for v in self.vars[model]]
        vals[idx] = float(value)
        if model == "RGB":
            vals = [round(x) for x in vals]       # у ползунка RGB — целые значения
        else:
            vals = [round(x, 1) for x in vals]
        self.update_from(model.lower(), tuple(vals))

    def _on_entry(self, model, idx):

        if self._lock:
            return
        name, lo, hi, _ = MODELS[model][idx]
        raw = self.vars[model][idx].get().strip().replace(",", ".")
        try:
            x = float(raw)
        except ValueError:
            self._error(model, idx, f"{model}: «{raw}» — не число. Значение {name} не изменено.")
            return
        if not (lo <= x <= hi):
            self._error(model, idx, f"{model}: {name} должно быть в диапазоне [{lo}; {hi}]. "
                                    f"Введено {x:g}.")
            return
        self.entries[model][idx].configure(style="TEntry")
        self.status.set("")
        vals = [float(v.get().replace(",", ".")) if k != idx else x
                for k, v in enumerate(self.vars[model])]
        if model == "HSV" and vals[0] >= 360:
            vals[0] = 0.0
        self.update_from(model.lower(), tuple(vals))

    def _error(self, model, idx, msg):
        self.status.set(msg)
        self.entries[model][idx].configure(style="Err.TEntry")
        self.root.after(1200, self.refresh)       # вернуть прежнее значение

    def _on_sv(self, event):
        x = clamp(event.x, 0, SV_SIZE - 1)
        y = clamp(event.y, 0, SV_SIZE - 1)
        s = 100.0 * x / (SV_SIZE - 1)
        v = 100.0 * (1 - y / (SV_SIZE - 1))
        self.update_from("hsv", (self.hsv[0], round(s, 1), round(v, 1)))

    def _on_hue(self, event):
        y = clamp(event.y, 0, SV_SIZE - 1)
        h = 360.0 * y / (SV_SIZE - 1)
        self.update_from("hsv", (round(h, 1), self.hsv[1], self.hsv[2]))

    def _on_hex(self, _event=None):
        s = self.hex_var.get().strip().lstrip("#")
        if len(s) == 3:
            s = "".join(ch * 2 for ch in s)
        try:
            if len(s) != 6:
                raise ValueError
            r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
        except ValueError:
            self.status.set("HEX: ожидается формат #RRGGBB.")
            self.root.after(1200, self.refresh)
            return
        self.status.set("")
        self.update_from("rgb", (r, g, b))

    def _system_picker(self):
        res = colorchooser.askcolor(color=to_hex(*self.rgb), title="Выбор цвета")
        if res and res[0]:
            self.update_from("rgb", tuple(round(c) for c in res[0]))

    def _random(self):
        self.update_from("rgb", tuple(random.randint(0, 255) for _ in range(3)))

    def update_from(self, source, values):
  
        old_h, old_s, _ = self.hsv
        if source == "rgb":
            self.rgb = tuple(float(x) for x in values)
            self.cmyk = rgb_to_cmyk(*self.rgb)
            h, s, v = rgb_to_hsv(*self.rgb)
            if s == 0 or v == 0:
                h = old_h
            if v == 0:
                s = old_s
            self.hsv = (h, s, v)
        elif source == "cmyk":
            self.cmyk = tuple(float(x) for x in values)
            self.rgb = cmyk_to_rgb(*self.cmyk)
            h, s, v = rgb_to_hsv(*self.rgb)
            if s < 1e-9 or v < 1e-9:
                h = old_h
            if v < 1e-9:
                s = old_s
            self.hsv = (h, s, v)
        else:  # hsv
            self.hsv = tuple(float(x) for x in values)
            self.rgb = hsv_to_rgb(*self.hsv)
            self.cmyk = rgb_to_cmyk(*self.rgb)
        self.refresh()

    def refresh(self):

        self._lock = True
        try:
            r, g, b = (clamp(x, 0, 255) for x in self.rgb)
            data = {"RGB": [round(r), round(g), round(b)],
                    "CMYK": [round(x, 1) for x in self.cmyk],
                    "HSV": [round(x, 1) for x in self.hsv]}
            for model, vals in data.items():
                for i, val in enumerate(vals):
                    self.scales[model][i].set(val)
                    self.vars[model][i].set(f"{val:g}" if model != "RGB" else str(val))
                    self.entries[model][i].configure(style="TEntry")

            hexcol = to_hex(r, g, b)
            self.hex_var.set(hexcol)
            self.preview.itemconfigure(self.preview_rect, fill=hexcol)

            h, s, v = self.hsv
            if self._last_hue != round(h, 1):          # перерисовываем квадрат только при смене H
                self._draw_sv_square(h)
                self._last_hue = round(h, 1)
            px = s / 100.0 * (SV_SIZE - 1)
            py = (1 - v / 100.0) * (SV_SIZE - 1)
            self.sv_canvas.coords(self.sv_marker, px - 6, py - 6, px + 6, py + 6)
            self.sv_canvas.coords(self.sv_marker2, px - 7, py - 7, px + 7, py + 7)
            hy = h / 360.0 * (SV_SIZE - 1)
            self.hue_canvas.coords(self.hue_marker, 0, hy - 2, HUE_W, hy + 2)
        finally:
            self._lock = False


def main():
    root = tk.Tk()
    ColorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()