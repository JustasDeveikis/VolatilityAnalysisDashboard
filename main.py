# -*- coding: utf-8 -*-
"""
Created on Thu Jun 11 14:40:16 2026

@author: justas
"""



import tkinter as tk
from classes.ib_app import IBApp
from classes.iv_dashboard import ImpliedVolatilityDashboard
import utils.mpl_settings


def main():
    root = tk.Tk()
    app = ImpliedVolatilityDashboard(root)
    root.mainloop()

if __name__ == "__main__":
    main()

