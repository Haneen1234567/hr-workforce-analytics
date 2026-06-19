
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="HR Workforce Analytics Dashboard", layout="wide")

st.title("HR Workforce Analytics Dashboard")
st.caption("Portfolio, collection, employee performance, risk, and talent segmentation")


# =========================
# Helpers
# =========================

def clean_columns(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def read_sheet(excel, sheet_name):
    try:
        return clean_columns(pd.read_excel(excel, sheet_name=sheet_name))
    except Exception:
        return pd.DataFrame()


def to_number(s):
    return pd.to_numeric(
        s.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.strip(),
        errors="coerce"
    ).fillna(0)


def ensure_cols(df, cols):
    for c in cols:
        if c not in df.columns:
            df[c] = 0
    return df


def money(x):
    return f"{x:,.0f}"


def pct(x):
    if pd.isna(x):
        x = 0
    if abs(x) <= 1:
        x = x * 100
    return f"{x:.2f}%"


def normalize_pct(s):
    s = to_number(s)
    if len(s) and s.abs().max() <= 1:
        return s * 100
    return s


def bar(df, x, y, title, ascending=False, top_n=None):
    if df.empty or x not in df.columns or y not in df.columns:
        st.info(f"No data available for {title}")
        return

    d = df.copy().sort_values(y, ascending=ascending)
    if top_n:
        d = d.head(top_n)

    fig = px.bar(d, x=x, y=y, text_auto=True, title=title)
    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True)


def pie(df, names, values, title):
    if df.empty or names not in df.columns or values not in df.columns or df[values].sum() == 0:
        st.info(f"No data available for {title}")
        return

    fig = px.pie(df, names=names, values=values, hole=0.35, title=title)
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)


def concentration(df, name_col, value_col, threshold=0.5):
    if df.empty or name_col not in df.columns or value_col not in df.columns:
        return pd.DataFrame()

    d = df[[name_col, value_col]].copy().sort_values(value_col, ascending=False)
    total = d[value_col].sum()

    if total == 0:
        return pd.DataFrame()

    d["Share %"] = d[value_col] / total * 100
    d["Cumulative Share %"] = d["Share %"].cumsum()

    result = d[d["Cumulative Share %"] <= threshold * 100].copy()
    if len(result) < len(d):
        result = pd.concat([result, d.iloc[[len(result)]]])

    return result


def high_score(s):
    return s.rank(pct=True) * 100


def low_score(s):
    return (1 - s.rank(pct=True)) * 100


# =========================
# Upload
# =========================

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])

if uploaded_file is None:
    st.info("Upload Q1 2026 Excel file to start.")
    st.stop()

excel = pd.ExcelFile(uploaded_file)

employees = read_sheet(excel, "Employees")
branches = read_sheet(excel, "Branches")
areas = read_sheet(excel, "Areas")
clients = read_sheet(excel, "client")
cases_area = read_sheet(excel, "Collection_Cases_Area")
cases_branch = read_sheet(excel, "Collection_Cases_Branch")
cases_employee = read_sheet(excel, "Collection_Cases_Employees")


# =========================
# Employees
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
    "Shift ": "Shift"
})

employee_cols = [
    "Employee", "Branch", "Hire Date", "Portfolio 2025", "Portfolio 2026",
    "Portfolio Growth %", "Loans 2026", "Customers", "Collection",
    "Collection Target", "Collection Achievement %", "Loan Issued Total",
    "# Loan Issued", "Loans Sent To Collection", "Provision",
    "Stage 3 Provision", "Refinance", "Shift", "BAR"
]

employees = ensure_cols(employees, employee_cols)

for c in employee_cols:
    if c not in ["Employee", "Branch", "Hire Date"]:
        employees[c] = to_number(employees[c])

employees["Portfolio Growth %"] = normalize_pct(employees["Portfolio Growth %"])
employees["Collection Achievement %"] = normalize_pct(employees["Collection Achievement %"])
employees["Employee"] = employees["Employee"].astype(str).str.strip()
employees["Branch"] = employees["Branch"].astype(str).str.strip()

