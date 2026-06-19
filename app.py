
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="HR Workforce Analytics Dashboard", layout="wide")

st.title("HR Workforce Analytics Dashboard")
st.caption("Workforce, portfolio, collection, performance, risk, and management insights")


# =========================
# Helper Functions
# =========================

def to_number(series):
    return pd.to_numeric(
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("%", "", regex=False),
        errors="coerce"
    ).fillna(0)


def clean_columns(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def safe_read(excel, sheet_name):
    try:
        return clean_columns(pd.read_excel(excel, sheet_name=sheet_name))
    except Exception:
        return pd.DataFrame()


def add_missing_columns(df, columns):
    for col in columns:
        if col not in df.columns:
            df[col] = 0
    return df


def format_money(value):
    return f"{value:,.0f}"


def format_pct(value):
    if pd.isna(value):
        value = 0
    if abs(value) <= 1:
        return f"{value * 100:.2f}%"
    return f"{value:.2f}%"


def normalize_percentage(series):
    s = to_number(series)
    if s.abs().max() <= 1:
        return s * 100
    return s


def bar_chart(df, x, y, title, ascending=False):
    if df.empty or x not in df.columns or y not in df.columns:
        st.info(f"No data available for {title}")
        return

    fig = px.bar(
        df.sort_values(y, ascending=ascending),
        x=x,
        y=y,
        text_auto=True,
        title=title
    )
    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True)


def pie_chart(df, names, values, title):
    if df.empty or names not in df.columns or values not in df.columns or df[values].sum() == 0:
        st.info(f"No data available for {title}")
        return

    fig = px.pie(df, names=names, values=values, title=title, hole=0.35)
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)


def concentration_table(df, name_col, value_col, threshold=0.5):
    if df.empty or name_col not in df.columns or value_col not in df.columns:
        return pd.DataFrame()

    temp = df[[name_col, value_col]].copy()
    temp = temp.sort_values(value_col, ascending=False)

    total = temp[value_col].sum()
    if total == 0:
        return pd.DataFrame()

    temp["Share %"] = temp[value_col] / total * 100
    temp["Cumulative Share %"] = temp["Share %"].cumsum()

    result = temp[temp["Cumulative Share %"] <= threshold * 100].copy()

    if len(result) < len(temp):
        result = pd.concat([result, temp.iloc[[len(result)]]])

    return result


def rank_score_high_is_good(series):
    return series.rank(pct=True) * 100


def rank_score_low_is_good(series):
    return (1 - series.rank(pct=True)) * 100


# =========================
# Upload File
# =========================

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])

if uploaded_file is None:
    st.info("Please upload the Q1 2026 Excel file.")
    st.stop()

excel = pd.ExcelFile(uploaded_file)

employees = safe_read(excel, "Employees")
branches = safe_read(excel, "Branches")
areas = safe_read(excel, "Areas")
clients = safe_read(excel, "client")


# =========================
# Prepare Employees
# =========================

employees = employees.rename(columns={
    "Name": "Employee",
    "Name ": "Employee",
    "Outstanding Portfolio 31/12/2024": "Portfolio 2024",
    "Outstanding Portfolio 31/12/2025": "Portfolio 2025",
    "Outstanding Portfolio 31/03/2026": "Portfolio 2026",
    "growth 25-26 VALUE": "Portfolio Growth %",
    "# Of Loans 31/12/2024": "Loans 2024",
    "# Of Loans 31/12/2025": "Loans 2025",
    "# Of Loans 31/03/2026": "Loans 2026",
    "growth 25-26 number": "Loans Growth %",
    "LOAN ISSUED New": "Loan Issued New",
    "LOAN ISSUED Returned": "Loan Issued Returned",
    "Loan Issued Total": "Loan Issued Total",
    "Loan Issued Total ": "Loan Issued Total",
    "# of Loan Issued New": "# Loan Issued New",
    "# of Loan Issued Rerturned": "# Loan Issued Returned",
    "# of Loan Issued": "# Loan Issued",
    "# of Loan Issued ": "# Loan Issued",
    "Clients Count": "Customers",
    "Collection During Period": "Collection",
    "Collection During Period ": "Collection",
    "Collection Achievement %": "Collection Achievement %",
    "Loan Sent To Collection": "Loans Sent To Collection",
    "Stage 3 Provision": "Stage 3 Provision",
    "Shift ": "Shift"
})

