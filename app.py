import re
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="HR Workforce Analytics Dashboard", layout="wide")

st.title("HR Workforce Analytics Dashboard")
st.caption("Workforce, portfolio, collection, performance, risk, and management insights")

ALIASES = {
    "Employee": [
        "employee", "employee name", "name", "staff", "staff name",
        "officer", "loan officer", "user", "collector"
    ],
    "Branch": [
        "branch", "branch name", "office", "office name"
    ],
    "Area": [
        "area", "area name", "region", "zone", "district"
    ],
    "Portfolio": [
        "portfolio", "portfolio balance", "portfolio amount",
        "outstanding portfolio", "outstanding balance", "outstanding",
        "glp", "gross loan portfolio", "current portfolio",
        "portfolio 2026", "portfolio_2026"
    ],
    "Portfolio 2025": [
        "portfolio 2025", "portfolio_2025", "previous portfolio",
        "previous outstanding", "portfolio last year"
    ],
    "Portfolio 2026": [
        "portfolio 2026", "portfolio_2026", "current portfolio",
        "current outstanding", "portfolio"
    ],
    "Customers": [
        "customers", "customer", "clients", "client", "active clients",
        "customer count", "number of customers", "no of customers",
        "number of clients", "no of clients"
    ],
    "Collection": [
        "collection", "collected", "actual collection",
        "total collection", "collection amount"
    ],
    "Collection Target": [
        "collection target", "target collection", "expected collection",
        "collection forecast", "forecast collection", "target"
    ],
    "Loans": [
        "loans", "loan", "loan count", "total loans", "number of loans"
    ],
    "Hire Date": [
        "hire date", "joining date", "start date", "employment date"
    ],
    "Loan Sent To Collection": [
        "loan sent to collection", "sent to collection",
        "collection loans", "loans sent to collection"
    ],
    "Provision": [
        "provision", "provisions"
    ],
    "PAR": [
        "par", "portfolio at risk"
    ],
    "BAR": [
        "bar", "balance at risk"
    ],
    "Growth %": [
        "growth", "growth %", "growth rate", "portfolio growth"
    ],
}

def clean_name(value):
    value = str(value).lower().strip()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def find_column(df, key):
    cleaned_columns = {clean_name(col): col for col in df.columns}

    for alias in ALIASES.get(key, [key]):
        alias_clean = clean_name(alias)
        if alias_clean in cleaned_columns:
            return cleaned_columns[alias_clean]

    for alias in ALIASES.get(key, [key]):
        alias_clean = clean_name(alias)
        for cleaned_col, original_col in cleaned_columns.items():
            if alias_clean in cleaned_col or cleaned_col in alias_clean:
                return original_col

    return None

def fallback_text_column(df):
    for col in df.columns:
        if df[col].dtype == "object":
            return col
    return None

def number_series(df, key):
    col = find_column(df, key)
    if col:
        return pd.to_numeric(
            df[col].astype(str).str.replace(",", "", regex=False).str.replace("%", "", regex=False),
            errors="coerce"
        ).fillna(0)
    return pd.Series([0] * len(df), index=df.index)

def text_series(df, key):
    col = find_column(df, key)

    if not col and key == "Employee":
        col = fallback_text_column(df)

    if col:
        return df[col].fillna("Unknown").astype(str)

    return pd.Series(["Unknown"] * len(df), index=df.index)

