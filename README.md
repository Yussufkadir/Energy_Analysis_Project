# ⚡ Energy Analysis Project 

A comprehensive analysis of U.S. electricity generation patterns across different energy sources using EIA (Energy Information Administration) data. This project explores temporal patterns, source contributions, and inter-relationships between energy sources through statistical analysis and dimensionality reduction techniques.

## 📋 About

This project analyzes one year of electricity generation data from the U.S. Energy Information Administration, examining how different energy sources (coal, natural gas, nuclear, renewables, etc.) contribute to the power grid. Through multi-temporal analysis spanning hourly, daily, weekly, monthly, and yearly patterns, the project uncovers consumption trends and dependencies between energy sources using Principal Component Analysis (PCA) to reveal underlying relationships in the data.

## ✨ Key Features

- **Multi-Temporal Analysis**: Examination of energy patterns across multiple time scales (hourly, daily, weekly, monthly, yearly)
- **Source Comparison**: Detailed breakdown of electricity generation by energy source
- **Pattern Recognition**: Identification of consumption trends and seasonal variations
- **PCA Analysis**: Dimensionality reduction to discover relationships between different energy sources
- **Data Visualization**: Clear, informative charts and graphs showing generation patterns
- **Statistical Insights**: Quantitative analysis of energy source contributions and correlations

## 🔍 Analysis Overview

### Energy Sources Analyzed
- Coal
- Natural Gas
- Nuclear
- Hydroelectric
- Wind
- Solar
- Other Renewables
- Petroleum and Other Fossil Fuels

### Temporal Scales
1. **Hourly Analysis**: Peak and off-peak generation patterns
2. **Daily Analysis**: Day-to-day variations and trends
3. **Weekly Analysis**: Weekday vs. weekend patterns
4. **Monthly Analysis**: Seasonal variations in generation
5. **Yearly Analysis**: Overall contribution and long-term trends

### Key Questions Answered
- Which energy sources generate the most electricity?
- How do generation patterns vary by time of day, week, and season?
- What relationships exist between different energy sources?
- How do renewable sources complement traditional sources?
- What are the peak demand periods for each energy source?

## 🛠️ Technology Stack

- **Python 3.x**: Primary programming language
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computations
- **Matplotlib**: Data visualization
- **Seaborn**: Statistical visualizations
- **Scikit-learn**: PCA implementation and analysis
- **Jupyter Notebook**: Interactive analysis and documentation

## 🏗️ Project Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Collection                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │  EIA API / CSV Download                            │    │
│  │  - One year of hourly generation data              │    │
│  │  - Multiple energy sources                         │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                Data Processing & Cleaning                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │  - Handle missing values                           │    │
│  │  - Data type conversions                           │    │
│  │  - Timestamp parsing                               │    │
│  │  - Outlier detection and handling                  │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              Temporal Aggregation                           │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Hourly   →  Group by hour of day                  │    │
│  │  Daily    →  Aggregate to daily totals             │    │
│  │  Weekly   →  Sum weekly generation                 │    │
│  │  Monthly  →  Calculate monthly patterns            │    │
│  │  Yearly   →  Annual total and averages             │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
┌───────▼────────┐          ┌─────────▼──────────┐
│   Statistical  │          │   PCA Analysis     │
│    Analysis    │          │                    │
│  ┌───────────┐ │          │  ┌──────────────┐ │
│  │ Totals by │ │          │  │ Correlation  │ │
│  │  source   │ │          │  │   matrix     │ │
│  │           │ │          │  └──────────────┘ │
│  │ % Share   │ │          │  ┌──────────────┐ │
│  │           │ │          │  │ Dimensionality│ │
│  │ Trends    │ │          │  │  reduction   │ │
│  │           │ │          │  └──────────────┘ │
│  │ Patterns  │ │          │  ┌──────────────┐ │
│  └───────────┘ │          │  │ Component    │ │
└────────────────┘          │  │  analysis    │ │
                            │  └──────────────┘ │
                            └────────────────────┘
        │                             │
        └──────────────┬──────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   Visualization                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │  - Time series plots                               │    │