employee_cols = [
    "Employee", "Branch", "Portfolio 2025", "Portfolio 2026",
    "Portfolio Growth %", "Loans 2026", "Customers",
    "Collection", "Collection Target", "Collection Achievement %",
    "Loan Issued Total", "# Loan Issued", "Loans Sent To Collection",
    "Provision", "Stage 3 Provision", "Refinance", "Shift", "BAR"
]

employees = add_missing_columns(employees, employee_cols)

for col in employee_cols:
    if col not in ["Employee", "Branch"]:
        employees[col] = to_number(employees[col])

employees["Portfolio Growth %"] = normalize_percentage(employees["Portfolio Growth %"])
employees["Collection Achievement %"] = normalize_percentage(employees["Collection Achievement %"])
employees["Employee"] = employees["Employee"].astype(str).str.strip()
employees["Branch"] = employees["Branch"].astype(str).str.strip()

if "Hire Date" in employees.columns:
    employees["Hire Date"] = pd.to_datetime(employees["Hire Date"], errors="coerce")
    employees["Years of Service"] = ((pd.Timestamp.today() - employees["Hire Date"]).dt.days / 365.25).fillna(0)
else:
    employees["Years of Service"] = 0


# =========================
# Prepare Branches
# =========================

branches = branches.rename(columns={
    "Outstanding Portfolio 31/12/2025": "Portfolio 2025",
    "Outstanding Portfolio 31/03/2026": "Portfolio 2026",
    "growth 25-26 VALUE": "Portfolio Growth %",
    "# Of Loans 31/12/2025": "Loans 2025",
    "# Of Loans 31/03/2026": "Loans 2026",
    "growth 25-26 number": "Loans Growth %",
    "LOAN ISSUED New": "Loan Issued New",
    "LOAN ISSUED Returned": "Loan Issued Returned",
    "Loan Issued Total": "Loan Issued Total",
    "Loan Issued Total ": "Loan Issued Total",
    "# of Loan Issued New": "# Loan Issued New",
    "# of Loan Issued Rerturned": "# Loan Issued Returned",
    "# of Loan Issued": "# Loan Issued",
    "# of Loan Issued ": "# Loan Issued",
    "Clients Count": "Customers",
    "Collection During Period": "Collection",
    "Collection During Period ": "Collection",
    "Collection Achievement %": "Collection Achievement %",
    "Loan Sent To Collection": "Loans Sent To Collection",
    "Stage 3 Provision": "Stage 3 Provision",
    "Shift ": "Shift"
})

branch_cols = [
    "Branch", "Portfolio 2025", "Portfolio 2026", "Portfolio Growth %",
    "Loans 2026", "Customers", "Collection", "Collection Target",
    "Collection Achievement %", "Loan Issued Total", "# Loan Issued",
    "Loans Sent To Collection", "Provision", "Stage 3 Provision",
    "Refinance", "Shift", "BAR"
]

branches = add_missing_columns(branches, branch_cols)

for col in branch_cols:
    if col != "Branch":
        branches[col] = to_number(branches[col])

branches["Portfolio Growth %"] = normalize_percentage(branches["Portfolio Growth %"])
branches["Collection Achievement %"] = normalize_percentage(branches["Collection Achievement %"])
branches["Branch"] = branches["Branch"].astype(str).str.strip()


# =========================
# Prepare Areas
# =========================