employees["Hire Date"] = pd.to_datetime(employees["Hire Date"], errors="coerce")
employees["Years of Service"] = ((pd.Timestamp.today() - employees["Hire Date"]).dt.days / 365.25).fillna(0)


# =========================
# Branches
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
    "Shift ": "Shift"
})

branch_cols = [
    "Branch", "Portfolio 2025", "Portfolio 2026", "Portfolio Growth %",
    "Loans 2026", "Customers", "Collection", "Collection Target",
    "Collection Achievement %", "Loan Issued Total", "# Loan Issued",
    "Loans Sent To Collection", "Provision", "Stage 3 Provision",
    "Refinance", "Shift"
]

branches = ensure_cols(branches, branch_cols)

for c in branch_cols:
    if c != "Branch":
        branches[c] = to_number(branches[c])

branches["Portfolio Growth %"] = normalize_pct(branches["Portfolio Growth %"])
branches["Collection Achievement %"] = normalize_pct(branches["Collection Achievement %"])
branches["Branch"] = branches["Branch"].astype(str).str.strip()


# =========================
# Areas
# =========================

areas = areas.rename(columns={
    "Outstanding Portfolio 31/12/2025": "Portfolio 2025",
    "Outstanding Portfolio 31/03/2026": "Portfolio 2026",
    "growth 25-26 VALUE": "Portfolio Growth %",
    "# Of Loans 31/12/2025": "Loans 2025",
    "# Of Loans 31/03/2026": "Loans 2026",
    "growth 25-26 number": "Loans Growth %",
    "LOAN ISSUED New": "Loan Issued New",
    "New Loan Issuance Growth %": "New Loan Issuance Growth %",
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
    "Shift ": "Shift"
})

area_cols = [
    "Area", "Portfolio 2025", "Portfolio 2026", "Portfolio Growth %",
    "Loans 2026", "Customers", "Collection", "Collection Target",
    "Collection Achievement %", "Loan Issued Total", "# Loan Issued",
    "New Loan Issuance Growth %", "Loans Sent To Collection",
    "Provision", "Stage 3 Provision", "Refinance", "Shift"
]

areas = ensure_cols(areas, area_cols)

for c in area_cols:
    if c != "Area":
        areas[c] = to_number(areas[c])

areas["Portfolio Growth %"] = normalize_pct(areas["Portfolio Growth %"])
areas["Collection Achievement %"] = normalize_pct(areas["Collection Achievement %"])
areas["New Loan Issuance Growth %"] = normalize_pct(areas["New Loan Issuance Growth %"])
areas["Area"] = areas["Area"].astype(str).str.strip()


# =========================
# Clients & Collection Cases
# =========================

if not clients.empty:
    clients = clients.rename(columns={
        "Name": "Client",
        "NO of Loans": "Client Loans",
        "NO of Customers": "Client Customers",
        "Contract amount": "Contract Amount",
        "Outstanding amount": "Outstanding Amount"
    })
    for c in ["Client Loans", "Client Customers", "Contract Amount", "Outstanding Amount"]:
        if c in clients.columns:
            clients[c] = to_number(clients[c])

for df in [cases_area, cases_branch, cases_employee]:
    if not df.empty:
        for c in df.columns:
            if c.lower() not in ["name", "id"]:
                df[c] = to_number(df[c])


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
# Smart Scores
# =========================

employees_filtered["Growth Score"] = high_score(employees_filtered["Portfolio Growth %"])
employees_filtered["Collection Score"] = high_score(employees_filtered["Collection Achievement %"])
employees_filtered["BAR Score"] = low_score(employees_filtered["BAR"])

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
    employees_filtered["Growth Score"] * 0.40 +
    employees_filtered["Collection Score"] * 0.40 +
    employees_filtered["BAR Score"] * 0.20
)

