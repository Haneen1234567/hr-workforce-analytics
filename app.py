import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="HR Workforce Analytics Dashboard",
    layout="wide"
)

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


def safe_read(excel, sheet_name):
    try:
        return pd.read_excel(excel, sheet_name=sheet_name)
    except Exception:
        return pd.DataFrame()


def clean_columns(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def format_money(value):
    return f"{value:,.0f}"


def format_pct(value):
    return f"{value * 100:.2f}%"


def bar_chart(df, x, y, title, text=True):
    if df.empty:
        st.info(f"No data available for {title}")
        return

    fig = px.bar(
        df,
        x=x,
        y=y,
        text_auto=text,
        title=title
    )
    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True)


def pie_chart(df, names, values, title):
    if df.empty or df[values].sum() == 0:
        st.info(f"No data available for {title}")
        return

    fig = px.pie(
        df,
        names=names,
        values=values,
        title=title,
        hole=0.35
    )
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)


def top_table(df, name_col, metric_col, n=10, ascending=False):
    if df.empty or metric_col not in df.columns:
        return pd.DataFrame()

    return df[[name_col, metric_col]].sort_values(
        metric_col,
        ascending=ascending
    ).head(n)


def concentration_table(df, name_col, value_col, threshold=0.5):
    if df.empty or value_col not in df.columns:
        return pd.DataFrame()

    temp = df[[name_col, value_col]].copy()
    temp = temp.sort_values(value_col, ascending=False)

    total = temp[value_col].sum()
    if total == 0:
        return pd.DataFrame()

    temp["Share %"] = temp[value_col] / total
    temp["Cumulative Share %"] = temp["Share %"].cumsum()

    result = temp[temp["Cumulative Share %"] <= threshold].copy()

    if len(result) < len(temp):
        result = pd.concat([result, temp.iloc[[len(result)]]])

    result["Share %"] = result["Share %"].apply(lambda x: f"{x*100:.2f}%")
    result["Cumulative Share %"] = result["Cumulative Share %"].apply(lambda x: f"{x*100:.2f}%")

    return result


# =========================
# Upload File
# =========================

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])

if uploaded_file is None:
    st.info("Please upload the Q1 2026 Excel file.")
    st.stop()

excel = pd.ExcelFile(uploaded_file)

employees = clean_columns(safe_read(excel, "Employees"))
branches = clean_columns(safe_read(excel, "Branches"))
areas = clean_columns(safe_read(excel, "Areas"))
clients = clean_columns(safe_read(excel, "client"))
collection_area = clean_columns(safe_read(excel, "Collection_Cases_Area"))
collection_branch = clean_columns(safe_read(excel, "Collection_Cases_Branch"))
collection_employee = clean_columns(safe_read(excel, "Collection_Cases_Employees"))


# =========================
# Prepare Employees Sheet
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
    "Shift": "Shift",
    "Shift ": "Shift"
})

required_employee_cols = [
    "Employee", "Branch", "Portfolio 2025", "Portfolio 2026",
    "Portfolio Growth %", "Loans 2026", "Customers",
    "Collection", "Collection Target", "Collection Achievement %",
    "Loan Issued Total", "# Loan Issued", "Loans Sent To Collection",
    "Provision", "Stage 3 Provision", "Refinance", "Shift", "BAR"
]

for col in required_employee_cols:
    if col not in employees.columns:
        employees[col] = 0

numeric_employee_cols = [
    "Portfolio 2025", "Portfolio 2026", "Portfolio Growth %",
    "Loans 2026", "Customers", "Collection", "Collection Target",
    "Collection Achievement %", "Loan Issued Total", "# Loan Issued",
    "Loans Sent To Collection", "Provision", "Stage 3 Provision",
    "Refinance", "Shift", "BAR"
]

for col in numeric_employee_cols:
    employees[col] = to_number(employees[col])

employees["Employee"] = employees["Employee"].astype(str).str.strip()
employees["Branch"] = employees["Branch"].astype(str).str.strip()

if "Hire Date" in employees.columns:
    employees["Hire Date"] = pd.to_datetime(employees["Hire Date"], errors="coerce")
    employees["Years of Service"] = (
        (pd.Timestamp.today() - employees["Hire Date"]).dt.days / 365.25
    ).fillna(0)
else:
    employees["Years of Service"] = 0


# =========================
# Prepare Branches Sheet
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
    "Shift": "Shift",
    "Shift ": "Shift"
})

for col in [
    "Branch", "Portfolio 2025", "Portfolio 2026", "Portfolio Growth %",
    "Loans 2026", "Customers", "Collection", "Collection Target",
    "Collection Achievement %", "Loan Issued Total", "# Loan Issued",
    "Loans Sent To Collection", "Provision", "Stage 3 Provision",
    "Refinance", "Shift"
]:
    if col not in branches.columns:
        branches[col] = 0

