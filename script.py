import tkinter as tk
from tkinter import ttk, messagebox


def convert_temperature():
    raw = entry_value.get().strip().replace(",", ".")
    if not raw:
        messagebox.showerror("Ошибка", "Введите значение температуры")
        return

    try:
        value = float(raw)
    except ValueError:
        messagebox.showerror("Ошибка", "Неверный формат ввода: введите число")
        return

    scale = scale_var.get()

    if scale == "Цельсий":
        celsius = value
    elif scale == "Фаренгейт":
        celsius = (value - 32) * 5 / 9
    elif scale == "Кельвин":
        if value < 0:
            messagebox.showerror("Ошибка", "Температура в Кельвинах не может быть отрицательной")
            return
        celsius = value - 273.15
    else:
        messagebox.showerror("Ошибка", "Некорректная шкала")
        return

    fahrenheit = celsius * 9 / 5 + 32
    kelvin = celsius + 273.15

    result_celsius.set(f"{celsius:.2f} °C")
    result_fahrenheit.set(f"{fahrenheit:.2f} °F")
    result_kelvin.set(f"{kelvin:.2f} K")


root = tk.Tk()
root.title("Конвертер температур")
root.geometry("420x280")
root.resizable(False, False)

frame_input = ttk.LabelFrame(root, text="Входные данные", padding=10)
frame_input.pack(fill="x", padx=15, pady=8)

ttk.Label(frame_input, text="Значение:").grid(row=0, column=0, sticky="w")
entry_value = ttk.Entry(frame_input, width=22)
entry_value.grid(row=0, column=1, padx=8)

ttk.Label(frame_input, text="Шкала:").grid(row=1, column=0, sticky="w", pady=6)
scale_var = tk.StringVar(value="Цельсий")
scale_combo = ttk.Combobox(
    frame_input,
    textvariable=scale_var,
    values=["Цельсий", "Фаренгейт", "Кельвин"],
    state="readonly",
    width=20,
)
scale_combo.grid(row=1, column=1, padx=8)

ttk.Button(
    frame_input, text="Конвертировать", command=convert_temperature
).grid(row=2, column=0, columnspan=2, pady=10)

frame_result = ttk.LabelFrame(root, text="Результаты", padding=10)
frame_result.pack(fill="x", padx=15, pady=5)

result_celsius = tk.StringVar(value="—")
result_fahrenheit = tk.StringVar(value="—")
result_kelvin = tk.StringVar(value="—")

for row, (label_text, var) in enumerate(
    [("Цельсий:", result_celsius), ("Фаренгейт:", result_fahrenheit), ("Кельвин:", result_kelvin)]
):
    ttk.Label(frame_result, text=label_text, width=12).grid(row=row, column=0, sticky="w", pady=2)
    ttk.Label(frame_result, textvariable=var, width=18, anchor="w").grid(row=row, column=1)

root.mainloop()