def prepare(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    df["Employee"] = text_series(df, "Employee")
    df["Branch"] = text_series(df, "Branch")
    df["Area"] = text_series(df, "Area")

    for col in [
        "Portfolio", "Portfolio 2025", "Portfolio 2026",
        "Customers", "Collection", "Collection Target",
        "Loans", "Loan Sent To Collection", "Provision", "PAR", "BAR"
    ]:
        df[col] = number_series(df, col)

    growth_col = find_column(df, "Growth %")
    if growth_col:
        df["Growth %"] = pd.to_numeric(
            df[growth_col].astype(str).str.replace("%", "", regex=False),
            errors="coerce"
        ).fillna(0)
    elif df["Portfolio 2025"].sum() > 0:
        df["Growth %"] = (
            (df["Portfolio 2026"] - df["Portfolio 2025"])
            / df["Portfolio 2025"].replace(0, pd.NA)
            * 100
        ).fillna(0)
    else:
        df["Growth %"] = 0

    df["Collection Achievement %"] = (
        df["Collection"] / df["Collection Target"].replace(0, pd.NA) * 100
    ).fillna(0)

    hire_col = find_column(df, "Hire Date")
    if hire_col:
        df["Hire Date"] = pd.to_datetime(df[hire_col], errors="coerce")
        df["Years of Service"] = (
            (pd.Timestamp.today() - df["Hire Date"]).dt.days / 365.25
        ).fillna(0)
    else:
        df["Years of Service"] = 0

    df["Portfolio per Year of Service"] = (
        df["Portfolio"] / df["Years of Service"].replace(0, pd.NA)
    ).fillna(0)

    return df

def aggregate(df, group_col):
    return df.groupby(group_col, as_index=False).agg({
        "Portfolio": "sum",
        "Customers": "sum",
        "Collection": "sum",
        "Collection Target": "sum",
        "Loans": "sum",
        "Loan Sent To Collection": "sum",
        "Provision": "sum",
        "PAR": "mean",
        "BAR": "mean",
        "Growth %": "mean",
        "Collection Achievement %": "mean"
    })

def top(df, name, metric, n=10, asc=False):
    return df[[name, metric]].sort_values(metric, ascending=asc).head(n)

def bar(df, x, y, title):
    if df.empty or df[y].sum() == 0:
        st.info(f"No values available for: {title}")
        return

    fig = px.bar(df, x=x, y=y, text_auto=True, title=title)
    fig.update_layout(height=420)
    st.plotly_chart(fig, use_container_width=True)

def concentration(df, name, threshold):
    temp = df[[name, "Portfolio"]].sort_values("Portfolio", ascending=False).copy()
    total = temp["Portfolio"].sum()

    if total == 0:
        return temp.head(0)

    temp["Share %"] = temp["Portfolio"] / total * 100
    temp["Cumulative Share %"] = temp["Share %"].cumsum()
    count = (temp["Cumulative Share %"] < threshold * 100).sum() + 1

    return temp.head(count)

def smart_insights(employees, branches):
    result = []

    best = employees.sort_values("Growth %", ascending=False).head(3)["Employee"].tolist()
    result.append("Top employees to use as performance benchmarks: " + ", ".join(best))

    result.append(f"Employees with negative growth: {len(employees[employees['Growth %'] < 0])}")
    result.append(f"Employees below collection target: {len(employees[employees['Collection Achievement %'] < 90])}")
    result.append(f"{len(concentration(employees, 'Employee', 0.5))} employees carry around 50% of the portfolio.")

    weak_branches = branches.sort_values("Growth %").head(3)["Branch"].tolist()
    result.append("Branches needing support or management intervention: " + ", ".join(weak_branches))

    high_potential = employees[
        (employees["Years of Service"] <= employees["Years of Service"].quantile(0.4)) &
        (employees["Growth %"] >= employees["Growth %"].quantile(0.75))
    ]
    result.append(f"High-potential employees: {len(high_potential)}")

    return result

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])

if uploaded_file is None:
    st.info("Upload an Excel file. The main sheet should be named Employees.")
    st.stop()

try:
    excel = pd.ExcelFile(uploaded_file)
    employees = prepare(pd.read_excel(excel, sheet_name="Employees"))
except Exception as e:
    st.error(f"Error reading Excel file: {e}")
    st.stop()

st.sidebar.header("Filters")

selected_areas = st.sidebar.multiselect(
    "Area",
    sorted(employees["Area"].unique()),
    default=sorted(employees["Area"].unique())
)
employees = employees[employees["Area"].isin(selected_areas)]

selected_branches = st.sidebar.multiselect(
    "Branch",
    sorted(employees["Branch"].unique()),
    default=sorted(employees["Branch"].unique())
)
employees = employees[employees["Branch"].isin(selected_branches)]

selected_employees = st.sidebar.multiselect(
    "Employee",
    sorted(employees["Employee"].unique()),
    default=sorted(employees["Employee"].unique())
)
employees = employees[employees["Employee"].isin(selected_employees)]

branches = aggregate(employees, "Branch")
areas = aggregate(employees, "Area")

with st.expander("Detected Data Preview"):
    st.write("If values are zero, your Excel column names may be different. This preview helps verify what was read.")
    st.dataframe(employees.head(20), use_container_width=True)

tabs = st.tabs([
    "Executive Dashboard",
    "Employee Performance",
    "Branch Performance",
    "Area Performance",
    "Concentration Risk",
    "Experience Analytics",
    "Risk Indicators",
    "Smart Insights"
])

with tabs[0]:
    st.subheader("Executive Dashboard")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Portfolio", f"{employees['Portfolio'].sum():,.0f}")
    c2.metric("Total Customers", f"{employees['Customers'].sum():,.0f}")
    c3.metric("Total Collection", f"{employees['Collection'].sum():,.0f}")
    c4.metric("Average Growth", f"{employees['Growth %'].mean():.2f}%")
    c5.metric("Total Loans", f"{employees['Loans'].sum():,.0f}")

    col1, col2 = st.columns(2)

    with col1:
        if areas["Portfolio"].sum() > 0:
            fig = px.pie(areas, names="Area", values="Portfolio", title="Portfolio by Area")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No portfolio values found.")

    with col2:
        bar(areas.sort_values("Growth %", ascending=False), "Area", "Growth %", "Area Growth")