for col in branches.columns:
    if col != "Branch":
        branches[col] = to_number(branches[col])

branches["Branch"] = branches["Branch"].astype(str).str.strip()


# =========================
# Prepare Areas Sheet
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
    "Shift": "Shift",
    "Shift ": "Shift"
})

for col in [
    "Area", "Portfolio 2025", "Portfolio 2026", "Portfolio Growth %",
    "Loans 2026", "Customers", "Collection", "Collection Target",
    "Collection Achievement %", "Loan Issued Total", "# Loan Issued",
    "Loans Sent To Collection", "Provision", "Stage 3 Provision",
    "Refinance", "Shift"
]:
    if col not in areas.columns:
        areas[col] = 0

for col in areas.columns:
    if col != "Area":
        areas[col] = to_number(areas[col])

areas["Area"] = areas["Area"].astype(str).str.strip()


# =========================
# Prepare Client Concentration Sheet
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
# Sidebar Filters
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
    "HR Productivity",
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
            "Area Growth %"
        )

    col3, col4 = st.columns(2)

    with col3:
        bar_chart(
            areas.sort_values("Collection", ascending=False),
            "Area",
            "Collection",
            "Collection by Area"
        )

    with col4:
        bar_chart(
            areas.sort_values("Customers", ascending=False),
            "Area",
            "Customers",
            "Customers by Area"
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
            "Areas Ranked by Portfolio"
        )

    with col2:
        bar_chart(
            areas.sort_values("Collection Achievement %", ascending=False),
            "Area",
            "Collection Achievement %",
            "Areas Ranked by Collection Achievement"
        )

    st.dataframe(
        areas.sort_values("Portfolio 2026", ascending=False),
        use_container_width=True
    )


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
            "Top 10 Branches by Growth"
        )

    with col2:
        bar_chart(
            branches_filtered.sort_values("Portfolio Growth %", ascending=True).head(10),
            "Branch",
            "Portfolio Growth %",
            "Bottom 10 Branches by Growth"
        )

    st.write("Top Branches by Portfolio")
    st.dataframe(
        branches_filtered.sort_values("Portfolio 2026", ascending=False).head(20),
        use_container_width=True
    )

    st.write("Best Branches by Collection Achievement")
    st.dataframe(
        branches_filtered.sort_values("Collection Achievement %", ascending=False).head(10),
        use_container_width=True
    )

    st.write("Worst Branches by Collection Achievement")
    st.dataframe(
        branches_filtered.sort_values("Collection Achievement %", ascending=True).head(10),
        use_container_width=True
    )


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
            "Top 10 Employees by Growth"
        )

    with col2:
        bar_chart(
            employees_filtered.sort_values("Portfolio Growth %", ascending=True).head(10),
            "Employee",
            "Portfolio Growth %",
            "Bottom 10 Employees by Growth"
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
            "Best Employees by Collection Achievement"
        )

    with col2:
        bar_chart(
            employees_filtered.sort_values("Collection Achievement %", ascending=True).head(10),
            "Employee",
            "Collection Achievement %",
            "Worst Employees by Collection Achievement"
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
    st.dataframe(
        concentration_table(employees_filtered, "Employee", "Portfolio 2026", 0.5),
        use_container_width=True
    )

    st.write("Branches Carrying 50% of Portfolio")
    st.dataframe(
        concentration_table(branches_filtered, "Branch", "Portfolio 2026", 0.5),
        use_container_width=True
    )

    st.write("Areas Carrying 50% of Portfolio")
    st.dataframe(
        concentration_table(areas, "Area", "Portfolio 2026", 0.5),
        use_container_width=True
    )

    st.write("80/20 Employee Portfolio Analysis")
    st.dataframe(
        concentration_table(employees_filtered, "Employee", "Portfolio 2026", 0.8),
        use_container_width=True
    )

    if not clients.empty:
        st.write("Top Clients by Outstanding Amount")
        st.dataframe(
            clients.sort_values("Outstanding Amount", ascending=False).head(20),
            use_container_width=True
        )


# =========================
# Risk Indicators
# =========================

with tabs[6]:
    st.subheader("Risk Indicators")

    risk_cols = [
        "Loans Sent To Collection",
        "Provision",
        "Stage 3 Provision",
        "Refinance",
        "Shift",
        "BAR"
    ]

    for metric in risk_cols:
        st.write(f"Top Employees by {metric}")
        st.dataframe(
            employees_filtered[["Employee", "Branch", metric]]
            .sort_values(metric, ascending=False)
            .head(10),
            use_container_width=True
        )

    st.write("Employees Requiring Follow-up")

    follow_up = employees_filtered[
        (employees_filtered["Portfolio Growth %"] < 0) |
        (employees_filtered["Collection Achievement %"] < 0.9) |
        (employees_filtered["Loans Sent To Collection"] > 0)
    ].copy()

    st.dataframe(
        follow_up[[
            "Employee", "Branch", "Portfolio 2026", "Portfolio Growth %",
            "Collection Achievement %", "Loans Sent To Collection",
            "Provision", "BAR"
        ]].sort_values("Portfolio Growth %", ascending=True),
        use_container_width=True
    )


# =========================
# HR Productivity
# =========================

with tabs[7]:
    st.subheader("HR Productivity Analytics")

    employees_filtered["Portfolio per Customer"] = (
        employees_filtered["Portfolio 2026"] /
        employees_filtered["Customers"].replace(0, pd.NA)
    ).fillna(0)

    employees_filtered["Collection per Customer"] = (
        employees_filtered["Collection"] /
        employees_filtered["Customers"].replace(0, pd.NA)
    ).fillna(0)

    employees_filtered["Portfolio per Year of Service"] = (
        employees_filtered["Portfolio 2026"] /
        employees_filtered["Years of Service"].replace(0, pd.NA)
    ).fillna(0)

    col1, col2 = st.columns(2)

    with col1:
        fig = px.scatter(
            employees_filtered,
            x="Years of Service",
            y="Portfolio 2026",
            size="Customers",
            color="Portfolio Growth %",
            hover_name="Employee",
            title="Years of Service vs Portfolio"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.scatter(
            employees_filtered,
            x="Years of Service",
            y="Collection Achievement %",
            size="Portfolio 2026",
            color="Portfolio Growth %",
            hover_name="Employee",
            title="Years of Service vs Collection Achievement"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.write("Top Employees by Portfolio per Customer")
    st.dataframe(
        employees_filtered[[
            "Employee", "Branch", "Portfolio 2026", "Customers",
            "Portfolio per Customer"
        ]]
        .sort_values("Portfolio per Customer", ascending=False)
        .head(20),
        use_container_width=True
    )

    st.write("High Potential Employees")
    high_potential = employees_filtered[
        (employees_filtered["Portfolio Growth %"] >= employees_filtered["Portfolio Growth %"].quantile(0.75)) &
        (employees_filtered["Collection Achievement %"] >= employees_filtered["Collection Achievement %"].quantile(0.75))
    ]

    st.dataframe(
        high_potential[[
            "Employee", "Branch", "Portfolio 2026",
            "Portfolio Growth %", "Collection Achievement %",
            "Customers", "Years of Service"
        ]].sort_values("Portfolio Growth %", ascending=False),
        use_container_width=True
    )


# =========================
# Smart Insights
# =========================

with tabs[8]:
    st.subheader("Smart Insights")

    negative_growth_count = len(employees_filtered[employees_filtered["Portfolio Growth %"] < 0])
    below_target_count = len(employees_filtered[employees_filtered["Collection Achievement %"] < 0.9])

    top_growth = employees_filtered.sort_values("Portfolio Growth %", ascending=False).head(3)["Employee"].tolist()
    bottom_growth = employees_filtered.sort_values("Portfolio Growth %", ascending=True).head(3)["Employee"].tolist()

    top_collection = employees_filtered.sort_values("Collection Achievement %", ascending=False).head(3)["Employee"].tolist()
    weak_collection = employees_filtered.sort_values("Collection Achievement %", ascending=True).head(3)["Employee"].tolist()

    top_area = areas.sort_values("Portfolio 2026", ascending=False).head(1)["Area"].iloc[0]
    weakest_area_growth = areas.sort_values("Portfolio Growth %", ascending=True).head(1)["Area"].iloc[0]

    st.info(f"Total portfolio based on Areas sheet is {format_money(total_portfolio)}.")
    st.info(f"Overall portfolio growth is {format_pct(average_growth)}.")
    st.info(f"{negative_growth_count} employees have negative portfolio growth.")
    st.info(f"{below_target_count} employees are below 90% collection achievement.")
    st.info("Top growth employees: " + ", ".join(top_growth))
    st.info("Employees requiring growth support: " + ", ".join(bottom_growth))
    st.info("Best collection achievement employees: " + ", ".join(top_collection))
    st.info("Weakest collection achievement employees: " + ", ".join(weak_collection))
    st.info(f"The largest portfolio area is {top_area}.")
    st.info(f"The weakest area by growth is {weakest_area_growth}.")

    st.write("Management Interpretation")
    st.write("""
    This dashboard can be used to support staffing decisions, performance discussions,
    training needs analysis, incentive design, and portfolio risk monitoring.
    Employees with high portfolio concentration should be monitored to avoid operational
    dependency risk. Employees with negative growth or weak collection achievement should
    be reviewed through coaching, workload analysis, and branch-level support.
    """)


# =========================
# Data Preview
# =========================

with tabs[9]:
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
