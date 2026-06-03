import pandas as pd
import numpy as np


class DataValidationReport:
    """Отчет по проверкам качества и согласованности данных."""

    def __init__(self):
        self.checks = []
        self.issues = []
        self.warnings = []

    def add_check(self, check_name: str, passed: bool, details: str = ""):
        """Добавление результата проверки."""

        status = "✓ OK" if passed else "✗ ОШИБКА"

        self.checks.append(
            {
                "check": check_name,
                "status": status,
                "passed": passed,
                "details": details,
            }
        )

        if not passed:
            self.issues.append(f"{check_name}: {details}")

    def add_warning(self, message: str):
        """Добавление предупреждения (не блокирует выполнение)."""

        self.warnings.append(message)

    def get_report(self) -> str:
        """Формирование текстового отчета по проверкам."""

        report = "\n=== ПРОВЕРКА КАЧЕСТВА ДАННЫХ ===\n"

        for check in self.checks:
            report += f"{check['status']}: {check['check']}"

            if check["details"]:
                report += f" ({check['details']})"

            report += "\n"

        if self.warnings:
            report += "\n⚠ ПРЕДУПРЕЖДЕНИЯ:\n"

            for warning in self.warnings:
                report += f"  - {warning}\n"

        return report

    def is_valid(self) -> bool:
        """Проверка, что критических ошибок нет."""

        return len(self.issues) == 0


def validate_data(
    df: pd.DataFrame,
    metrics_df: pd.DataFrame,
) -> DataValidationReport:
    """
    Комплексная проверка качества и согласованности данных.

    Проверяются:
    - полнота данных
    - корректность справочников
    - логическая согласованность метрик
    """

    report = DataValidationReport()

    # 1. Проверка пропусков в критических полях
    critical_cols = [
        "user_id",
        "month",
        "plan",
        "monthly_price",
        "payment_status",
        "amount_paid",
        "is_active",
    ]

    missing = df[critical_cols].isnull().sum().sum()

    report.add_check(
        "Отсутствие пропусков в критических полях",
        missing == 0,
        f"Найдено пропусков: {missing}" if missing > 0 else "Пропуски отсутствуют",
    )

    # 2. Проверка корректности user_id
    valid_user_ids = bool(
        (df["user_id"] > 0).all()
        and (df["user_id"] == df["user_id"].astype(int)).all()
    )

    report.add_check(
        "Корректность идентификаторов пользователей",
        valid_user_ids,
        "user_id должен быть положительным целым числом",
    )

    # 3. Проверка диапазона месяцев
    valid_months = bool(df["month"].between(1, 12).all())

    report.add_check(
        "Корректность значений месяца",
        valid_months,
        f"Ожидался диапазон 1–12. Найдено: {sorted(df['month'].unique())}",
    )

    # 4. Проверка тарифных планов
    valid_plans = set(df["plan"].unique()).issubset(
        {"basic", "standard", "premium"}
    )

    report.add_check(
        "Корректность тарифных планов",
        valid_plans,
        f"Обнаружены планы: {set(df['plan'].unique())}",
    )

    # 5. Проверка статусов платежей
    valid_statuses = set(df["payment_status"].unique()).issubset(
        {"paid", "failed"}
    )

    report.add_check(
        "Корректность статусов платежей",
        valid_statuses,
        f"Обнаружены статусы: {set(df['payment_status'].unique())}",
    )

    # 6. Согласованность сумм оплат
    amount_consistency = bool(
        (df[df["payment_status"] == "paid"]["amount_paid"] > 0).all()
        and (df[df["payment_status"] == "failed"]["amount_paid"] == 0).all()
    )

    report.add_check(
        "Согласованность статусов и оплат",
        amount_consistency,
        "paid → amount > 0, failed → amount = 0",
    )

    # 7. Проверка бинарного признака активности
    valid_active = set(df["is_active"].unique()).issubset({0, 1})

    report.add_check(
        "Корректность флага активности",
        valid_active,
        "is_active должен быть 0 или 1",
    )

    # 8. Проверка логики оттока (нет возвратов после ухода)
    churn_violations = 0

    for user_id in df["user_id"].unique():
        user_data = df[df["user_id"] == user_id].sort_values("month")

        active_by_month = user_data.set_index("month")["is_active"].to_dict()

        was_inactive = False

        for month in sorted(active_by_month.keys()):
            if was_inactive and active_by_month[month] == 1:
                churn_violations += 1
                break

            if active_by_month[month] == 0:
                was_inactive = True

    churn_check_pass = churn_violations == 0

    report.add_check(
        "Отсутствие повторной активации после оттока",
        churn_check_pass,
        f"Нарушений: {churn_violations}",
    )

    # 9. Проверка неизменности цены для пользователя
    price_consistency = bool(
        df.groupby("user_id")["monthly_price"].nunique().max() == 1
    )

    report.add_check(
        "Стабильность тарифа для пользователя",
        price_consistency,
        "У одного пользователя не должно быть разных цен",
    )

    # 10. Сверка выручки между сырыми данными и метриками
    total_revenue_data = df[df["payment_status"] == "paid"][
        "amount_paid"
    ].sum()

    total_revenue_metrics = metrics_df["monthly_revenue"].sum()

    revenue_match = abs(
        total_revenue_data - total_revenue_metrics
    ) < 0.01

    report.add_check(
        "Сверка выручки (данные vs метрики)",
        revenue_match,
        f"Данные: {total_revenue_data}, Метрики: {total_revenue_metrics}",
    )

    # 11. Проверка активных пользователей в первом месяце
    month_1_data = df[df["month"] == 1]

    month_1_active = len(
        month_1_data[month_1_data["is_active"] == 1]
    )

    month_1_metrics = metrics_df[
        metrics_df["month"] == 1
    ]["active_users"].values[0]

    month_1_match = bool(month_1_active == month_1_metrics)

    report.add_check(
        "Активные пользователи (1-й месяц)",
        month_1_match,
        f"Данные: {month_1_active}, Метрики: {month_1_metrics}",
    )

    # Предупреждения (не блокируют выполнение)
    churn_rate_max = metrics_df["churn_rate"].max()

    if churn_rate_max > 30:
        report.add_warning(
            f"Высокий пик оттока: {churn_rate_max:.1f}%"
        )

    retention_rate = 100 - metrics_df[
        metrics_df["month"] == 12
    ]["churn_rate"].values[0]

    if retention_rate < 50:
        report.add_warning(
            f"Низкое удержание за 12 месяцев: {retention_rate:.1f}%"
        )

    return report