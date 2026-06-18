import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="HR Workforce Analytics Dashboard", layout="wide")

st.title("HR Workforce Analytics Dashboard")
st.caption("Excel to HR, portfolio, collection, performance, risk, and management insights")

def num(df, col):
    if col in df.columns:
        return pd.to_numeric(df[col], errors="coerce").fillna(0)
    return pd.Series([0] * len(df), index=df.index)

def txt(df, col):
    if col in df.columns:
        return df[col].fillna("Unknown").astype(str)
    return pd.Series(["Unknown"] * len(df), index=df.index)

def prepare(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    for col in ["Employee", "Branch", "Area"]:
        df[col] = txt(df, col)

    for col in [
        "Portfolio", "Portfolio 2025", "Portfolio 2026",
        "Customers", "Collection", "Collection Target",
        "Loans", "Loan Sent To Collection", "Provision", "PAR", "BAR"
    ]:
        df[col] = num(df, col)

    if "Growth %" in df.columns:
        df["Growth %"] = num(df, "Growth %")
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

    if "Hire Date" in df.columns:
        df["Hire Date"] = pd.to_datetime(df["Hire Date"], errors="coerce")
        df["Years of Service"] = ((pd.Timestamp.today() - df["Hire Date"]).dt.days / 365.25).fillna(0)
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

def insights(employees, branches):
    result = []

    best = employees.sort_values("Growth %", ascending=False).head(3)["Employee"].tolist()
    result.append("Top employees to use as performance benchmarks: " + ", ".join(best))

    result.append(f"Number of employees with negative growth: {len(employees[employees['Growth %'] < 0])}")
    result.append(f"Number of employees below collection target: {len(employees[employees['Collection Achievement %'] < 90])}")
    result.append(f"{len(concentration(employees, 'Employee', 0.5))} employees carry around 50% of the total portfolio.")

    weak_branches = branches.sort_values("Growth %").head(3)["Branch"].tolist()
    result.append("Branches that need support or management intervention: " + ", ".join(weak_branches))

    high_potential = employees[
        (employees["Years of Service"] <= employees["Years of Service"].quantile(0.4)) &
        (employees["Growth %"] >= employees["Growth %"].quantile(0.75))
    ]
    result.append(f"Number of high-potential employees: {len(high_potential)}")

    return result

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])

if uploaded_file is None:
    st.info("Upload an Excel file with a sheet named: Employees")
    st.stop()

try:
    employees = prepare(pd.read_excel(uploaded_file, sheet_name="Employees"))
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
        fig = px.pie(
            areas,
            names="Area",
            values="Portfolio",
            title="Portfolio by Area"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        bar(
            areas.sort_values("Growth %", ascending=False),
            "Area",
            "Growth %",
            "Area Growth"
        )

with tabs[1]:
    st.subheader("Employee Performance")

    col1, col2 = st.columns(2)

    with col1:
        bar(
            top(employees, "Employee", "Growth %", 10),
            "Employee",
            "Growth %",
            "Top 10 Employees by Growth"
        )

    with col2:
        bar(
            top(employees, "Employee", "Growth %", 10, True),
            "Employee",
            "Growth %",
            "Bottom 10 Employees by Growth"
        )

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
        bar(
            top(branches, "Branch", "Growth %", 10),
            "Branch",
            "Growth %",
            "Top 10 Branches by Growth"
        )

    with col2:
        bar(
            top(branches, "Branch", "Growth %", 10, True),
            "Branch",
            "Growth %",
            "Bottom 10 Branches by Growth"
        )

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

    bar(
        areas.sort_values("Growth %", ascending=False),
        "Area",
        "Growth %",
        "Areas Ranked by Growth"
    )

    bar(
        areas.sort_values("Portfolio", ascending=False),
        "Area",
        "Portfolio",
        "Areas Ranked by Portfolio"
    )

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

    for item in insights(employees, branches):
        st.info(item)