│  │  - Stacked area charts                             │    │
│  │  - Heatmaps                                        │    │
│  │  - Box plots                                       │    │
│  │  - PCA biplots and scree plots                    │    │
│  │  - Correlation matrices                            │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- pip or conda package manager
- Jupyter Notebook or JupyterLab

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/Yussufkadir/Energy_Analysis_Project.git
cd Energy_Analysis_Project
```

2. **Create virtual environment** (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

## 📊 Key Analyses & Findings

### 1. Generation by Source
Analysis of total electricity generation and percentage contribution by each energy source over the year.

**Key Metrics:**
- Total generation per source (MWh)
- Percentage share of total generation
- Average daily generation by source

### 2. Temporal Patterns

**Hourly Patterns:**
- Peak generation hours
- Off-peak periods
- Hour-of-day profiles for each source

**Daily Patterns:**
- Weekday vs. weekend differences
- Day-to-day variability
- Rolling averages and trends

**Weekly Patterns:**
- Weekly cycles in generation
- Seasonal week-over-week changes

**Monthly Patterns:**
- Seasonal variations (summer vs. winter)
- Monthly averages by source
- Peak demand months

**Yearly Overview:**
- Annual totals and trends
- Year-over-year comparisons (if multi-year data)

### 3. PCA Analysis

Principal Component Analysis reveals:
- **Energy Source Relationships**: Which sources tend to increase/decrease together
- **Variance Explained**: How much of the total variation is captured by main components
- **Component Interpretation**: What each principal component represents (e.g., baseload vs. peaking sources)
- **Correlation Patterns**: Strong and weak correlations between energy sources

**Example Insights:**
- Natural gas generation dominates the energy generation
- Nuclear provides consistent baseload with minimal variation

## 📈 Sample Visualizations

The project includes various visualization types:

- **Stacked Area Charts**: Showing generation mix over time
- **Line Plots**: Individual source trends across time scales
- **Heatmaps**: Hourly/daily patterns by source
- **Box Plots**: Distribution of generation by source
- **Correlation Matrix**: Relationships between energy sources
- **PCA Biplots**: Principal components and variable loadings
- **Scree Plots**: Variance explained by each component

## 🎯 Learning Outcomes

This project demonstrates proficiency in:

- Data acquisition from government APIs (EIA)
- Time series data manipulation with Pandas
- Multi-scale temporal analysis
- Exploratory Data Analysis (EDA)
- Statistical visualization techniques
- Dimensionality reduction (PCA)
- Pattern recognition in energy data
- Scientific computing with Python
- Clear communication of analytical findings

## 💡 Insights & Conclusions

- Natural gas is the dominant source
- Nuclear provides steady baseload power with minimal variation
- Summer months show increased generation due to cooling demand
- Renewable energy sources have very low share in energy generation

## 🔄 Future Enhancements

- [ ] Multi-year analysis to identify long-term trends
- [ ] Weather data integration to correlate with renewable generation
- [ ] Price analysis (cost per MWh by source)
- [ ] Carbon emissions calculations by source
- [ ] Interactive dashboards with Plotly/Dash
- [ ] Machine learning models for generation forecasting
- [ ] Geographic analysis by region/state
- [ ] Economic analysis of energy source competitiveness

## 🤝 Contributing

Contributions, suggestions, and improvements are welcome! Feel free to:
- Open issues for bugs or suggestions
- Submit pull requests with enhancements
- Share your own analysis ideas

## 📝 License

This project is part of a Big Data Analytics course and follows academic guidelines for educational projects.

## 👨‍💻 Author

**Yussuf Kadir**
- GitHub: [@Yussufkadir](https://github.com/Yussufkadir)

## 🙏 Acknowledgments

- **U.S. Energy Information Administration (EIA)** for providing open access to energy data
- Course instructors and peers for guidance and feedback
- Python data science community for excellent libraries and documentation

## 📚 Resources & References

- [EIA Open Data](https://www.eia.gov/opendata/)
- [EIA Electricity Data Browser](https://www.eia.gov/electricity/data/browser/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Scikit-learn PCA Guide](https://scikit-learn.org/stable/modules/decomposition.html#pca)
- [Python Data Science Handbook](https://jakevdp.github.io/PythonDataScienceHandbook/)

## 📞 Dataset Information

**Data Source**: U.S. Energy Information Administration (EIA)  
**Dataset**: Hourly Electric Grid Monitor  
**Time Period**: One year of hourly data  
**Variables**: Electricity generation by energy source (MWh)  
**Frequency**: Hourly recordings aggregated to multiple time scales  