employees_filtered["Future Leaders Index"] = (
    employees_filtered["Growth Score"] * 0.50 +
    employees_filtered["Collection Score"] * 0.30 +
    low_score(employees_filtered["Years of Service"]) * 0.20
)


def classify_talent(row):
    p = row["Performance Score"]
    q = row["Potential Score"]

    if p >= 70 and q >= 70:
        return "Stars"
    elif p >= 70 and q < 70:
        return "Cash Cows"
    elif p < 70 and q >= 70:
        return "Question Marks"
    else:
        return "Dogs"


employees_filtered["Talent Segment"] = employees_filtered.apply(classify_talent, axis=1)


# =========================
# KPIs
# =========================

total_portfolio = areas["Portfolio 2026"].sum()
total_customers = areas["Customers"].sum()
total_collection = areas["Collection"].sum()
total_loans = areas["Loans 2026"].sum()
total_collection_target = areas["Collection Target"].sum()
total_issued = areas["Loan Issued Total"].sum()

average_growth = (
    (areas["Portfolio 2026"].sum() - areas["Portfolio 2025"].sum())
    / areas["Portfolio 2025"].sum()
    if areas["Portfolio 2025"].sum() else 0
)

collection_achievement = (
    total_collection / total_collection_target
    if total_collection_target else 0
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
    "Future Leaders",
    "Smart Insights",
    "Data Preview"
])


# =========================
# Executive Dashboard
# =========================

with tabs[0]:
    st.subheader("Executive Dashboard")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Portfolio", money(total_portfolio))
    c2.metric("Total Customers", money(total_customers))
    c3.metric("Total Collection", money(total_collection))
    c4.metric("Average Growth", pct(average_growth))
    c5.metric("Total Loans", money(total_loans))

    c6, c7, c8 = st.columns(3)
    c6.metric("Total Issued Loans Amount", money(total_issued))
    c7.metric("Collection Target", money(total_collection_target))
    c8.metric("Collection Achievement", pct(collection_achievement))

    col1, col2 = st.columns(2)
    with col1:
        pie(areas.sort_values("Portfolio 2026", ascending=False), "Area", "Portfolio 2026", "Portfolio by Area")
    with col2:
        bar(areas, "Area", "Portfolio Growth %", "Area Growth %", ascending=False)

    col3, col4 = st.columns(2)
    with col3:
        bar(areas, "Area", "Collection", "Collection by Area", ascending=False)
    with col4:
        bar(areas, "Area", "Customers", "Customers by Area", ascending=False)


# =========================
# Area Performance
# =========================

with tabs[1]:
    st.subheader("Area Performance")

    col1, col2 = st.columns(2)
    with col1:
        bar(areas, "Area", "Portfolio 2026", "Areas Ranked by Portfolio", ascending=False)
    with col2:
        bar(areas, "Area", "Collection Achievement %", "Areas Ranked by Collection Achievement", ascending=False)

    col3, col4 = st.columns(2)
    with col3:
        bar(areas, "Area", "New Loan Issuance Growth %", "New Loan Issuance Growth by Area", ascending=False)
    with col4:
        bar(areas, "Area", "Loans Sent To Collection", "Loans Sent To Collection by Area - Lower is Better", ascending=True)

    st.dataframe(areas.sort_values("Portfolio 2026", ascending=False), use_container_width=True)


# =========================
# Branch Performance
# =========================

with tabs[2]:
    st.subheader("Branch Performance")

    col1, col2 = st.columns(2)
    with col1:
        bar(branches_filtered, "Branch", "Portfolio Growth %", "Top Branches by Growth", ascending=False, top_n=10)
    with col2:
        bar(branches_filtered, "Branch", "Portfolio Growth %", "Weakest Branches by Growth", ascending=True, top_n=10)

    st.write("Top Branches by Portfolio")
    st.dataframe(branches_filtered.sort_values("Portfolio 2026", ascending=False).head(20), use_container_width=True)

    st.write("Best Branches by Collection Achievement")
    st.dataframe(branches_filtered.sort_values("Collection Achievement %", ascending=False).head(10), use_container_width=True)

    st.write("Lowest Risk Branches by Loans Sent To Collection")
    st.dataframe(branches_filtered.sort_values("Loans Sent To Collection", ascending=True).head(10), use_container_width=True)


