import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="HR Workforce Analytics Dashboard",
    layout="wide"
)

st.title("HR Workforce Analytics Dashboard")
st.caption("Automated workforce, portfolio, productivity and risk analytics platform")

uploaded_file = st.file_uploader("Upload Data Summary Excel File", type=["xlsx"])

def load_sheet(file, sheet_name):
    try:
        return pd.read_excel(file, sheet_name=sheet_name)
    except Exception:
        return pd.DataFrame()

def clean_name(df, column="Name"):
    if column in df.columns:
        df[column] = df[column].astype(str).str.strip()
    return df

if uploaded_file:
    # Load sheets
    par_area = clean_name(load_sheet(uploaded_file, "Par By Area "))
    par_branch = clean_name(load_sheet(uploaded_file, "Par by Branch "))
    par_officer = clean_name(load_sheet(uploaded_file, "Par 30 By Credit Officer "))

    loan_area = clean_name(load_sheet(uploaded_file, "Loan Issued By Area "))
    loan_branch = clean_name(load_sheet(uploaded_file, "Loan Issued By Branch"))
    loan_officer = clean_name(load_sheet(uploaded_file, "Loan Issued By Credit Officer "))

    portfolio_area = clean_name(load_sheet(uploaded_file, "Outstanding Portfolio By Area"))
    portfolio_branch = clean_name(load_sheet(uploaded_file, "Outstanding Portfolio By Branch"))
    portfolio_officer = clean_name(load_sheet(uploaded_file, "Outstanding Portfolio By Credit"))

    collection_area = clean_name(load_sheet(uploaded_file, "Collection During Period by AR "))
    collection_branch = clean_name(load_sheet(uploaded_file, "Collection During Period by br "))
    collection_officer = clean_name(load_sheet(uploaded_file, "Collection during period by C"))

    st.success("File uploaded and processed successfully.")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Executive Dashboard",
        "Area Analytics",
        "Branch Analytics",
        "Credit Officer Analytics",
        "Risk & AI Insights"
    ])

    with tab1:
        st.header("Executive Dashboard")

        total_portfolio = 0
        total_loans = 0
        avg_growth = 0
        avg_par30 = 0

        if not portfolio_area.empty and "Outstanding Amount 31/12/2025" in portfolio_area.columns:
            total_portfolio = portfolio_area["Outstanding Amount 31/12/2025"].sum()

        if not portfolio_area.empty and "Loans 31/12/2025" in portfolio_area.columns:
            total_loans = portfolio_area["Loans 31/12/2025"].sum()

        if not portfolio_area.empty and "Amount Growth  %" in portfolio_area.columns:
            avg_growth = portfolio_area["Amount Growth  %"].mean() * 100

        if not par_area.empty and "Portfolio at Risk 30 DAY %" in par_area.columns:
            avg_par30 = par_area["Portfolio at Risk 30 DAY %"].mean() * 100

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Portfolio", f"${total_portfolio:,.0f}")
        c2.metric("Total Loans", f"{total_loans:,.0f}")
        c3.metric("Average Growth", f"{avg_growth:.2f}%")
        c4.metric("Average PAR30", f"{avg_par30:.2f}%")

        st.subheader("Portfolio Growth by Area")
        if not portfolio_area.empty and "Name" in portfolio_area.columns and "Amount Growth  %" in portfolio_area.columns:
            area_growth = portfolio_area[["Name", "Amount Growth  %"]].copy()
            area_growth["Amount Growth  %"] = area_growth["Amount Growth  %"] * 100
            st.bar_chart(area_growth.set_index("Name"))

        st.subheader("Top 10 Credit Officers by Portfolio")
        if not portfolio_officer.empty and "Name" in portfolio_officer.columns and "Outstanding Amount 31/12/2025" in portfolio_officer.columns:
            top_officers = portfolio_officer.sort_values(
                "Outstanding Amount 31/12/2025",
                ascending=False
            ).head(10)
            st.dataframe(top_officers[["Name", "Outstanding Amount 31/12/2025", "Amount Growth  %"]])
            st.bar_chart(top_officers.set_index("Name")["Outstanding Amount 31/12/2025"])

    with tab2:
        st.header("Area Analytics")

        st.subheader("Outstanding Portfolio by Area")
        if not portfolio_area.empty:
            st.dataframe(portfolio_area)

        st.subheader("Collection by Area")
        if not collection_area.empty and "Name" in collection_area.columns and "Total_Amount_FCY" in collection_area.columns:
            st.bar_chart(collection_area.set_index("Name")["Total_Amount_FCY"])
            st.dataframe(collection_area)

        st.subheader("PAR30 by Area")
        if not par_area.empty and "Name" in par_area.columns and "Portfolio at Risk 30 DAY %" in par_area.columns:
            par_area_chart = par_area[["Name", "Portfolio at Risk 30 DAY %"]].copy()
            par_area_chart["Portfolio at Risk 30 DAY %"] = par_area_chart["Portfolio at Risk 30 DAY %"] * 100
            st.bar_chart(par_area_chart.set_index("Name"))
            st.dataframe(par_area)

    with tab3:
        st.header("Branch Analytics")

        st.subheader("Branch Portfolio Ranking")
        if not portfolio_branch.empty and "Name" in portfolio_branch.columns and "Outstanding Amount 31/12/2025" in portfolio_branch.columns:
            branch_rank = portfolio_branch.sort_values(
                "Outstanding Amount 31/12/2025",
                ascending=False
            )
            st.dataframe(branch_rank)
            st.bar_chart(branch_rank.set_index("Name")["Outstanding Amount 31/12/2025"])

        st.subheader("Branch Growth")
        if not portfolio_branch.empty and "Amount Growth  %" in portfolio_branch.columns:
            branch_growth = portfolio_branch[["Name", "Amount Growth  %"]].copy()
            branch_growth["Amount Growth  %"] = branch_growth["Amount Growth  %"] * 100
            st.bar_chart(branch_growth.set_index("Name"))

        st.subheader("PAR30 by Branch")
        if not par_branch.empty and "Name" in par_branch.columns and "Portfolio at Risk 30 day  %" in par_branch.columns:
            par_branch_chart = par_branch[["Name", "Portfolio at Risk 30 day  %"]].copy()
            par_branch_chart["Portfolio at Risk 30 day  %"] = par_branch_chart["Portfolio at Risk 30 day  %"] * 100
            st.bar_chart(par_branch_chart.set_index("Name"))

    with tab4:
        st.header("Credit Officer Analytics")

        st.subheader("Top Credit Officers by Portfolio")
        if not portfolio_officer.empty and "Name" in portfolio_officer.columns and "Outstanding Amount 31/12/2025" in portfolio_officer.columns:
            officer_rank = portfolio_officer.sort_values(
                "Outstanding Amount 31/12/2025",
                ascending=False
            )
            st.dataframe(officer_rank)
            st.bar_chart(officer_rank.head(20).set_index("Name")["Outstanding Amount 31/12/2025"])

        st.subheader("Top Credit Officers by Growth")
        if not portfolio_officer.empty and "Amount Growth  %" in portfolio_officer.columns:
            growth_rank = portfolio_officer.sort_values(
                "Amount Growth  %",
                ascending=False
            ).head(10)
            growth_rank["Amount Growth  %"] = growth_rank["Amount Growth  %"] * 100
            st.dataframe(growth_rank)
            st.bar_chart(growth_rank.set_index("Name")["Amount Growth  %"])

        st.subheader("Collections by Credit Officer")
        if not collection_officer.empty and "Name" in collection_officer.columns and "Total_Amount_FCY" in collection_officer.columns:
            coll_rank = collection_officer.sort_values("Total_Amount_FCY", ascending=False).head(20)
            st.dataframe(coll_rank)
            st.bar_chart(coll_rank.set_index("Name")["Total_Amount_FCY"])

    with tab5:
        st.header("Risk & AI Insights")

        st.subheader("Growth vs PAR30 Risk Matrix")
        if (
            not portfolio_officer.empty
            and not par_officer.empty
            and "Id" in portfolio_officer.columns
            and "Id" in par_officer.columns
        ):
            merged = pd.merge(
                portfolio_officer,
                par_officer[["Id", "Portfolio at Risk 30 day %"]],
                on="Id",
                how="left"
            )

            if "Amount Growth  %" in merged.columns and "Portfolio at Risk 30 day %" in merged.columns:
                merged["Growth %"] = merged["Amount Growth  %"] * 100
                merged["PAR30 %"] = merged["Portfolio at Risk 30 day %"] * 100

                def classify(row):
                    if row["Growth %"] >= 3 and row["PAR30 %"] <= 3:
                        return "Top Performer"
                    elif row["Growth %"] < 3 and row["PAR30 %"] <= 3:
                        return "Stable"
                    elif row["Growth %"] >= 3 and row["PAR30 %"] > 3:
                        return "Risky Growth"
                    else:
                        return "Critical"

                merged["AI Classification"] = merged.apply(classify, axis=1)

                st.dataframe(merged[["Name", "Growth %", "PAR30 %", "AI Classification"]])

                st.scatter_chart(
                    merged,
                    x="Growth %",
                    y="PAR30 %",
                    size="Outstanding Amount 31/12/2025",
                    color="AI Classification"
                )

                st.subheader("AI-Generated Management Recommendations")

                top_count = len(merged[merged["AI Classification"] == "Top Performer"])
                critical_count = len(merged[merged["AI Classification"] == "Critical"])
                risky_count = len(merged[merged["AI Classification"] == "Risky Growth"])

                st.info(f"{top_count} credit officers are classified as Top Performers and can be used as internal benchmarks.")
                st.warning(f"{risky_count} credit officers show growth with elevated PAR30 risk and require risk monitoring.")
                st.error(f"{critical_count} credit officers are classified as Critical and may require performance intervention, coaching or portfolio review.")

                st.markdown("""
                **Suggested HR Actions**
                - Link high performance with recognition and incentive schemes.
                - Target critical cases with coaching and branch-level interventions.
                - Use the results to support workforce planning and branch staffing decisions.
                - Repeat the analysis quarterly to monitor progress and risk trends.
                """)

else:
    st.info("Please upload the Data Summary Excel file to start the analysis.")