areas = areas.rename(columns={
    "Outstanding Portfolio 31/12/2025": "Portfolio 2025",
    "Outstanding Portfolio 31/03/2026": "Portfolio 2026",
    "growth 25-26 VALUE": "Portfolio Growth %",
    "# Of Loans 31/12/2025": "Loans 2025",
    "# Of Loans 31/03/2026": "Loans 2026",
    "growth 25-26 number": "Loans Growth %",
    "LOAN ISSUED New": "Loan Issued New",
    "LOAN ISSUED Returned": "Loan Issued Returned",
    "Loan Issued Total": "Loan Issued Total",
    "Loan Issued Total ": "Loan Issued Total",
    "# of Loan Issued New": "# Loan Issued New",
    "# of Loan Issued Rerturned": "# Loan Issued Returned",
    "# of Loan Issued": "# Loan Issued",
    "# of Loan Issued ": "# Loan Issued",
    "Number of Clients": "Customers",
    "Collection During Period": "Collection",
    "Collection During Period ": "Collection",
    "Collection Achievement %": "Collection Achievement %",
    "Loan Sent To Collection": "Loans Sent To Collection",
    "Stage 3 Provision": "Stage 3 Provision",
    "Shift ": "Shift"
})

area_cols = [
    "Area", "Portfolio 2025", "Portfolio 2026", "Portfolio Growth %",
    "Loans 2026", "Customers", "Collection", "Collection Target",
    "Collection Achievement %", "Loan Issued Total", "# Loan Issued",
    "Loans Sent To Collection", "Provision", "Stage 3 Provision",
    "Refinance", "Shift", "BAR"
]

areas = add_missing_columns(areas, area_cols)

for col in area_cols:
    if col != "Area":
        areas[col] = to_number(areas[col])

areas["Portfolio Growth %"] = normalize_percentage(areas["Portfolio Growth %"])
areas["Collection Achievement %"] = normalize_percentage(areas["Collection Achievement %"])
areas["Area"] = areas["Area"].astype(str).str.strip()


# =========================
# Prepare Clients
# =========================

if not clients.empty:
    clients = clients.rename(columns={
        "Name": "Client",
        "NO of Loans": "Client Loans",
        "NO of Customers": "Client Customers",
        "Contract amount": "Contract Amount",
        "Outstanding amount": "Outstanding Amount"
    })

    for col in ["Client Loans", "Client Customers", "Contract Amount", "Outstanding Amount"]:
        if col in clients.columns:
            clients[col] = to_number(clients[col])


# =========================
# Filters
# =========================

st.sidebar.header("Filters")

all_branches = sorted(employees["Branch"].dropna().unique())

selected_branches = st.sidebar.multiselect(
    "Branch",
    all_branches,
    default=all_branches
)

employees_filtered = employees[employees["Branch"].isin(selected_branches)].copy()
branches_filtered = branches[branches["Branch"].isin(selected_branches)].copy()

selected_employees = st.sidebar.multiselect(
    "Employee",
    sorted(employees_filtered["Employee"].dropna().unique()),
    default=sorted(employees_filtered["Employee"].dropna().unique())
)

employees_filtered = employees_filtered[
    employees_filtered["Employee"].isin(selected_employees)
].copy()


# =========================
# Talent Segmentation and Overall Score
# =========================

employees_filtered["Growth Score"] = rank_score_high_is_good(employees_filtered["Portfolio Growth %"])
employees_filtered["Collection Score"] = rank_score_high_is_good(employees_filtered["Collection Achievement %"])
employees_filtered["BAR Score"] = rank_score_low_is_good(employees_filtered["BAR"])

employees_filtered["Performance Score"] = (
    employees_filtered["Growth Score"] * 0.40 +
    employees_filtered["Collection Score"] * 0.40 +
    employees_filtered["BAR Score"] * 0.20
)

employees_filtered["Potential Score"] = (
    employees_filtered["Growth Score"] * 0.50 +
    employees_filtered["Collection Score"] * 0.30 +
    employees_filtered["BAR Score"] * 0.20
)

