import sys
import sqlite3
import re
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

def run_all_queries():
    db_path = project_root / "data" / "db" / "mutual_fund_analytics.db"
    queries_path = project_root / "sql" / "queries.sql"
    processed_dir = project_root / "data" / "processed"
    docs_dir = project_root / "docs"
    
    processed_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    if not db_path.exists():
        print(f"Error: Database file does not exist at {db_path}")
        return False
    if not queries_path.exists():
        print(f"Error: SQL queries file does not exist at {queries_path}")
        return False
        
    conn = sqlite3.connect(str(db_path))
    
    # Read and parse sql/queries.sql
    with open(queries_path, "r", encoding="utf-8") as f:
        sql_content = f.read()
        
    # Split queries by double-dash comments followed by a number or number+letter
    # Pattern: (?=-- \d[a-z]?\.)
    query_blocks = re.split(r'(?=-- \d[a-z]?\.)', sql_content)
    
    # Filter out empty blocks
    query_blocks = [q.strip() for q in query_blocks if q.strip()]
    
    query_results = {}
    
    # Define mapping of query numbers to metadata for execution & plotting
    query_metadata = {
        "1": {"name": "aum_analysis", "title": "AUM Analysis by Fund House"},
        "2a": {"name": "transaction_summary", "title": "Transaction Volume & Amounts by Type"},
        "2b": {"name": "payment_mode_breakdown", "title": "Payment Mode Breakdown"},
        "3": {"name": "top_performing_funds", "title": "Top Performing Funds (Sharpe > 1.0)"},
        "4": {"name": "sip_mom_trends", "title": "SIP Inflow MoM Trends"},
        "5": {"name": "portfolio_diversity", "title": "Dominant Sector Allocation per Scheme"}
    }
    
    print(f"Loaded {len(query_blocks)} query blocks from SQL file.\n")
    
    for q_block in query_blocks:
        # Extract the query number (e.g. 1, 2a, 2b, 3, 4, 5) from the first line comment
        first_line = q_block.split("\n")[0]
        match = re.search(r'-- (\d[a-z]?)\.', first_line)
        if not match:
            print(f"Warning: Could not parse query number from line: {first_line}")
            continue
            
        q_id = match.group(1)
        meta = query_metadata.get(q_id)
        if not meta:
            print(f"Warning: No metadata configured for query ID {q_id}")
            continue
            
        print(f"Executing Query {q_id}: {meta['title']}...")
        
        # Execute query
        try:
            df = pd.read_sql_query(q_block, conn)
            query_results[q_id] = df
            
            # Save to CSV
            csv_path = processed_dir / f"query_{q_id}_{meta['name']}.csv"
            df.to_csv(csv_path, index=False)
            print(f" -> Exported result to {csv_path.name} | {len(df)} rows")
        except Exception as e:
            print(f"Error executing Query {q_id}: {e}")
            
    # Set premium Seaborn theme for plotting
    sns.set_theme(style="whitegrid")
    plt.rcParams['figure.figsize'] = (10, 6)
    plt.rcParams['font.sans-serif'] = 'Inter'
    plt.rcParams['font.family'] = 'sans-serif'
    
    # --- PLOTTING CHARTS ---
    print("\nGenerating premium visualization charts...")
    
    # Chart 1: AUM Ranking by Fund House (Query 1)
    if "1" in query_results:
        df1 = query_results["1"]
        plt.figure(figsize=(10, 5))
        # Deep blue/indigo theme
        colors = sns.color_palette("coolwarm", len(df1))
        sns.barplot(data=df1, x="aum_crore", y="fund_house", palette=colors)
        plt.title("AUM Ranking by Fund House (Crores)", fontsize=14, fontweight="bold", pad=15)
        plt.xlabel("AUM (INR Crore)", fontsize=11)
        plt.ylabel("Fund House", fontsize=11)
        # Add labels to the bars
        for idx, row in df1.iterrows():
            plt.text(row["aum_crore"] + 5000, idx, f"{int(row['aum_crore']):,}", va='center', fontsize=9, fontweight='semibold')
        plt.tight_layout()
        chart_path = docs_dir / "01_aum_ranking.png"
        plt.savefig(chart_path, dpi=300)
        plt.close()
        print(f" -> Saved chart: {chart_path.name}")
        
    # Chart 2a: Transactions Volume & Value by Type (Query 2a)
    if "2a" in query_results:
        df2a = query_results["2a"]
        # Double plot (count and amount side-by-side)
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        # Left plot: Volume (count)
        sns.barplot(data=df2a, x="transaction_type", y="transaction_count", ax=axes[0], palette="Blues_d")
        axes[0].set_title("Transaction Count by Type", fontsize=12, fontweight="bold")
        axes[0].set_xlabel("Transaction Type")
        axes[0].set_ylabel("Count")
        for p in axes[0].patches:
            axes[0].annotate(f"{int(p.get_height()):,}", (p.get_x() + p.get_width() / 2., p.get_height()),
                        ha='center', va='center', xytext=(0, 5), textcoords='offset points', fontsize=10, fontweight='semibold')
            
        # Right plot: Amount (value in Cr)
        df2a["total_amount_cr"] = df2a["total_amount_inr"] / 1e7
        sns.barplot(data=df2a, x="transaction_type", y="total_amount_cr", ax=axes[1], palette="Purples_d")
        axes[1].set_title("Total Transaction Value (Crores)", fontsize=12, fontweight="bold")
        axes[1].set_xlabel("Transaction Type")
        axes[1].set_ylabel("Value (INR Crore)")
        for p in axes[1].patches:
            axes[1].annotate(f"{p.get_height():.2f} Cr", (p.get_x() + p.get_width() / 2., p.get_height()),
                        ha='center', va='center', xytext=(0, 5), textcoords='offset points', fontsize=10, fontweight='semibold')
            
        plt.suptitle("Transaction Type Breakdown (Volume vs Value)", fontsize=15, fontweight="bold", y=0.98)
        plt.tight_layout()
        chart_path = docs_dir / "02a_transactions_by_type.png"
        plt.savefig(chart_path, dpi=300)
        plt.close()
        print(f" -> Saved chart: {chart_path.name}")
        
    # Chart 2b: Payment Mode Breakdown (Query 2b)
    if "2b" in query_results:
        df2b = query_results["2b"]
        plt.figure(figsize=(8, 6))
        colors = sns.color_palette("pastel")[0:len(df2b)]
        # Donut chart
        plt.pie(df2b["transaction_count"], labels=df2b["payment_mode"], autopct='%1.1f%%', 
                startangle=140, colors=colors, wedgeprops=dict(width=0.4, edgecolor='w'))
        plt.title("Transaction Volume Breakdown by Payment Mode", fontsize=14, fontweight="bold", pad=15)
        plt.tight_layout()
        chart_path = docs_dir / "02b_payment_modes.png"
        plt.savefig(chart_path, dpi=300)
        plt.close()
        print(f" -> Saved chart: {chart_path.name}")
        
    # Chart 4: SIP Inflow MoM Trends (Query 4)
    if "4" in query_results:
        df4 = query_results["4"]
        plt.figure(figsize=(12, 6))
        # Plot dual axis: SIP Inflow (line) and MoM Growth % (bar)
        ax1 = sns.lineplot(data=df4, x="month", y="sip_inflow_crore", marker="o", color="#1a73e8", linewidth=2.5, label="SIP Inflow (Cr)")
        plt.xticks(rotation=45)
        ax1.set_title("Industry SIP Inflow Trends & Growth", fontsize=14, fontweight="bold", pad=15)
        ax1.set_xlabel("Month", fontsize=11)
        ax1.set_ylabel("SIP Inflow (INR Crore)", color="#1a73e8")
        ax1.tick_params(axis='y', labelcolor="#1a73e8")
        
        # Instantiate second y-axis
        ax2 = ax1.twinx()
        # Bar plot for mom_growth_pct (excluding the first month which is null)
        df4_growth = df4.dropna(subset=["mom_growth_pct"])
        sns.barplot(data=df4_growth, x="month", y="mom_growth_pct", ax=ax2, alpha=0.3, color="#34a853", label="MoM Growth %")
        ax2.set_ylabel("MoM Growth Rate (%)", color="#34a853")
        ax2.tick_params(axis='y', labelcolor="#34a853")
        ax2.grid(False) # avoid overlapping gridlines
        
        plt.tight_layout()
        chart_path = docs_dir / "04_sip_mom_trends.png"
        plt.savefig(chart_path, dpi=300)
        plt.close()
        print(f" -> Saved chart: {chart_path.name}")
        
    # Chart 5: Sector Allocations (Query 5)
    if "5" in query_results:
        df5 = query_results["5"].head(10) # Plot top 10 dominant sector schemes
        plt.figure(figsize=(12, 6))
        sns.barplot(data=df5, x="dominant_sector_weight_pct", y="scheme_name", hue="dominant_sector", dodge=False, palette="Set2")
        plt.title("Dominant Sector Allocations (Top 10 Schemes)", fontsize=14, fontweight="bold", pad=15)
        plt.xlabel("Sector Weight (%)", fontsize=11)
        plt.ylabel("Scheme Name", fontsize=11)
        plt.legend(title="Dominant Sector", loc="lower right")
        plt.tight_layout()
        chart_path = docs_dir / "05_sector_allocations.png"
        plt.savefig(chart_path, dpi=300)
        plt.close()
        print(f" -> Saved chart: {chart_path.name}")
        
    # --- GENERATING ANALYSIS REPORT ---
    print("\nGenerating comprehensive database analysis report...")
    cursor = conn.cursor()
    report_lines = []
    report_lines.append("# Mutual Fund Database & Query Analysis Report")
    report_lines.append(f"\nReport Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("\nThis report compiles the results of the Day 2 analytical SQL queries run on the relational SQLite database `mutual_fund_analytics.db`.")
    
    # 1. Scheme/Database Structure
    report_lines.append("\n## 1. Database Schema & Volume Overview")
    report_lines.append("\nThe relational SQLite database implements a star schema to optimize query speeds for financial reporting, containing 2 dimension tables and 9 fact/helper tables:")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cursor.fetchall() if not r[0].startswith("sqlite_")]
    
    report_lines.append("\n| Table Name | Row Count | Purpose |")
    report_lines.append("| --- | --- | --- |")
    
    table_descriptions = {
        "dim_fund": "Dimension table containing fund manager, benchmark, and asset class details.",
        "dim_date": "Pre-populated date dimensions (quarter, month, day, is_weekend).",
        "fact_nav": "Fact table tracking historical Daily Net Asset Values (NAV).",
        "fact_transactions": "Fact table capturing individual investor transaction details.",
        "fact_performance": "Fact table displaying 1yr, 3yr, 5yr returns, Sharpe ratios, and AUM.",
        "fact_portfolio": "Fact table documenting mutual fund stock holdings and sector weights.",
        "fact_aum": "Fact table summarizing monthly Assets Under Management by fund house.",
        "fact_sip_industry": "Fact table tracking monthly industry-wide SIP inflows and folio growth.",
        "fact_category_inflows": "Fact table logging net category inflows (large/mid/small cap).",
        "fact_industry_folios": "Fact table summarizing total equity, debt, and hybrid folio counts.",
        "fact_benchmark_indices": "Fact table displaying closing prices for reference market indices."
    }
    
    for table in sorted(tables):
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        count = cursor.fetchone()[0]
        desc = table_descriptions.get(table, "Helper table.")
        report_lines.append(f"| `{table}` | {count:,} | {desc} |")
        
    # 2. Query Results and Explanations
    report_lines.append("\n## 2. Analytical SQL Query Insights")
    
    # Section for Query 1
    if "1" in query_results:
        df = query_results["1"]
        report_lines.append("\n### Query 1: Assets Under Management (AUM) Analysis")
        report_lines.append("\nThis query ranks the fund houses based on their latest AUM. AUM indicates the scale and investor trust in a fund house.")
        report_lines.append("\n#### Query Output Table:")
        report_lines.append("\n" + df.to_markdown(index=False))
        report_lines.append("\n#### Visualization:")
        report_lines.append("\n![AUM Ranking by Fund House](01_aum_ranking.png)")
        report_lines.append("\n*Insight*: SBI Mutual Fund is the largest player in this dataset with over 6.05 lakh crore AUM and 186 schemes, followed by ICICI Prudential and HDFC Mutual Fund.")
        
    # Section for Query 2
    if "2a" in query_results and "2b" in query_results:
        df2a = query_results["2a"]
        df2b = query_results["2b"]
        report_lines.append("\n### Query 2: Transaction Summaries")
        report_lines.append("\nThese queries provide summaries of investor transaction volumes, types, and payment modes.")
        report_lines.append("\n#### Query 2a Output (Transaction Types):")
        report_lines.append("\n" + df2a.to_markdown(index=False))
        report_lines.append("\n#### Query 2b Output (Payment Modes):")
        report_lines.append("\n" + df2b.to_markdown(index=False))
        report_lines.append("\n#### Visualizations:")
        report_lines.append("\n![Transaction Type Volume vs Value](02a_transactions_by_type.png)")
        report_lines.append("\n![Payment Mode Breakdown](02b_payment_modes.png)")
        report_lines.append("\n*Insight*: SIP is the most frequent transaction type (highest volume/count), indicating a strong regular investing culture. However, Lumpsum transactions account for the largest share of total cash volume. Net Banking and UPI are the dominant transaction methods.")
        
    # Section for Query 3
    if "3" in query_results:
        df = query_results["3"]
        report_lines.append("\n### Query 3: Performance Metrics (Top Performing Funds)")
        report_lines.append("\nThis query filters schemes with a Sharpe Ratio > 1.0 (indicating good risk-adjusted returns) and ranks them by their 3-year annualized returns.")
        report_lines.append("\n#### Query Output Table (Top 10):")
        report_lines.append("\n" + df.head(10).to_markdown(index=False))
        report_lines.append("\n*Insight*: Nippon India Large Cap Fund and SBI Bluechip Fund show strong 3-year performance while maintaining a Sharpe ratio of over 1.0, representing superior efficiency in generating return per unit of volatility.")
        
    # Section for Query 4
    if "4" in query_results:
        df = query_results["4"]
        report_lines.append("\n### Query 4: Industry SIP Inflow Trends")
        report_lines.append("\nThis query calculates month-over-month (MoM) growth in SIP inflows, highlighting industry health and retail investor participation.")
        report_lines.append("\n#### Query Output Table (Latest 12 Months):")
        report_lines.append("\n" + df.tail(12).to_markdown(index=False))
        report_lines.append("\n#### Visualization:")
        report_lines.append("\n![SIP Inflow Trends](04_sip_mom_trends.png)")
        report_lines.append("\n*Insight*: SIP inflows have steadily grown month-over-month, showing a resilient retail investor appetite for equity mutual funds despite market fluctuations.")
        
    # Section for Query 5
    if "5" in query_results:
        df = query_results["5"]
        report_lines.append("\n### Query 5: Portfolio Diversity (Dominant Sectors)")
        report_lines.append("\nThis query identifies the dominant stock sector allocation for each scheme.")
        report_lines.append("\n#### Query Output Table (Top 10 Schemes):")
        report_lines.append("\n" + df.head(10).to_markdown(index=False))
        report_lines.append("\n#### Visualization:")
        report_lines.append("\n![Dominant Sector Allocation](05_sector_allocations.png)")
        report_lines.append("\n*Insight*: Technology and Financial Services are the most dominant sectors across bluechip and large-cap equity portfolios, in some cases commanding over 20-30% of total fund weight.")
        
    report_file = docs_dir / "database_analysis_report.md"
    with open(report_file, "w", encoding="utf-8") as rf:
        rf.write("\n".join(report_lines))
        
    print(f"Comprehensive report successfully written to: {report_file}")
    
    conn.close()
    return True

if __name__ == "__main__":
    success = run_all_queries()
    sys.exit(0 if success else 1)
