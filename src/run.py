from cProfile import label
from posixpath import split

import tkinter as tk
from tkinter import ttk
from gui import GUI

if __name__ == "__main__":
    root = tk.Tk()
    root.title("TMB's FIFA Autobidder")

    # Set theme
    root.tk.call("source", "azure.tcl")
    root.tk.call("set_theme", "dark")

    app = GUI(root)
    app.pack(fill="both", expand=True)

    # Set a minsize for the window, and place it in the middle
    root.update()
    root.minsize(root.winfo_width(), root.winfo_height())
    x_cordinate = int((root.winfo_screenwidth() / 2) - (root.winfo_width() / 2))
    y_cordinate = int((root.winfo_screenheight() / 2) - (root.winfo_height() / 2))
    root.geometry("+{}+{}".format(x_cordinate, y_cordinate-20))

    root.mainloop()