employees_filtered["Overall Score"] = (
    employees_filtered["Growth Score"] * 0.35 +
    employees_filtered["Collection Score"] * 0.45 +
    employees_filtered["BAR Score"] * 0.20
)


def classify_bcg(row):
    performance = row["Performance Score"]
    potential = row["Potential Score"]

    if performance >= 70 and potential >= 70:
        return "Stars"
    elif performance >= 70 and potential < 70:
        return "Cash Cows"
    elif performance < 70 and potential >= 70:
        return "Question Marks"
    else:
        return "Dogs"


employees_filtered["Talent Segment"] = employees_filtered.apply(classify_bcg, axis=1)


# =========================
# Executive KPIs
# =========================

total_portfolio = areas["Portfolio 2026"].sum()
total_customers = areas["Customers"].sum()
total_collection = areas["Collection"].sum()
total_loans = areas["Loans 2026"].sum()

average_growth = (
    (areas["Portfolio 2026"].sum() - areas["Portfolio 2025"].sum())
    / areas["Portfolio 2025"].sum()
    if areas["Portfolio 2025"].sum() > 0 else 0
)

total_issued = areas["Loan Issued Total"].sum()
total_collection_target = areas["Collection Target"].sum()
collection_achievement = (
    total_collection / total_collection_target
    if total_collection_target > 0 else 0
)


# =========================
# Tabs
# =========================

tabs = st.tabs([
    "Executive Dashboard",
    "Area Performance",
    "Branch Performance",
    "Employee Performance",
    "Collection Analytics",
    "Portfolio Concentration",
    "Risk Indicators",
    "Talent Segmentation",
    "Best Overall Employees",
    "Smart Insights",
    "Data Preview"
])


# =========================
# Executive Dashboard
# =========================

with tabs[0]:
    st.subheader("Executive Dashboard")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Portfolio", format_money(total_portfolio))
    c2.metric("Total Customers", format_money(total_customers))
    c3.metric("Total Collection", format_money(total_collection))
    c4.metric("Average Growth", format_pct(average_growth))
    c5.metric("Total Loans", format_money(total_loans))

    c6, c7, c8 = st.columns(3)
    c6.metric("Total Issued Loans Amount", format_money(total_issued))
    c7.metric("Collection Target", format_money(total_collection_target))
    c8.metric("Collection Achievement", format_pct(collection_achievement))

    col1, col2 = st.columns(2)

    with col1:
        pie_chart(
            areas.sort_values("Portfolio 2026", ascending=False),
            "Area",
            "Portfolio 2026",
            "Portfolio by Area"
        )

    with col2:
        bar_chart(
            areas.sort_values("Portfolio Growth %", ascending=False),
            "Area",
            "Portfolio Growth %",
            "Area Growth %",
            ascending=False
        )

    col3, col4 = st.columns(2)

    with col3:
        bar_chart(
            areas.sort_values("Collection", ascending=False),
            "Area",
            "Collection",
            "Collection by Area",
            ascending=False
        )

    with col4:
        bar_chart(
            areas.sort_values("Customers", ascending=False),
            "Area",
            "Customers",
            "Customers by Area",
            ascending=False
        )


# =========================
# Area Performance
# =========================

with tabs[1]:
    st.subheader("Area Performance")

    col1, col2 = st.columns(2)

    with col1:
        bar_chart(
            areas.sort_values("Portfolio 2026", ascending=False),
            "Area",
            "Portfolio 2026",
            "Areas Ranked by Portfolio",
            ascending=False
        )

    with col2:
        bar_chart(
            areas.sort_values("Collection Achievement %", ascending=False),
            "Area",
            "Collection Achievement %",
            "Areas Ranked by Collection Achievement",
            ascending=False
        )

    st.dataframe(areas.sort_values("Portfolio 2026", ascending=False), use_container_width=True)


# =========================
# Branch Performance
# =========================

