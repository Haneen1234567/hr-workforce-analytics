import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="HR Workforce Analytics Dashboard",
    layout="wide"
)

st.title("HR Workforce Analytics Dashboard")
st.caption("Automated workforce, portfolio, collection, risk, and HR analytics platform")

uploaded_file = st.file_uploader(
    "Upload quarterly Excel file",
    type=["xlsx", "xls"]
)

def normalize_columns(df):
    df = df.copy()
    df.columns = df.columns.str.strip()
    return df

def find_col(df, options):
    cols = {c.lower().strip(): c for c in df.columns}
    for opt in options:
        if opt.lower() in cols:
            return cols[opt.lower()]
    return None

def add_growth(df):
    current = find_col(df, ["Portfolio 2026", "Current Portfolio", "Portfolio"])
    previous = find_col(df, ["Portfolio 2025", "Previous Portfolio"])

    if current and previous:
        df["Growth %"] = ((df[current] - df[previous]) / df[previous].replace(0, pd.NA)) * 100
    elif "Growth %" not in df.columns:
        df["Growth %"] = 0

    df["Growth %"] = pd.to_numeric(df["Growth %"], errors="coerce").fillna(0)
    return df

def prepare_df(df):
    df = normalize_columns(df)
    df = add_growth(df)

    numeric_cols = [
        "Portfolio", "Portfolio 2025", "Portfolio 2026",
        "Customers", "Clients", "Collection", "Collection Target",
        "Loans", "Loan Sent To Collection", "Provision",
        "PAR", "BAR", "Growth %"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df

def metric_value(df, options):
    col = find_col(df, options)
    if col:
        return df[col].sum()
    return 0

def top_table(df, name_col, value_col, n=10, ascending=False):
    if name_col not in df.columns or value_col not in df.columns:
        return pd.DataFrame()
    return df[[name_col, value_col]].sort_values(value_col, ascending=ascending).head(n)

def bar(df, x, y, title):
    if df.empty:
        st.info("No data available")
        return
    fig = px.bar(df, x=x, y=y, title=title, text_auto=True)
    fig.update_layout(height=420)
    st.plotly_chart(fig, use_container_width=True)

def collection_achievement(df):
    collection = find_col(df, ["Collection", "Actual Collection"])
    target = find_col(df, ["Collection Target", "Expected Collection", "Collection Forecast"])

    if collection and target:
        df["Collection Achievement %"] = (
            df[collection] / df[target].replace(0, pd.NA)
        ) * 100
        df["Collection Achievement %"] = df["Collection Achievement %"].fillna(0)
    else:
        df["Collection Achievement %"] = 0

    return df

def concentration(df, name_col, portfolio_col, threshold=0.5):
    if name_col not in df.columns or portfolio_col not in df.columns:
        return pd.DataFrame()

    temp = df[[name_col, portfolio_col]].copy()
    temp = temp.sort_values(portfolio_col, ascending=False)
    total = temp[portfolio_col].sum()

    if total == 0:
        return pd.DataFrame()

    temp["Share %"] = temp[portfolio_col] / total * 100
    temp["Cumulative Share %"] = temp["Share %"].cumsum()

    count = (temp["Cumulative Share %"] < threshold * 100).sum() + 1
    return temp.head(count)

def smart_insights(employees, branches, areas):
    insights = []

    if "Employee" in employees.columns and "Growth %" in employees.columns:
        top_emp = employees.sort_values("Growth %", ascending=False).head(3)["Employee"].tolist()
        insights.append(f"أفضل الموظفين أداءً ويمكن استخدامهم كـ benchmarks: {', '.join(map(str, top_emp))}")

    if "Growth %" in employees.columns:
        negative = employees[employees["Growth %"] < 0]
        insights.append(f"عدد الموظفين ذوي النمو السلبي: {len(negative)}")

    if "Collection Achievement %" in employees.columns:
        weak_collection = employees[employees["Collection Achievement %"] < 90]
        insights.append(f"عدد الموظفين بتحصيل أقل من 90% من الهدف: {len(weak_collection)}")

    if "Portfolio" in employees.columns:
        high_portfolio = concentration(employees, "Employee", "Portfolio", 0.5)
        insights.append(f"{len(high_portfolio)} موظفين يحملون تقريبًا 50% من إجمالي المحفظة.")

    if "Branch" in branches.columns and "Growth %" in branches.columns:
        weak_branches = branches.sort_values("Growth %").head(3)["Branch"].tolist()
        insights.append(f"فروع تحتاج متابعة أو دعم: {', '.join(map(str, weak_branches))}")

    if "Area" in areas.columns and "Growth %" in areas.columns:
        best_area = areas.sort_values("Growth %", ascending=False).head(1)["Area"].tolist()
        if best_area:
            insights.append(f"أفضل منطقة نموًا: {best_area[0]}")

    return insights

if uploaded_file:
    try:
        employees = pd.read_excel(uploaded_file, sheet_name="Employees")
        branches = pd.read_excel(uploaded_file, sheet_name="Branches")
        areas = pd.read_excel(uploaded_file, sheet_name="Areas")

        employees = collection_achievement(prepare_df(employees))
        branches = collection_achievement(prepare_df(branches))
        areas = collection_achievement(prepare_df(areas))

        st.sidebar.header("Filters")

        if "Area" in employees.columns:
            selected_area = st.sidebar.multiselect(
                "Area",
                sorted(employees["Area"].dropna().unique()),
                default=sorted(employees["Area"].dropna().unique())
            )
            employees = employees[employees["Area"].isin(selected_area)]

        if "Branch" in employees.columns:
            selected_branch = st.sidebar.multiselect(
                "Branch",
                sorted(employees["Branch"].dropna().unique()),
                default=sorted(employees["Branch"].dropna().unique())
            )
            employees = employees[employees["Branch"].isin(selected_branch)]

        if "Employee" in employees.columns:
            selected_employee = st.sidebar.multiselect(
                "Employee",
                sorted(employees["Employee"].dropna().unique()),
                default=sorted(employees["Employee"].dropna().unique())
            )
            employees = employees[employees["Employee"].isin(selected_employee)]

        tabs = st.tabs([
            "Executive Dashboard",
            "Employees Performance",
            "Branch Performance",
            "Area Performance",
            "Concentration Risk",
            "Experience Analytics",
            "Risk Indicators",
            "Smart Insights"
        ])

        with tabs[0]:
            st.subheader("Executive Dashboard")

            total_portfolio = metric_value(employees, ["Portfolio", "Portfolio 2026"])
            total_customers = metric_value(employees, ["Customers", "Clients"])
            total_collection = metric_value(employees, ["Collection"])
            total_loans = metric_value(employees, ["Loans"])
            avg_growth = employees["Growth %"].mean() if "Growth %" in employees.columns else 0

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("إجمالي المحفظة", f"{total_portfolio:,.0f}")
            c2.metric("إجمالي العملاء", f"{total_customers:,.0f}")
            c3.metric("إجمالي التحصيل", f"{total_collection:,.0f}")
            c4.metric("متوسط النمو", f"{avg_growth:.2f}%")
            c5.metric("إجمالي القروض", f"{total_loans:,.0f}")

            if "Area" in areas.columns and "Portfolio" in areas.columns:
                fig = px.pie(areas, names="Area", values="Portfolio", title="المحفظة حسب المنطقة")
                st.plotly_chart(fig, use_container_width=True)

            if "Area" in areas.columns and "Growth %" in areas.columns:
                bar(areas.sort_values("Growth %", ascending=False), "Area", "Growth %", "نمو المناطق")

        with tabs[1]:
            st.subheader("Employees Performance")

            if "Employee" in employees.columns:
                c1, c2 = st.columns(2)
                with c1:
                    bar(top_table(employees, "Employee", "Growth %", 10), "Employee", "Growth %", "أفضل 10 موظفين بالنمو")
                with c2:
                    bar(top_table(employees, "Employee", "Growth %", 10, True), "Employee", "Growth %", "أسوأ 10 موظفين بالنمو")

                if "Portfolio" in employees.columns:
                    st.write("أكبر 20 موظف حسب حجم المحفظة")
                    st.dataframe(top_table(employees, "Employee", "Portfolio", 20), use_container_width=True)

                customer_col = find_col(employees, ["Customers", "Clients"])
                if customer_col:
                    st.write("أكثر موظفين عندهم عدد زبائن")
                    st.dataframe(top_table(employees, "Employee", customer_col, 20), use_container_width=True)

                st.write("أفضل وأسوأ موظفين بتحقيق توقعات التحصيل")
                st.dataframe(top_table(employees, "Employee", "Collection Achievement %", 10), use_container_width=True)
                st.dataframe(top_table(employees, "Employee", "Collection Achievement %", 10, True), use_container_width=True)

        with tabs[2]:
            st.subheader("Branch Performance")

            if "Branch" in branches.columns:
                c1, c2 = st.columns(2)
                with c1:
                    bar(top_table(branches, "Branch", "Growth %", 10), "Branch", "Growth %", "أفضل 10 فروع بالنمو")
                with c2:
                    bar(top_table(branches, "Branch", "Growth %", 10, True), "Branch", "Growth %", "أسوأ 10 فروع بالنمو")

                if "Portfolio" in branches.columns:
                    st.write("أكبر الفروع حسب المحفظة")
                    st.dataframe(top_table(branches, "Branch", "Portfolio", 20), use_container_width=True)

                customer_col = find_col(branches, ["Customers", "Clients"])
                if customer_col:
                    st.write("أكثر الفروع بعدد العملاء")
                    st.dataframe(top_table(branches, "Branch", customer_col, 20), use_container_width=True)

                st.write("أفضل وأسوأ فروع بتحقيق توقعات التحصيل")
                st.dataframe(top_table(branches, "Branch", "Collection Achievement %", 10), use_container_width=True)
                st.dataframe(top_table(branches, "Branch", "Collection Achievement %", 10, True), use_container_width=True)

        with tabs[3]:
            st.subheader("Area Performance")

            if "Area" in areas.columns:
                bar(areas.sort_values("Growth %", ascending=False), "Area", "Growth %", "ترتيب المناطق حسب النمو")

                if "Portfolio" in areas.columns:
                    bar(areas.sort_values("Portfolio", ascending=False), "Area", "Portfolio", "ترتيب المناطق حسب المحفظة")

                st.write("أفضل وأسوأ مناطق بتحقيق توقعات التحصيل")
                st.dataframe(top_table(areas, "Area", "Collection Achievement %", 10), use_container_width=True)
                st.dataframe(top_table(areas, "Area", "Collection Achievement %", 10, True), use_container_width=True)

        with tabs[4]:
            st.subheader("Concentration Risk")

            if "Portfolio" in employees.columns:
                st.write("الموظفون الذين يحملون 50% من إجمالي المحفظة")
                st.dataframe(concentration(employees, "Employee", "Portfolio", 0.5), use_container_width=True)

            if "Portfolio" in branches.columns:
                st.write("الفروع التي تحمل 50% من المحفظة")
                st.dataframe(concentration(branches, "Branch", "Portfolio", 0.5), use_container_width=True)

            if "Portfolio" in areas.columns:
                st.write("المناطق التي تحمل 50% من المحفظة")
                st.dataframe(concentration(areas, "Area", "Portfolio", 0.5), use_container_width=True)

            st.write("Pareto / 80-20 Analysis")
            if "Portfolio" in employees.columns:
                st.dataframe(concentration(employees, "Employee", "Portfolio", 0.8), use_container_width=True)

        with tabs[5]:
            st.subheader("Experience Analytics")

            if "Hire Date" in employees.columns:
                employees["Hire Date"] = pd.to_datetime(employees["Hire Date"], errors="coerce")
                employees["Years of Service"] = (
                    datetime.today() - employees["Hire Date"]
                ).dt.days / 365.25

                employees["Years of Service"] = employees["Years of Service"].fillna(0)

                if "Portfolio" in employees.columns:
                    employees["Portfolio per Year of Service"] = (
                        employees["Portfolio"] / employees["Years of Service"].replace(0, pd.NA)
                    ).fillna(0)

                    fig = px.scatter(
                        employees,
                        x="Years of Service",
                        y="Portfolio",
                        color="Growth %",
                        hover_name="Employee",
                        title="ربط سنوات الخدمة بحجم المحفظة"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    st.write("Portfolio per Year of Service")
                    st.dataframe(
                        employees[["Employee", "Years of Service", "Portfolio", "Growth %", "Portfolio per Year of Service"]]
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
            else:
                st.info("أضف عمود Hire Date لتفعيل تحليل سنوات الخدمة.")

        with tabs[6]:
            st.subheader("Risk Indicators")

            risk_cols = ["Loan Sent To Collection", "Provision", "PAR", "BAR"]

            for col in risk_cols:
                if col in employees.columns:
                    st.write(f"أعلى موظفين في {col}")
                    st.dataframe(top_table(employees, "Employee", col, 10), use_container_width=True)

            st.write("قائمة الموظفين الذين يحتاجون متابعة")

            follow_up = employees.copy()
            conditions = []

            if "Growth %" in follow_up.columns:
                conditions.append(follow_up["Growth %"] < 0)

            if "Collection Achievement %" in follow_up.columns:
                conditions.append(follow_up["Collection Achievement %"] < 90)

            if "Portfolio" in follow_up.columns and "Loan Sent To Collection" in follow_up.columns:
                conditions.append(
                    (follow_up["Portfolio"] >= follow_up["Portfolio"].quantile(0.75)) &
                    (follow_up["Loan Sent To Collection"] >= follow_up["Loan Sent To Collection"].quantile(0.75))
                )

            if conditions:
                final_condition = conditions[0]
                for condition in conditions[1:]:
                    final_condition = final_condition | condition

                st.dataframe(follow_up[final_condition], use_container_width=True)
            else:
                st.info("No risk indicators available.")

        with tabs[7]:
            st.subheader("AI / Smart Insights")

            insights = smart_insights(employees, branches, areas)

            for item in insights:
                st.info(item)

    except Exception as e:
        st.error(f"Error reading file: {e}")

else:
    st.info("Upload an Excel file with sheets: Employees, Branches, Areas")
