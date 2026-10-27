# -*- coding: utf-8 -*-
"""
Created on Thu Jul  9 16:08:32 2026

@author: justas
"""

import threading
import time
from datetime import datetime
import warnings

import numpy as np
import pandas as pd
from scipy import stats
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from ibapi.contract import Contract

from classes.ib_app import IBApp
from classes.volatility_analyzer import VolatilityAnalyzer

warnings.filterwarnings('ignore')




class ImpliedVolatilityDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Implied Volatility Analysis Dashboard")
        self.root.geometry("1400x1200")

        # Application State
        self.equity_data = None
        self.volatility_data = None
        self.current_implied_vol = None
        self.connected = False
        self.vol_annualization = 252

        # IB Connection
        self.ib_app = IBApp()

        # Build UI Components
        self.setup_ui()

    # ----------------------------------------------------------------------
    # UI Setup & Layout
    # ----------------------------------------------------------------------
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)

        self._build_conn_frame(main_frame)
        self._build_query_frame(main_frame)
        self._build_vol_frame(main_frame)
        self._build_regime_frame(main_frame)
        self._build_status_frame(main_frame)
        self._build_plot_frame(main_frame)

    def _build_conn_frame(self, parent):
        frame = ttk.LabelFrame(parent, text="Interactive Brokers Connection", padding="5")
        frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        ttk.Label(frame, text="Host:").grid(row=0, column=0, padx=(0, 5))
        self.host_var = tk.StringVar(value="127.0.0.1")
        ttk.Entry(frame, textvariable=self.host_var, width=15).grid(row=0, column=1, padx=(0, 10))

        ttk.Label(frame, text="Port:").grid(row=0, column=2, padx=(0, 5))
        self.port_var = tk.StringVar(value="7497")
        ttk.Entry(frame, textvariable=self.port_var, width=10).grid(row=0, column=3, padx=(0, 10))

        self.connect_btn = ttk.Button(frame, text="Connect", command=self.connect_ib)
        self.connect_btn.grid(row=0, column=4, padx=(0, 10))

        self.disconnect_btn = ttk.Button(frame, text="Disconnect", command=self.disconnect_ib, state="disabled")
        self.disconnect_btn.grid(row=0, column=5)

    def _build_query_frame(self, parent):
        frame = ttk.LabelFrame(parent, text="Data Query", padding="5")
        frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        ttk.Label(frame, text="Symbol:").grid(row=0, column=0, padx=(0, 5))
        self.symbol_var = tk.StringVar(value="SPY")
        ttk.Entry(frame, textvariable=self.symbol_var, width=10).grid(row=0, column=1, padx=(0, 10))

        ttk.Label(frame, text="Duration:").grid(row=0, column=2, padx=(0, 5))
        self.duration_var = tk.StringVar(value="2 Y")
        ttk.Entry(frame, textvariable=self.duration_var, width=10).grid(row=0, column=3, padx=(0, 10))

        ttk.Label(frame, text="Forward Window (days):").grid(row=0, column=4, padx=(0, 5))
        self.forward_window_var = tk.StringVar(value="30")
        ttk.Entry(frame, textvariable=self.forward_window_var, width=6).grid(row=0, column=5, padx=(0, 10))

        self.query_btn = ttk.Button(frame, text="Query IV Data", command=self.query_data, state="disabled")
        self.query_btn.grid(row=0, column=6, padx=(0, 10))

        self.analyze_btn = ttk.Button(frame, text="Plot Vol Data", command=self.analyze_volatility, state="disabled")
        self.analyze_btn.grid(row=0, column=7)

    def _build_vol_frame(self, parent):
        frame = ttk.LabelFrame(parent, text="Current Implied Volatility", padding="5")
        frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        ttk.Label(frame, text="Current IV:").grid(row=0, column=0, padx=(0, 5))
        self.current_vol_label = ttk.Label(frame, text="N/A", font=("Arial", 12, "bold"))
        self.current_vol_label.grid(row=0, column=1, padx=(0, 20))

        ttk.Label(frame, text="Computation:").grid(row=0, column=2, padx=(0, 5))
        self.vol_computation_label = ttk.Label(frame, text="No data", font=("Arial", 10))
        self.vol_computation_label.grid(row=0, column=3, padx=(0, 10))

        ttk.Label(frame, text="Vol Range:").grid(row=0, column=4, padx=(0, 5))
        self.vol_range_label = ttk.Label(frame, text="N/A", font=("Arial", 10))
        self.vol_range_label.grid(row=0, column=5)

    def _build_regime_frame(self, parent):
        frame = ttk.LabelFrame(parent, text="Volatility Regime Analysis", padding="5")
        frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        ttk.Label(frame, text="Current Regime:").grid(row=0, column=0, padx=(0, 5))
        self.regime_label = ttk.Label(frame, text="N/A", font=("Arial", 11, "bold"))
        self.regime_label.grid(row=0, column=1, padx=(0, 20))

        ttk.Label(frame, text="Percentile:").grid(row=0, column=2, padx=(0, 5))
        self.percentile_label = ttk.Label(frame, text="N/A", font=("Arial", 10))
        self.percentile_label.grid(row=0, column=3, padx=(0, 20))

        ttk.Label(frame, text="Mean Reversion Signal:").grid(row=0, column=4, padx=(0, 5))
        self.reversion_label = ttk.Label(frame, text="N/A", font=("Arial", 10))
        self.reversion_label.grid(row=0, column=5)

    def _build_status_frame(self, parent):
        frame = ttk.LabelFrame(parent, text="Status", padding="5")
        frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        frame.columnconfigure(0, weight=1)

        self.status_text = scrolledtext.ScrolledText(frame, height=6, width=80)
        self.status_text.grid(row=0, column=0, sticky="ew")

    def _build_plot_frame(self, parent):
        frame = ttk.LabelFrame(parent, text="Implied Volatility Analysis Results", padding="5")
        frame.grid(row=5, column=0, columnspan=2, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        self.fig = Figure(figsize=(18, 6))
        self.ax1 = self.fig.add_subplot(1, 3, 1)
        self.ax2 = self.fig.add_subplot(1, 3, 2)
        self.ax3 = self.fig.add_subplot(1, 3, 3)

        self.canvas = FigureCanvasTkAgg(self.fig, frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

    # ----------------------------------------------------------------------
    # Helper Methods
    # ----------------------------------------------------------------------
    def log_message(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)

    def create_equity_contract(self, symbol: str) -> Contract:
        contract = Contract()
        contract.symbol = symbol.upper()
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        return contract

    # ----------------------------------------------------------------------
    # Network & Event Handlers
    # ----------------------------------------------------------------------
    def connect_ib(self):
        try:
            host = self.host_var.get()
            port = int(self.port_var.get())
            self.log_message(f"Connecting to IB at {host}:{port}...")

            threading.Thread(target=self._run_ib_connection, args=(host, port), daemon=True).start()
            self._poll_connection(start_time=time.time())
        except Exception as e:
            self.log_message(f"Connection error: {e}")

    def _run_ib_connection(self, host: str, port: int):
        try:
            self.ib_app.connect(host, port, 0)
            self.ib_app.run()
        except Exception as e:
            self.log_message(f"Connection thread error: {e}")

    def _poll_connection(self, start_time: float):
        """Non-blocking UI check for IB connection status."""
        if self.ib_app.connected:
            self.connected = True
            self.connect_btn.config(state="disabled")
            self.disconnect_btn.config(state="normal")
            self.query_btn.config(state="normal")
            self.log_message("Successfully connected to Interactive Brokers")
        elif time.time() - start_time < 5.0:
            self.root.after(100, self._poll_connection, start_time)
        else:
            self.log_message("Failed to connect to Interactive Brokers (Timeout)")

    def disconnect_ib(self):
        try:
            self.ib_app.disconnect()
            self.connected = False
            self.connect_btn.config(state="normal")
            self.disconnect_btn.config(state="disabled")
            self.query_btn.config(state="disabled")
            self.analyze_btn.config(state="disabled")

            self.current_implied_vol = None
            self.update_current_vol_display()
            self.log_message("Disconnected from Interactive Brokers")
        except Exception as e:
            self.log_message(f"Disconnect error: {e}")

    def query_data(self):
        if not self.connected:
            messagebox.showerror("Error", "Not connected to Interactive Brokers")
            return

        symbol = self.symbol_var.get().upper()
        duration = self.duration_var.get()

        self.log_message(f"Querying implied volatility data for {symbol}...")
        self.ib_app.historical_data.clear()

        contract = self.create_equity_contract(symbol)
        self.ib_app.reqHistoricalData(
            reqId=1,
            contract=contract,
            endDateTime="",
            durationStr=duration,
            barSizeSetting="1 day",
            whatToShow="OPTION_IMPLIED_VOLATILITY",
            useRTH=1,
            formatDate=1,
            keepUpToDate=False,
            chartOptions=[]
        )

        self._poll_historical_data(start_time=time.time(), symbol=symbol)

    def _poll_historical_data(self, start_time: float, symbol: str):
        """Non-blocking check for historical query completion."""
        if 1 in self.ib_app.historical_data:
            data = self.ib_app.historical_data[1]
            if data:
                df = pd.DataFrame(data)
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)

                self.equity_data = VolatilityAnalyzer.process_iv(df)
                self.volatility_data = self.equity_data[['implied_vol', 'iv_percentile']].copy()
                self.current_implied_vol = self.equity_data['implied_vol'].iloc[-1]

                self.log_message(f"Received {len(self.equity_data)} IV points for {symbol}")
                self.update_current_vol_display()
                self.analyze_btn.config(state="normal")
            else:
                self.log_message("No implied volatility data received.")
        elif time.time() - start_time < 15.0:
            self.root.after(100, self._poll_historical_data, start_time, symbol)
        else:
            self.log_message("Timeout waiting for historical volatility data.")

    # ----------------------------------------------------------------------
    # Updates & Plotting
    # ----------------------------------------------------------------------
    def update_current_vol_display(self):
        if self.current_implied_vol is None:
            self.current_vol_label.config(text="N/A", foreground="black")
            self.vol_computation_label.config(text="No data")
            self.vol_range_label.config(text="N/A")
            self.regime_label.config(text="N/A")
            self.percentile_label.config(text="N/A")
            self.reversion_label.config(text="N/A")
            return

        # Current Vol Label
        self.current_vol_label.config(text=f"{self.current_implied_vol:.4f} ({self.current_implied_vol * 100:.2f}%)")
        self.vol_computation_label.config(text="Annualized using √252 factor")

        # Range Label
        v_min, v_max, v_mean = (
            self.equity_data['implied_vol'].min(),
            self.equity_data['implied_vol'].max(),
            self.equity_data['implied_vol'].mean()
        )
        self.vol_range_label.config(text=f"Min: {v_min:.3f} | Mean: {v_mean:.3f} | Max: {v_max:.3f}")

        # Text color
        if self.current_implied_vol > 0.4:
            self.current_vol_label.config(foreground="red")
        elif self.current_implied_vol < 0.15:
            self.current_vol_label.config(foreground="green")
        else:
            self.current_vol_label.config(foreground="black")

        self.update_regime_analysis()

    def update_regime_analysis(self):
        if self.volatility_data is None or self.current_implied_vol is None:
            return

        pct = self.volatility_data['iv_percentile'].iloc[-1]
        regime_map = [
            (0.8, "HIGH VOLATILITY", "red", "EXPECT MEAN REVERSION DOWN", "blue"),
            (0.6, "ABOVE AVERAGE", "orange", "NEUTRAL", "black"),
            (0.4, "NORMAL", "black", "NEUTRAL", "black"),
            (0.2, "BELOW AVERAGE", "blue", "NEUTRAL", "black"),
            (-0.1, "LOW VOLATILITY", "green", "EXPECT MEAN REVERSION UP", "red")
        ]

        for threshold, regime, r_color, reversion, rev_color in regime_map:
            if pct > threshold:
                self.regime_label.config(text=regime, foreground=r_color)
                self.percentile_label.config(text=f"{pct:.1%}")
                self.reversion_label.config(text=reversion, foreground=rev_color)
                break

    def analyze_volatility(self):
        if self.equity_data is None or self.volatility_data is None:
            messagebox.showerror("Error", "No data available for analysis")
            return

        try:
            forward_window = int(self.forward_window_var.get())
            if forward_window <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Forward window must be a positive integer (days)")
            return

        self.log_message(f"Analyzing implied volatility patterns with a {forward_window}-day forward window...")

        vol_forward = self.volatility_data['implied_vol'].rolling(
            window=forward_window, min_periods=1
        ).mean().shift(-forward_window)

        analysis_df = pd.DataFrame({
            'current_vol': self.volatility_data['implied_vol'],
            'forward_30d_vol': vol_forward,
            'vol_diff': vol_forward - self.volatility_data['implied_vol'],
            'vol_percentile': self.volatility_data['iv_percentile']
        }).dropna()

        if len(analysis_df) < 30:
            self.log_message("Insufficient data for analysis")
            return

        # Perform Overall Regressions
        res1 = stats.linregress(analysis_df['current_vol'], analysis_df['forward_30d_vol'])
        res2 = stats.linregress(analysis_df['current_vol'], analysis_df['vol_diff'])

        intersection_x = res1.intercept / (1 - res1.slope) if res1.slope != 1 else analysis_df['current_vol'].median()
        high_reg, low_reg, high_vol_regime, low_vol_regime = VolatilityAnalyzer.run_regressions(
            analysis_df, intersection_x
        )

        self._plot_results(analysis_df, forward_window, intersection_x, res1, high_reg, low_reg, high_vol_regime, low_vol_regime)

    def _plot_results(self, df, forward_window, intersection_x, res1, high_reg, low_reg, high_regime, low_regime):
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()

        # Plot 1: Forward Vol vs Current Vol
        self.ax1.scatter(df['current_vol'], df['forward_30d_vol'], alpha=0.6, s=20)
        x_range = np.linspace(df['current_vol'].min(), df['current_vol'].max(), 100)
        self.ax1.plot(x_range, res1.slope * x_range + res1.intercept, 'r-', lw=2, label=f'R^2 = {res1.rvalue**2:.3f}')
        self.ax1.plot([df['current_vol'].min(), df['current_vol'].max()],
                      [df['current_vol'].min(), df['current_vol'].max()], 'k--', lw=1, alpha=0.7, label='y=x')

        self.ax1.set_xlabel(f'{forward_window}-Day Implied Volatility')
        self.ax1.set_ylabel(f'{forward_window}-Day Realised Average Vol')
        self.ax1.set_title(f'Forward Vol vs Current Vol\ny={res1.slope:.3f}x+{res1.intercept:.3f}')
        self.ax1.legend()
        self.ax1.grid(True, alpha=0.3)

        # Plot 2: Vol Difference vs Current Vol
        self.ax2.scatter(df.loc[high_regime, 'current_vol'], df.loc[high_regime, 'vol_diff'], alpha=0.6, s=20, color='red', label='High Vol')
        self.ax2.scatter(df.loc[low_regime, 'current_vol'], df.loc[low_regime, 'vol_diff'], alpha=0.6, s=20, color='blue', label='Low Vol')

        if high_reg:
            xh = df.loc[high_regime, 'current_vol']
            xr_h = np.linspace(xh.min(), xh.max(), 100)
            self.ax2.plot(xr_h, high_reg.slope * xr_h + high_reg.intercept, 'r-', lw=2, label=f'High R^2 = {high_reg.rvalue**2:.3f}')

        if low_reg:
            xl = df.loc[low_regime, 'current_vol']
            xr_l = np.linspace(xl.min(), xl.max(), 100)
            self.ax2.plot(xr_l, low_reg.slope * xr_l + low_reg.intercept, 'b-', lw=2, label=f'Low R^2 = {low_reg.rvalue**2:.3f}')
        
        self.ax2.set_xlabel(f'{forward_window}-Day Implied Volatility')
        self.ax2.set_ylabel(f'Realised Vol - iVol ({forward_window} days period)')
        self.ax2.axhline(y=0, color='k', linestyle='--', lw=1, alpha=0.7)
        self.ax2.axvline(x=intersection_x, color='g', linestyle=':', lw=1, alpha=0.7, label=f'Split ({intersection_x:.3f})')
        self.ax2.set_title('Vol Difference vs iVol')
        self.ax2.legend()
        self.ax2.grid(True, alpha=0.3)

        # Plot 3: Volatility Time Series
        self.ax3.plot(self.volatility_data.index, self.volatility_data['implied_vol'], lw=1, label='Implied Vol')
        self.ax3.axhline(y=self.volatility_data['implied_vol'].quantile(0.75), color='red', linestyle='--', alpha=0.7, label='75th Pct')
        self.ax3.axhline(y=self.volatility_data['implied_vol'].quantile(0.25), color='green', linestyle='--', alpha=0.7, label='25th Pct')
        self.ax3.axhline(y=self.volatility_data['implied_vol'].mean(), color='black', linestyle='-', alpha=0.7, label='Mean')
        
        if self.current_implied_vol is not None:
            self.ax3.scatter(self.volatility_data.index[-1], self.current_implied_vol, color='red', s=100, zorder=5, label='Current')

        self.ax3.set_title('Implied Volatility Time Series')
        self.ax3.set_ylabel('iVol')
        self.ax3.tick_params(axis='x', rotation=45)
        self.ax3.legend()
        self.ax3.grid(True, alpha=0.3)

        self.fig.tight_layout()
        self.canvas.draw()