with tabs[2]:
    st.subheader("Branch Performance")

    col1, col2 = st.columns(2)

    with col1:
        bar_chart(
            branches_filtered.sort_values("Portfolio Growth %", ascending=False).head(10),
            "Branch",
            "Portfolio Growth %",
            "Top 10 Branches by Growth",
            ascending=False
        )

    with col2:
        bar_chart(
            branches_filtered.sort_values("Portfolio Growth %", ascending=True).head(10),
            "Branch",
            "Portfolio Growth %",
            "Bottom 10 Branches by Growth",
            ascending=True
        )

    st.write("Top Branches by Portfolio")
    st.dataframe(branches_filtered.sort_values("Portfolio 2026", ascending=False).head(20), use_container_width=True)

    st.write("Best Branches by Collection Achievement")
    st.dataframe(branches_filtered.sort_values("Collection Achievement %", ascending=False).head(10), use_container_width=True)

    st.write("Lowest Risk Branches by BAR")
    st.dataframe(branches_filtered.sort_values("BAR", ascending=True).head(10), use_container_width=True)


# =========================
# Employee Performance
# =========================

with tabs[3]:
    st.subheader("Employee Performance")

    col1, col2 = st.columns(2)

    with col1:
        bar_chart(
            employees_filtered.sort_values("Portfolio Growth %", ascending=False).head(10),
            "Employee",
            "Portfolio Growth %",
            "Top 10 Employees by Growth",
            ascending=False
        )

    with col2:
        bar_chart(
            employees_filtered.sort_values("Portfolio Growth %", ascending=True).head(10),
            "Employee",
            "Portfolio Growth %",
            "Bottom 10 Employees by Growth",
            ascending=True
        )

    st.write("Top Employees by Portfolio Size")
    st.dataframe(
        employees_filtered[["Employee", "Branch", "Portfolio 2026"]]
        .sort_values("Portfolio 2026", ascending=False)
        .head(20),
        use_container_width=True
    )

    st.write("Top Employees by Customers")
    st.dataframe(
        employees_filtered[["Employee", "Branch", "Customers"]]
        .sort_values("Customers", ascending=False)
        .head(20),
        use_container_width=True
    )

    st.write("Top Employees by Collection")
    st.dataframe(
        employees_filtered[["Employee", "Branch", "Collection"]]
        .sort_values("Collection", ascending=False)
        .head(20),
        use_container_width=True
    )


# =========================
# Collection Analytics
# =========================

with tabs[4]:
    st.subheader("Collection Analytics")

    col1, col2 = st.columns(2)

    with col1:
        bar_chart(
            employees_filtered.sort_values("Collection Achievement %", ascending=False).head(10),
            "Employee",
            "Collection Achievement %",
            "Best Employees by Collection Achievement",
            ascending=False
        )

    with col2:
        bar_chart(
            employees_filtered.sort_values("Collection Achievement %", ascending=True).head(10),
            "Employee",
            "Collection Achievement %",
            "Weakest Employees by Collection Achievement",
            ascending=True
        )

    st.write("Collection Achievement by Area")
    st.dataframe(
        areas[["Area", "Collection", "Collection Target", "Collection Achievement %"]]
        .sort_values("Collection Achievement %", ascending=False),
        use_container_width=True
    )

    st.write("Collection Achievement by Branch")
    st.dataframe(
        branches_filtered[["Branch", "Collection", "Collection Target", "Collection Achievement %"]]
        .sort_values("Collection Achievement %", ascending=False),
        use_container_width=True
    )


# =========================
# Portfolio Concentration
# =========================