# =========================
# Employee Performance
# =========================

with tabs[3]:
    st.subheader("Employee Performance")

    col1, col2 = st.columns(2)
    with col1:
        bar(employees_filtered, "Employee", "Portfolio Growth %", "Top 10 Employees by Growth", ascending=False, top_n=10)
    with col2:
        bar(employees_filtered, "Employee", "Portfolio Growth %", "Weakest 10 Employees by Growth", ascending=True, top_n=10)

    col3, col4 = st.columns(2)
    with col3:
        bar(employees_filtered, "Employee", "Collection Achievement %", "Top 10 Employees by Collection Achievement", ascending=False, top_n=10)
    with col4:
        bar(employees_filtered, "Employee", "BAR", "Best Employees by Lowest BAR", ascending=True, top_n=10)

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


# =========================
# Collection Analytics
# =========================

with tabs[4]:
    st.subheader("Collection Analytics")

    col1, col2 = st.columns(2)
    with col1:
        bar(employees_filtered, "Employee", "Collection Achievement %", "Best Employees by Collection Achievement", ascending=False, top_n=10)
    with col2:
        bar(employees_filtered, "Employee", "Collection Achievement %", "Weakest Employees by Collection Achievement", ascending=True, top_n=10)

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
    st.dataframe(concentration(employees_filtered, "Employee", "Portfolio 2026", 0.5), use_container_width=True)

    st.write("Branches Carrying 50% of Portfolio")
    st.dataframe(concentration(branches_filtered, "Branch", "Portfolio 2026", 0.5), use_container_width=True)

    st.write("Areas Carrying 50% of Portfolio")
    st.dataframe(concentration(areas, "Area", "Portfolio 2026", 0.5), use_container_width=True)

    st.write("80/20 Employee Portfolio Analysis")
    st.dataframe(concentration(employees_filtered, "Employee", "Portfolio 2026", 0.8), use_container_width=True)

    if not clients.empty and "Outstanding Amount" in clients.columns:
        st.write("Top Clients by Outstanding Amount")
        st.dataframe(
            clients.sort_values("Outstanding Amount", ascending=False).head(20),
            use_container_width=True
        )


# =========================
# Risk Indicators
# =========================

with tabs[6]:
    st.subheader("Risk Indicators - Lower is Better")

    risk_cols = [
        "Loans Sent To Collection",
        "Provision",
        "Stage 3 Provision",
        "Refinance",
        "Shift",
        "BAR"
    ]

    for metric in risk_cols:
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
            "Provision", "Stage 3 Provision", "BAR", "Overall Score"
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
            "Branch", "Portfolio Growth %",
            "Collection Achievement %", "BAR", "Overall Score"
        ],
        title="BCG Talent Matrix: Performance vs Potential"
    )
    fig.update_layout(height=620)
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        employees_filtered[[
            "Employee", "Branch", "Portfolio Growth %",
            "Collection Achievement %", "BAR",
            "Growth Score", "Collection Score", "BAR Score",
            "Performance Score", "Potential Score",
            "Overall Score", "Talent Segment"
        ]].sort_values("Overall Score", ascending=False),
        use_container_width=True
    )


# =========================
# Best Overall Employees
# =========================

