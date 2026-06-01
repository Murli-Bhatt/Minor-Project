import data_cleaning
import exploratory_analysis
import visualizations

def main():
    print("==================================================")
    print("Starting Bitcoin Sentiment & Trader Performance Analysis")
    print("Modular Pipeline Orchestrator (Intern Portfolio Version)")
    print("==================================================")
    
    # Step 1: Clean and Merge Raw Datasets
    data_cleaning.clean_and_merge_data()
    
    # Step 2: Compute and Print Statistical Analysis
    exploratory_analysis.run_analysis()
    
    # Step 3: Generate Matplotlib & Seaborn Visualizations
    visualizations.generate_plots()
    
    print("\n==================================================")
    print("Analysis Workflow Complete! All modular scripts ran successfully.")
    print("==================================================")

if __name__ == "__main__":
    main()