with tabs[5]:
    st.subheader("Portfolio Concentration Risk")

    st.write("Employees Carrying 50% of Portfolio")
    st.dataframe(concentration_table(employees_filtered, "Employee", "Portfolio 2026", 0.5), use_container_width=True)

    st.write("Branches Carrying 50% of Portfolio")
    st.dataframe(concentration_table(branches_filtered, "Branch", "Portfolio 2026", 0.5), use_container_width=True)

    st.write("Areas Carrying 50% of Portfolio")
    st.dataframe(concentration_table(areas, "Area", "Portfolio 2026", 0.5), use_container_width=True)

    st.write("80/20 Employee Portfolio Analysis")
    st.dataframe(concentration_table(employees_filtered, "Employee", "Portfolio 2026", 0.8), use_container_width=True)

    if not clients.empty and "Outstanding Amount" in clients.columns:
        st.write("Top Clients by Outstanding Amount")
        st.dataframe(clients.sort_values("Outstanding Amount", ascending=False).head(20), use_container_width=True)


# =========================
# Risk Indicators
# =========================

with tabs[6]:
    st.subheader("Risk Indicators")

    lower_is_better = [
        "Loans Sent To Collection",
        "Provision",
        "Stage 3 Provision",
        "Refinance",
        "Shift",
        "BAR"
    ]

    for metric in lower_is_better:
        st.write(f"Best Employees by Lowest {metric}")
        st.dataframe(
            employees_filtered[["Employee", "Branch", metric]]
            .sort_values(metric, ascending=True)
            .head(10),
            use_container_width=True
        )

        st.write(f"Highest Risk Employees by {metric}")
        st.dataframe(
            employees_filtered[["Employee", "Branch", metric]]
            .sort_values(metric, ascending=False)
            .head(10),
            use_container_width=True
        )

    st.write("Employees Requiring Follow-up")

    follow_up = employees_filtered[
        (employees_filtered["Portfolio Growth %"] < 0) |
        (employees_filtered["Collection Achievement %"] < 90) |
        (employees_filtered["Loans Sent To Collection"] > 0) |
        (employees_filtered["BAR"] > employees_filtered["BAR"].quantile(0.75))
    ].copy()

    st.dataframe(
        follow_up[[
            "Employee", "Branch", "Portfolio 2026", "Portfolio Growth %",
            "Collection Achievement %", "Loans Sent To Collection",
            "Provision", "Stage 3 Provision", "BAR"
        ]].sort_values("Overall Score", ascending=True),
        use_container_width=True
    )


# =========================
# Talent Segmentation
# =========================

with tabs[7]:
    st.subheader("BCG Talent Segmentation")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Stars", len(employees_filtered[employees_filtered["Talent Segment"] == "Stars"]))
    c2.metric("Cash Cows", len(employees_filtered[employees_filtered["Talent Segment"] == "Cash Cows"]))
    c3.metric("Question Marks", len(employees_filtered[employees_filtered["Talent Segment"] == "Question Marks"]))
    c4.metric("Dogs", len(employees_filtered[employees_filtered["Talent Segment"] == "Dogs"]))

    fig = px.scatter(
        employees_filtered,
        x="Potential Score",
        y="Performance Score",
        color="Talent Segment",
        size="Portfolio 2026",
        hover_name="Employee",
        hover_data=[
            "Branch",
            "Portfolio Growth %",
            "Collection Achievement %",
            "BAR",
            "Overall Score"
        ],
        title="BCG Talent Matrix: Performance vs Potential"
    )
    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)

    st.write("Talent Segmentation Table")
    st.dataframe(
        employees_filtered[[
            "Employee", "Branch", "Portfolio 2026",
            "Portfolio Growth %", "Collection Achievement %",
            "BAR", "Growth Score", "Collection Score", "BAR Score",
            "Performance Score", "Potential Score", "Overall Score",
            "Talent Segment"
        ]].sort_values("Overall Score", ascending=False),
        use_container_width=True
    )


# =========================
# Best Overall Employees
# =========================

