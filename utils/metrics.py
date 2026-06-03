import pandas as pd
import numpy as np


def calculate_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Расчет ключевых метрик по месяцам для подписочной модели.

    Метрики включают:
    - активных пользователей
    - платящих пользователей
    - отток пользователей
    - выручку за месяц
    - коэффициент оттока
    - ARPU (выручка на пользователя)
    """

    metrics_list = []

    for month in sorted(df["month"].unique()):
        month_data = df[df["month"] == month]

        # Активные пользователи за месяц
        active_users = len(month_data[month_data["is_active"] == 1])

        # Пользователи, совершившие оплату
        paid_users = len(month_data[month_data["payment_status"] == "paid"])

        # Выручка за месяц
        monthly_revenue = month_data[
            month_data["payment_status"] == "paid"
        ]["amount_paid"].sum()

        # Расчет оттока относительно прошлого месяца
        if month > 1:
            prev_month_data = df[df["month"] == month - 1]

            users_last_month = set(
                prev_month_data[
                    prev_month_data["is_active"] == 1
                ]["user_id"].unique()
            )

            users_this_month = set(
                month_data[
                    month_data["is_active"] == 1
                ]["user_id"].unique()
            )

            churned_users = len(users_last_month - users_this_month)

            churn_rate = (
                (churned_users / len(users_last_month) * 100)
                if len(users_last_month) > 0
                else 0
            )
        else:
            # Первый месяц — база для расчета оттока отсутствует
            churned_users = 0
            churn_rate = 0

        # ARPU (средняя выручка на активного пользователя)
        arpu = (
            monthly_revenue / active_users
            if active_users > 0
            else 0
        )

        metrics_list.append(
            {
                "month": month,
                "active_users": active_users,
                "paid_users": paid_users,
                "churned_users": churned_users,
                "monthly_revenue": monthly_revenue,
                "churn_rate": round(churn_rate, 2),
                "arpu": round(arpu, 2),
            }
        )

    return pd.DataFrame(metrics_list)


def get_monthly_summary(metrics_df: pd.DataFrame) -> dict:
    """
    Сводные показатели по рассчитанным метрикам.
    """

    return {
        "total_revenue": metrics_df["monthly_revenue"].sum(),
        "avg_active_users": metrics_df["active_users"].mean(),
        "total_churned": metrics_df["churned_users"].sum(),
        "avg_churn_rate": metrics_df["churn_rate"].mean(),
        "avg_arpu": metrics_df["arpu"].mean(),
        "max_revenue_month": metrics_df.loc[
            metrics_df["monthly_revenue"].idxmax(),
            "month",
        ],
        "max_churn_month": metrics_df.loc[
            metrics_df["churn_rate"].idxmax(),
            "month",
        ],
    }