with tabs[8]:
    st.subheader("Best Overall Employees")

    st.caption("Overall Score = 40% Growth + 40% Collection Achievement + 20% Low BAR Risk")

    if not employees_filtered.empty:
        best_overall = employees_filtered.sort_values("Overall Score", ascending=False).head(1)
        best_growth = employees_filtered.sort_values("Portfolio Growth %", ascending=False).head(1)
        best_collection = employees_filtered.sort_values("Collection Achievement %", ascending=False).head(1)
        lowest_bar = employees_filtered.sort_values("BAR", ascending=True).head(1)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Best Overall", best_overall["Employee"].iloc[0])
        c2.metric("Best Growth", best_growth["Employee"].iloc[0])
        c3.metric("Best Collection", best_collection["Employee"].iloc[0])
        c4.metric("Lowest BAR Risk", lowest_bar["Employee"].iloc[0])

    top_overall = employees_filtered[[
        "Employee", "Branch", "Portfolio Growth %",
        "Collection Achievement %", "BAR",
        "Growth Score", "Collection Score", "BAR Score",
        "Overall Score", "Talent Segment"
    ]].sort_values("Overall Score", ascending=False).head(20)

    st.write("Top 20 Overall Employees")
    st.dataframe(top_overall, use_container_width=True)

    bar(top_overall, "Employee", "Overall Score", "Top 20 Employees by Overall Score", ascending=False)

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
# Future Leaders
# =========================

with tabs[9]:
    st.subheader("Future Leaders Index")

    st.caption("Future Leaders Index = 50% Growth + 30% Collection Achievement + 20% Lower Years of Service")

    top_future = employees_filtered[[
        "Employee", "Branch", "Years of Service",
        "Portfolio Growth %", "Collection Achievement %",
        "Future Leaders Index", "Talent Segment"
    ]].sort_values("Future Leaders Index", ascending=False).head(20)

    st.dataframe(top_future, use_container_width=True)
    bar(top_future, "Employee", "Future Leaders Index", "Top 20 Future Leaders", ascending=False)


# =========================
# Smart Insights
# =========================

with tabs[10]:
    st.subheader("Smart Insights")

    if not employees_filtered.empty:
        negative_growth_count = len(employees_filtered[employees_filtered["Portfolio Growth %"] < 0])
        below_target_count = len(employees_filtered[employees_filtered["Collection Achievement %"] < 90])

        top_overall = employees_filtered.sort_values("Overall Score", ascending=False).head(3)["Employee"].tolist()
        top_growth = employees_filtered.sort_values("Portfolio Growth %", ascending=False).head(3)["Employee"].tolist()
        weak_growth = employees_filtered.sort_values("Portfolio Growth %", ascending=True).head(3)["Employee"].tolist()
        top_collection = employees_filtered.sort_values("Collection Achievement %", ascending=False).head(3)["Employee"].tolist()
        high_risk_bar = employees_filtered.sort_values("BAR", ascending=False).head(3)["Employee"].tolist()

        st.info(f"Total portfolio based on Areas sheet is {money(total_portfolio)}.")
        st.info(f"Overall portfolio growth is {pct(average_growth)}.")
        st.info(f"{negative_growth_count} employees have negative portfolio growth.")
        st.info(f"{below_target_count} employees are below 90% collection achievement.")
        st.info("Top overall employees: " + ", ".join(top_overall))
        st.info("Top growth employees: " + ", ".join(top_growth))
        st.info("Employees requiring growth support: " + ", ".join(weak_growth))
        st.info("Best collection achievement employees: " + ", ".join(top_collection))
        st.info("Highest BAR risk employees: " + ", ".join(high_risk_bar))

    st.write("Management Interpretation")
    st.write("""
    This dashboard supports performance reviews, staffing decisions, training needs analysis,
    incentive design, portfolio risk monitoring, and succession planning.
    The BCG Talent Segmentation identifies Stars, Cash Cows, Question Marks, and Dogs using
    growth, collection achievement, and BAR risk.
    """)


# =========================
# Data Preview
# =========================

with tabs[11]:
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

    if not cases_employee.empty:
        st.write("Collection Cases - Employees")
        st.dataframe(cases_employee.head(50), use_container_width=True)