with tabs[8]:
    st.subheader("Best Overall Employees")

    st.caption("Ranking is based on portfolio growth, collection achievement, and low BAR risk.")

    c1, c2, c3, c4 = st.columns(4)

    if not employees_filtered.empty:
        best_growth = employees_filtered.sort_values("Portfolio Growth %", ascending=False).head(1)
        best_collection = employees_filtered.sort_values("Collection Achievement %", ascending=False).head(1)
        lowest_bar = employees_filtered.sort_values("BAR", ascending=True).head(1)
        best_overall = employees_filtered.sort_values("Overall Score", ascending=False).head(1)

        c1.metric("Best Overall", best_overall["Employee"].iloc[0])
        c2.metric("Best Growth", best_growth["Employee"].iloc[0])
        c3.metric("Best Collection", best_collection["Employee"].iloc[0])
        c4.metric("Lowest BAR Risk", lowest_bar["Employee"].iloc[0])

    st.write("Top 20 Overall Employees")

    top_overall = employees_filtered[[
        "Employee", "Branch", "Portfolio Growth %",
        "Collection Achievement %", "BAR",
        "Growth Score", "Collection Score", "BAR Score",
        "Overall Score", "Talent Segment"
    ]].sort_values("Overall Score", ascending=False).head(20)

    st.dataframe(top_overall, use_container_width=True)

    bar_chart(top_overall, "Employee", "Overall Score", "Top 20 Employees by Overall Score", ascending=False)

    st.write("Best Balanced Employees: Growth + Collection + Lowest BAR")
    balanced = employees_filtered[
        (employees_filtered["Growth Score"] >= 70) &
        (employees_filtered["Collection Score"] >= 70) &
        (employees_filtered["BAR Score"] >= 70)
    ].sort_values("Overall Score", ascending=False)

    st.dataframe(
        balanced[[
            "Employee", "Branch", "Portfolio Growth %",
            "Collection Achievement %", "BAR",
            "Overall Score", "Talent Segment"
        ]],
        use_container_width=True
    )


# =========================
# Smart Insights
# =========================

with tabs[9]:
    st.subheader("Smart Insights")

    negative_growth_count = len(employees_filtered[employees_filtered["Portfolio Growth %"] < 0])
    below_target_count = len(employees_filtered[employees_filtered["Collection Achievement %"] < 90])

    top_growth = employees_filtered.sort_values("Portfolio Growth %", ascending=False).head(3)["Employee"].tolist()
    bottom_growth = employees_filtered.sort_values("Portfolio Growth %", ascending=True).head(3)["Employee"].tolist()
    top_collection = employees_filtered.sort_values("Collection Achievement %", ascending=False).head(3)["Employee"].tolist()
    top_overall = employees_filtered.sort_values("Overall Score", ascending=False).head(3)["Employee"].tolist()

    st.info(f"Total portfolio based on Areas sheet is {format_money(total_portfolio)}.")
    st.info(f"Overall portfolio growth is {format_pct(average_growth)}.")
    st.info(f"{negative_growth_count} employees have negative portfolio growth.")
    st.info(f"{below_target_count} employees are below 90% collection achievement.")
    st.info("Top overall employees: " + ", ".join(top_overall))
    st.info("Top growth employees: " + ", ".join(top_growth))
    st.info("Employees requiring growth support: " + ", ".join(bottom_growth))
    st.info("Best collection achievement employees: " + ", ".join(top_collection))

    st.write("Management Interpretation")
    st.write("""
    This dashboard supports staffing decisions, performance discussions, training needs analysis,
    incentive design, succession planning, and risk monitoring.
    The BCG Talent Segmentation helps management identify Stars, Cash Cows, Question Marks,
    and Dogs based on growth, collection achievement, and BAR risk.
    """)


# =========================
# Data Preview
# =========================

with tabs[10]:
    st.subheader("Data Preview")

    st.write("Employees")
    st.dataframe(employees.head(50), use_container_width=True)

    st.write("Branches")
    st.dataframe(branches.head(50), use_container_width=True)

    st.write("Areas")
    st.dataframe(areas.head(50), use_container_width=True)

    if not clients.empty:
        st.write("Clients")
        st.dataframe(clients.head(50), use_container_width=True)