with tabs[1]:
    st.subheader("Employee Performance")

    col1, col2 = st.columns(2)

    with col1:
        bar(top(employees, "Employee", "Growth %", 10), "Employee", "Growth %", "Top 10 Employees by Growth")

    with col2:
        bar(top(employees, "Employee", "Growth %", 10, True), "Employee", "Growth %", "Bottom 10 Employees by Growth")

    st.write("Top 20 Employees by Portfolio Size")
    st.dataframe(top(employees, "Employee", "Portfolio", 20), use_container_width=True)

    st.write("Top Employees by Number of Customers")
    st.dataframe(top(employees, "Employee", "Customers", 20), use_container_width=True)

    st.write("Best Employees by Collection Target Achievement")
    st.dataframe(top(employees, "Employee", "Collection Achievement %", 10), use_container_width=True)

    st.write("Worst Employees by Collection Target Achievement")
    st.dataframe(top(employees, "Employee", "Collection Achievement %", 10, True), use_container_width=True)

with tabs[2]:
    st.subheader("Branch Performance")

    col1, col2 = st.columns(2)

    with col1:
        bar(top(branches, "Branch", "Growth %", 10), "Branch", "Growth %", "Top 10 Branches by Growth")

    with col2:
        bar(top(branches, "Branch", "Growth %", 10, True), "Branch", "Growth %", "Bottom 10 Branches by Growth")

    st.write("Top Branches by Portfolio Size")
    st.dataframe(top(branches, "Branch", "Portfolio", 20), use_container_width=True)

    st.write("Top Branches by Number of Customers")
    st.dataframe(top(branches, "Branch", "Customers", 20), use_container_width=True)

    st.write("Best Branches by Collection Target Achievement")
    st.dataframe(top(branches, "Branch", "Collection Achievement %", 10), use_container_width=True)

    st.write("Worst Branches by Collection Target Achievement")
    st.dataframe(top(branches, "Branch", "Collection Achievement %", 10, True), use_container_width=True)

with tabs[3]:
    st.subheader("Area Performance")

    bar(areas.sort_values("Growth %", ascending=False), "Area", "Growth %", "Areas Ranked by Growth")
    bar(areas.sort_values("Portfolio", ascending=False), "Area", "Portfolio", "Areas Ranked by Portfolio")

    st.write("Best Areas by Collection Target Achievement")
    st.dataframe(top(areas, "Area", "Collection Achievement %", 10), use_container_width=True)

    st.write("Worst Areas by Collection Target Achievement")
    st.dataframe(top(areas, "Area", "Collection Achievement %", 10, True), use_container_width=True)

with tabs[4]:
    st.subheader("Concentration Risk")

    st.write("Employees Carrying 50% of Total Portfolio")
    st.dataframe(concentration(employees, "Employee", 0.5), use_container_width=True)

    st.write("Branches Carrying 50% of Total Portfolio")
    st.dataframe(concentration(branches, "Branch", 0.5), use_container_width=True)

    st.write("Areas Carrying 50% of Total Portfolio")
    st.dataframe(concentration(areas, "Area", 0.5), use_container_width=True)

    st.write("Pareto / 80-20 Analysis")
    st.dataframe(concentration(employees, "Employee", 0.8), use_container_width=True)

with tabs[5]:
    st.subheader("Experience Analytics")

    col1, col2 = st.columns(2)

    with col1:
        fig = px.scatter(
            employees,
            x="Years of Service",
            y="Portfolio",
            color="Growth %",
            hover_name="Employee",
            title="Years of Service vs Portfolio"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.scatter(
            employees,
            x="Years of Service",
            y="Growth %",
            size="Portfolio",
            hover_name="Employee",
            title="Years of Service vs Growth"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.write("Portfolio per Year of Service")
    st.dataframe(
        employees[
            [
                "Employee",
                "Branch",
                "Area",
                "Years of Service",
                "Portfolio",
                "Growth %",
                "Portfolio per Year of Service"
            ]
        ]
        .sort_values("Portfolio per Year of Service", ascending=False)
        .head(20),
        use_container_width=True
    )

    st.write("High Potential Employees")
    high_potential = employees[
        (employees["Years of Service"] <= employees["Years of Service"].quantile(0.4)) &
        (employees["Growth %"] >= employees["Growth %"].quantile(0.75))
    ]
    st.dataframe(high_potential, use_container_width=True)

with tabs[6]:
    st.subheader("Risk Indicators")

    for metric in ["Loan Sent To Collection", "Provision", "PAR", "BAR"]:
        st.write(f"Top Employees by {metric}")
        st.dataframe(top(employees, "Employee", metric, 10), use_container_width=True)

    st.write("Employees Requiring Follow-up")

    follow_up = employees[
        (employees["Growth %"] < 0) |
        (employees["Collection Achievement %"] < 90) |
        (
            (employees["Portfolio"] >= employees["Portfolio"].quantile(0.75)) &
            (employees["Loan Sent To Collection"] >= employees["Loan Sent To Collection"].quantile(0.75))
        )
    ]

    st.dataframe(follow_up, use_container_width=True)

with tabs[7]:
    st.subheader("Smart Insights")

    for item in smart_insights(employees, branches):
        st.info(item)
