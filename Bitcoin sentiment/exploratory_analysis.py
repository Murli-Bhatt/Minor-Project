import pandas as pd
import numpy as np

def run_analysis():
    print("\n--- [Exploratory Analysis] Calculating Statistics ---")
    
    # 1. Load the cleaned merged dataset
    df = pd.read_csv("data/cleaned_data.csv")
    df['parsed_ist'] = pd.to_datetime(df['parsed_ist'])
    
    # 2. Feature Engineering
    df['trader_segment'] = pd.cut(
        df['Size USD'], 
        bins=[-1, 1000, 20000, np.inf], 
        labels=['Retail', 'Pro', 'Whale']
    )
    
    regime_map = {
        'Extreme Fear': 'Fearful',
        'Fear': 'Fearful',
        'Neutral': 'Neutral',
        'Greed': 'Greedy',
        'Extreme Greed': 'Greedy'
    }
    df['sentiment_regime'] = df['classification'].map(regime_map)
    df['is_win'] = (df['Closed PnL'] > 0).astype(int)
    df['is_close_trade'] = (df['Closed PnL'] != 0).astype(int)
    
    # Summary 1: Trader Performance by Sentiment Regime
    print("\nSummary 1: Trader Performance by Sentiment Regime")
    regime_stats = df.groupby('sentiment_regime', observed=False).agg(
        total_trades=('Closed PnL', 'count'),
        total_volume=('Size USD', 'sum'),
        net_pnl=('Closed PnL', 'sum'),
        closes=('is_close_trade', 'sum'),
        wins=('is_win', 'sum'),
        taker_ratio=('Crossed', 'mean')
    ).reset_index()
    regime_stats['win_rate_pct'] = (regime_stats['wins'] / regime_stats['closes']) * 100
    regime_stats['taker_ratio_pct'] = regime_stats['taker_ratio'] * 100
    
    for _, row in regime_stats.iterrows():
        pnl_str = f"${row['net_pnl']:,.2f}"
        vol_str = f"${row['total_volume']:,.2f}"
        print(f"Regime: {row['sentiment_regime']:<8} | "
              f"Net PnL: {pnl_str:<14} | "
              f"Win Rate: {row['win_rate_pct']:.2f}% | "
              f"Volume: {vol_str:<18} | "
              f"Taker Orders: {row['taker_ratio_pct']:.1f}%")
        
    # Summary 2: Performance by Trader Cohort
    print("\nSummary 2: Performance by Trader Cohort")
    cohort_stats = df.groupby('trader_segment', observed=False).agg(
        total_trades=('Closed PnL', 'count'),
        total_volume=('Size USD', 'sum'),
        net_pnl=('Closed PnL', 'sum'),
        closes=('is_close_trade', 'sum'),
        wins=('is_win', 'sum')
    ).reset_index()
    cohort_stats['win_rate_pct'] = (cohort_stats['wins'] / cohort_stats['closes']) * 100
    
    for _, row in cohort_stats.iterrows():
        pnl_str = f"${row['net_pnl']:,.2f}"
        avg_str = f"${row['total_volume']/row['total_trades']:,.2f}"
        print(f"Segment: {row['trader_segment']:<7} | "
              f"Net PnL: {pnl_str:<14} | "
              f"Win Rate: {row['win_rate_pct']:.2f}% | "
              f"Avg Size: {avg_str:<10}")
        
    # Summary 3: Cohort x Sentiment Regime Matrix
    print("\nSummary 3: Cohort x Sentiment Regime Matrix")
    matrix = df.groupby(['trader_segment', 'sentiment_regime'], observed=False).agg(
        net_pnl=('Closed PnL', 'sum'),
        closes=('is_close_trade', 'sum'),
        wins=('is_win', 'sum')
    ).reset_index()
    matrix['win_rate_pct'] = (matrix['wins'] / matrix['closes']) * 100
    
    for _, row in matrix.iterrows():
        pnl_str = f"${row['net_pnl']:,.2f}"
        print(f"Segment: {row['trader_segment']:<7} | "
              f"Regime: {row['sentiment_regime']:<8} | "
              f"Net PnL: {pnl_str:<14} | "
              f"Win Rate: {row['win_rate_pct']:.2f}%")
              
    # Summary 4: Trader Behavioral Taxonomy (All-Weather vs Sentiment-Dependent)
    print("\nSummary 4: Trader Behavioral Taxonomy (All-Weather vs. Sentiment-Dependent)")
    account_pnl = df.groupby(['Account', 'sentiment_regime'], observed=False)['Closed PnL'].sum().unstack(fill_value=0)
    
    all_weather = account_pnl[(account_pnl['Fearful'] > 0) & (account_pnl['Greedy'] > 0)].index
    greed_dep = account_pnl[(account_pnl['Fearful'] <= 0) & (account_pnl['Greedy'] > 0)].index
    fear_dep = account_pnl[(account_pnl['Fearful'] > 0) & (account_pnl['Greedy'] <= 0)].index
    struggling = account_pnl[(account_pnl['Fearful'] <= 0) & (account_pnl['Greedy'] <= 0)].index
    
    print(f"Total Unique Trading Accounts Analyzed: {len(account_pnl)}")
    print(f"1. All-Weather Superstar Accounts (Profitable in both Fear & Greed): {len(all_weather)} ({len(all_weather)/len(account_pnl)*100:.1f}%)")
    print(f"2. Greed-Dependent Chaser Accounts (Profitable ONLY in Greed): {len(greed_dep)} ({len(greed_dep)/len(account_pnl)*100:.1f}%)")
    print(f"3. Fear-Dependent Contrarian Accounts (Profitable ONLY in Fear): {len(fear_dep)} ({len(fear_dep)/len(account_pnl)*100:.1f}%)")
    print(f"4. Struggling Accounts (Negative in both regimes): {len(struggling)} ({len(struggling)/len(account_pnl)*100:.1f}%)")

    # Summary 5: Top 10 Most Profitable Traders & Their Most Traded Coin
    print("\nSummary 5: Top 10 Most Profitable Traders Portfolio Analysis")
    top_traders = df.groupby('Account')['Closed PnL'].sum().sort_values(ascending=False).head(10).index
    for rank, acc in enumerate(top_traders, 1):
        acc_df = df[df['Account'] == acc]
        most_traded_coin = acc_df['Coin'].value_counts().idxmax()
        total_pnl = acc_df['Closed PnL'].sum()
        closes = (acc_df['Closed PnL'] != 0).sum()
        wins = (acc_df['Closed PnL'] > 0).sum()
        win_rate = (wins / closes * 100) if closes > 0 else 0
        pnl_str = f"${total_pnl:,.2f}"
        print(f"Rank {rank:<2} | Trader: {acc[:6]}...{acc[-4:]} | Most Traded: {most_traded_coin:<9} | PnL: {pnl_str:<14} | Win Rate: {win_rate:.2f}% | Trades: {len(acc_df):,}")

    # Summary 6: Coin Performance under Fearful vs. Greedy Regimes
    print("\nSummary 6: Symbol-Level Performance under Sentiment Regimes")
    coin_regime = df.groupby(['Coin', 'sentiment_regime'], observed=False)['Closed PnL'].sum().unstack(fill_value=0)
    
    print("\nTop 5 Coins by PnL in Fearful Markets:")
    fear_top = coin_regime.sort_values('Fearful', ascending=False).head(5)
    for coin, row in fear_top.iterrows():
        f_pnl_str = f"${row['Fearful']:,.2f}"
        g_pnl_str = f"${row['Greedy']:,.2f}"
        print(f"Coin: {coin:<9} | Fearful PnL: {f_pnl_str:<14} | Greedy PnL: {g_pnl_str}")
        
    print("\nTop 5 Coins by PnL in Greedy Markets:")
    greed_top = coin_regime.sort_values('Greedy', ascending=False).head(5)
    for coin, row in greed_top.iterrows():
        f_pnl_str = f"${row['Fearful']:,.2f}"
        g_pnl_str = f"${row['Greedy']:,.2f}"
        print(f"Coin: {coin:<9} | Greedy PnL: {g_pnl_str:<14} | Fearful PnL: {f_pnl_str}")

    print("\nStatistical analysis complete!")

if __name__ == "__main__":
    run_analysis()
