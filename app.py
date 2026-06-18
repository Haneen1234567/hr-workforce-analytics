from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Iterable

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="HR Workforce Analytics Dashboard",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)


SHEET_EMPLOYEES = "Employees"
SHEET_BRANCHES = "Branches"
SHEET_AREAS = "Areas"


COLUMN_ALIASES = {
    "employee": [
        "employee",
        "employee name",
        "employee_name",
        "staff",
        "staff name",
        "officer",
        "loan officer",
        "موظف",
        "اسم الموظف",
    ],
    "branch": ["branch", "branch name", "branch_name", "فرع", "اسم الفرع"],
    "area": ["area", "area name", "area_name", "region", "منطقة", "اسم المنطقة"],
    "portfolio": [
        "portfolio",
        "portfolio amount",
        "outstanding portfolio",
        "portfolio balance",
        "محفظة",
        "اجمالي المحفظة",
        "إجمالي المحفظة",
    ],
    "customers": [
        "customers",
        "clients",
        "number of customers",
        "customer count",
        "عدد العملاء",
        "عملاء",
        "زبائن",
    ],
    "collection": [
        "collection",
        "collected",
        "total collection",
        "actual collection",
        "تحصيل",
        "اجمالي التحصيل",
        "إجمالي التحصيل",
    ],
    "collection_target": [
        "collection target",
        "target collection",
        "collection forecast",
        "expected collection",
        "forecast collection",
        "هدف التحصيل",
        "توقعات التحصيل",
    ],
    "loans": ["loans", "loan count", "total loans", "عدد القروض", "قروض"],
    "growth": ["growth", "growth rate", "portfolio growth", "نمو", "معدل النمو"],
    "portfolio_2025": ["portfolio 2025", "portfolio_2025", "2025 portfolio", "محفظة 2025"],
    "portfolio_2026": ["portfolio 2026", "portfolio_2026", "2026 portfolio", "محفظة 2026"],
    "hire_date": ["hire date", "hire_date", "joining date", "start date", "تاريخ التعيين", "تاريخ الالتحاق"],
    "loan_sent_to_collection": [
        "loan sent to collection",
        "sent to collection",
        "collection loans",
        "قروض للتحصيل",
    ],
    "provision": ["provision", "مخصص", "مخصصات"],
    "par": ["par", "portfolio at risk", "PAR"],
    "bar": ["bar", "balance at risk", "BAR"],
}


@dataclass(frozen=True)
class WorkbookData:
    employees: pd.DataFrame
    branches: pd.DataFrame
    areas: pd.DataFrame


def normalize_text(value: object) -> str:
