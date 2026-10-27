# -*- coding: utf-8 -*-
"""
Created on Thu Jul  9 17:11:38 2026

@author: justas
"""

import pandas as pd
from scipy import stats



class VolatilityAnalyzer:
    """Handles core data processing and statistical computations."""

    @staticmethod
    def process_iv(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['implied_vol'] = df['close']
        df['iv_percentile'] = df['implied_vol'].rolling(window=252).rank(pct=True)
        return df

    @staticmethod
    def run_regressions(analysis_df: pd.DataFrame, intersection_x: float):
        high_mask = analysis_df['current_vol'] > intersection_x
        low_mask = analysis_df['current_vol'] <= intersection_x

        high_reg = (stats.linregress(analysis_df.loc[high_mask, 'current_vol'],
                                     analysis_df.loc[high_mask, 'vol_diff'])
                    if high_mask.sum() > 10 else None)

        low_reg = (stats.linregress(analysis_df.loc[low_mask, 'current_vol'],
                                    analysis_df.loc[low_mask, 'vol_diff'])
                   if low_mask.sum() > 10 else None)

        return high_reg, low_reg, high_mask, low_mask