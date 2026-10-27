# -*- coding: utf-8 -*-
"""
Created on Thu Jul  9 15:59:38 2026

@author: justas
"""


from ibapi.client import EClient
from ibapi.wrapper import EWrapper



class IBApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.connected = False
        self.historical_data = {}
        
    def error(self, reqId, errorCode, errorString):
        # Filter out irrelevant warnings about fractional shares
        if errorCode == 2176 and "fractional share" in errorString.lower():
            return  # Ignore this specific warning
        print(f"Error {errorCode}: {errorString}")
        
    def nextValidId(self, orderId):
        self.connected = True
        print("Connected to IB")
        
    def historicalData(self, reqId, bar):
        if reqId not in self.historical_data:
            self.historical_data[reqId] = []
        self.historical_data[reqId].append({
            'date': bar.date,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.volume
        })
        
    def historicalDataEnd(self, reqId, start, end):
        print(f"Historical data received for reqId {reqId}")