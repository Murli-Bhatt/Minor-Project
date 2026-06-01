import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

def generate_plots():
    print("\n--- [Visualizations] Generating Figures ---")
    
    # 1. Load the cleaned merged dataset
    df = pd.read_csv("data/cleaned_data.csv")
    df['parsed_ist'] = pd.to_datetime(df['parsed_ist'])
    df['date_only'] = pd.to_datetime(df['date_only'])
    
    # Create trader size cohorts
    df['trader_segment'] = pd.cut(
        df['Size USD'], 
        bins=[-1, 1000, 20000, np.inf], 
        labels=['Retail', 'Pro', 'Whale']
    )
    
    # Map classifications to regimes
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
    
    # Set up Seaborn aesthetics for premium human look
    sns.set_theme(style="whitegrid")
    
    # -------------------------------------------------------------
    # Figure 1: Cumulative Closed PnL Over Time with Sentiment Shading
    # -------------------------------------------------------------
    print("Generating Figure 1 (Cumulative PnL timeseries)...")
    fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
    
    segments = ['Whale', 'Pro', 'Retail']
    segment_colors = {'Whale': '#e67e22', 'Pro': '#9b59b6', 'Retail': '#3498db'}
    sentiment_colors = {
        'Extreme Fear': '#e74c3c',
        'Fear': '#e67e22',
        'Neutral': '#bdc3c7',
        'Greed': '#2ecc71',
        'Extreme Greed': '#1abc9c'
    }
    
    # Get unique daily classifications for shading the background
    daily_sent = df.groupby('date_only')[['value', 'classification']].first().reset_index()
    
    for i, seg in enumerate(segments):
        ax = axes[i]
        seg_df = df[df['trader_segment'] == seg].copy()
        seg_df['cum_pnl'] = seg_df['Closed PnL'].cumsum()
        
        # Plot cumulative PnL
        ax.plot(seg_df['parsed_ist'], seg_df['cum_pnl'], color=segment_colors[seg], linewidth=2.0, label=f'{seg} PnL')
        
        # Shade background according to Fear & Greed classification
        for idx in range(len(daily_sent) - 1):
            start = daily_sent.loc[idx, 'date_only']
            end = daily_sent.loc[idx+1, 'date_only']
            sent = daily_sent.loc[idx, 'classification']
            ax.axvspan(start, end, color=sentiment_colors[sent], alpha=0.08, zorder=0)
            
        ax.set_ylabel("PnL ($)")
        ax.set_title(f"Cumulative Closed PnL - {seg}s", loc='left', fontsize=11, fontweight='bold')
        ax.legend(loc='upper left')
        
    axes[2].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.xticks(rotation=15)
    plt.suptitle("Hyperliquid Trader Cumulative PnL Cycles vs. Daily Market Sentiment Shading", fontsize=14, fontweight='bold', y=0.96)
    
    os.makedirs('plots', exist_ok=True)
    fig.savefig("plots/cumulative_pnl_by_segment.png", dpi=150, bbox_inches='tight')
    plt.close()
    
    # -------------------------------------------------------------
    # Figure 2: Grouped Bar Charts for Net PnL and Win Rates (Seaborn-powered)
    # -------------------------------------------------------------
    print("Generating Figure 2 (Performance Matrix grouped bar charts)...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Aggregating metrics
    matrix = df.groupby(['trader_segment', 'sentiment_regime'], observed=False).agg(
        net_pnl=('Closed PnL', 'sum'),
        closes=('is_close_trade', 'sum'),
        wins=('is_win', 'sum')
    ).reset_index()
    matrix['win_rate'] = (matrix['wins'] / matrix['closes']) * 100
    
    # Plot 1: Net PnL Grouped Bar
    sns.barplot(
        data=matrix, 
        x='trader_segment', 
        y='net_pnl', 
        hue='sentiment_regime', 
        ax=ax1,
        palette="coolwarm"
    )
    ax1.set_title("Total Net Closed PnL by Cohort & Regime", fontsize=12, fontweight='bold')
    ax1.set_ylabel("Net PnL ($)")
    ax1.set_xlabel("Trader Cohort")
    ax1.legend(title="Sentiment Regime")
    
    # Plot 2: Win Rate Grouped Bar
    sns.barplot(
        data=matrix, 
        x='trader_segment', 
        y='win_rate', 
        hue='sentiment_regime', 
        ax=ax2,
        palette="coolwarm"
    )
    ax2.set_title("Average Transaction Win Rate (%) by Cohort & Regime", fontsize=12, fontweight='bold')
    ax2.set_ylabel("Win Rate (%)")
    ax2.set_xlabel("Trader Cohort")
    ax2.axhline(50.0, color='#e74c3c', linestyle=':')
    ax2.legend(title="Sentiment Regime")
    
    plt.suptitle("How Bitcoin Sentiment Regimes Impact Profitability and Win Rates", fontsize=14, fontweight='bold', y=0.96)
    fig.savefig("plots/performance_by_sentiment_regime.png", dpi=150, bbox_inches='tight')
    plt.close()
    
    # -------------------------------------------------------------
    # Figure 3: Daily Long Open Ratio vs. Fear & Greed Index Score
    # -------------------------------------------------------------
    print("Generating Figure 3 (Daily Long Open Ratio scatter plot)...")
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Aggregate daily statistics
    daily = df.groupby('date_only').agg(
        fg_value=('value', 'first'),
        fg_class=('classification', 'first'),
        open_longs=('Direction', lambda x: ((x == 'Open Long') | (x == 'Buy')).sum()),
        open_shorts=('Direction', lambda x: ((x == 'Open Short') | (x == 'Sell')).sum()),
    ).reset_index()
    
    daily['long_ratio'] = (daily['open_longs'] / (daily['open_longs'] + daily['open_shorts'])) * 100
    daily = daily.dropna()
    
    # Plot scatter plot using seaborn with hue colored by classification
    sns.scatterplot(
        data=daily,
        x='fg_value',
        y='long_ratio',
        hue='fg_class',
        s=100,
        alpha=0.8,
        ax=ax,
        palette=sentiment_colors
    )
    
    # Add a simple numpy linear fit line
    if len(daily) > 1:
        z = np.polyfit(daily['fg_value'], daily['long_ratio'], 1)
        p = np.poly1d(z)
        xp = np.linspace(daily['fg_value'].min(), daily['fg_value'].max(), 100)
        ax.plot(xp, p(xp), color='#34495e', linestyle='--', linewidth=1.5, label=f"Trendline (Slope: {z[0]:.2f})")
        
    ax.axhline(50.0, color='#7f8c8d', linestyle=':', alpha=0.7)
    ax.set_title("Do Traders Herd? Daily Long Open Ratio vs. Fear & Greed Value", fontsize=12, fontweight='bold')
    ax.set_xlabel("Fear & Greed Index Score (0 = Extreme Fear, 100 = Extreme Greed)")
    ax.set_ylabel("Opened Long Positions (%)")
    ax.legend(title="Sentiment Category")
    
    # -------------------------------------------------------------
    # Figure 4: Distribution of Transaction Sizes (Volume in USD)
    # -------------------------------------------------------------
    print("Generating Figure 4 (Transaction size distribution histogram)...")
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Using seaborn to draw a simple histogram of trade sizes with log scale and KDE fit
    sns.histplot(
        data=df, 
        x='Size USD', 
        bins=50, 
        kde=True, 
        ax=ax, 
        color='#9b59b6',
        log_scale=True
    )
    
    ax.set_title("Distribution of Trader Transaction Volumes (USD Size)", fontsize=12, fontweight='bold')
    ax.set_xlabel("Transaction Size in USD (Log Scale)")
    ax.set_ylabel("Number of Transactions (Frequency)")
    
    fig.savefig("plots/trade_size_distribution.png", dpi=150, bbox_inches='tight')
    plt.close()
    
    # -------------------------------------------------------------
    # Figure 5: Symbol-Level Net Profits by Sentiment Regime
    # -------------------------------------------------------------
    print("Generating Figure 5 (Symbol performance grouped bar chart)...")
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Filter the dataset for the top symbols we analyzed
    top_coins = ['HYPE', 'ETH', 'SOL', 'BTC', 'MELANIA', '@107']
    df_filtered = df[df['Coin'].isin(top_coins)].copy()
    
    # Aggregate PnL by Coin and Sentiment Regime
    coin_pnl = df_filtered.groupby(['Coin', 'sentiment_regime'], observed=False)['Closed PnL'].sum().reset_index()
    
    # Plot grouped bar chart using seaborn
    sns.barplot(
        data=coin_pnl,
        x='Coin',
        y='Closed PnL',
        hue='sentiment_regime',
        ax=ax,
        palette='coolwarm'
    )
    
    ax.set_title("Total Net Profit (Closed PnL) by Symbol & Sentiment Regime", fontsize=12, fontweight='bold')
    ax.set_xlabel("Trading Symbol")
    ax.set_ylabel("Net Profit ($)")
    ax.legend(title="Sentiment Regime")
    
    fig.savefig("plots/symbol_performance.png", dpi=150, bbox_inches='tight')
    plt.close()
    
    print("All visualizations generated successfully and saved to 'plots/' directory!")

if __name__ == "__main__":
    generate_plots()
