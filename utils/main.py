"""
Основной сценарий формирования аналитического отчета.

Последовательность выполнения:

1. Подготовка или генерация тестовых данных.
2. Расчет ключевых метрик по месяцам.
3. Проверка качества и целостности данных.
4. Формирование аналитических выводов.
5. Подготовка итогового отчета.
"""

import os
import sys

import pandas as pd

# Добавляем директорию со вспомогательными модулями в PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate import generate_subscriptions_csv
from metrics import calculate_metrics, get_monthly_summary
from validation import validate_data
from agent import create_agent


def ensure_data_exists(data_path: str = "./data/subscriptions.csv") -> str:
    """
    Проверяет наличие файла с данными.
    Если файл отсутствует — генерирует тестовый набор данных.
    """

    if not os.path.exists(data_path):
        print("📊 Файл с данными не найден. Выполняется генерация тестовых данных...")
        generate_subscriptions_csv(data_path)
    else:
        print(f"✓ Используется существующий файл: {data_path}")

    return data_path


def run_pipeline(
    data_path: str = "./data/subscriptions.csv",
    output_report_path: str = "./report.md",
) -> str:
    """
    Выполняет полный цикл подготовки аналитического отчета.

    Args:
        data_path: путь к CSV-файлу с данными.
        output_report_path: путь для сохранения итогового отчета.

    Returns:
        Текст сформированного отчета.
    """

    print("\n" + "=" * 70)
    print("АНАЛИЗ ПОДПИСОЧНОЙ МОДЕЛИ")
    print("=" * 70 + "\n")

    # Шаг 1. Подготовка данных
    print("[1/5] Проверка наличия данных...")
    data_path = ensure_data_exists(data_path)
    print("✓ Данные готовы к обработке\n")

    # Шаг 2. Расчет метрик
    print("[2/5] Загрузка данных и расчет метрик...")

    df = pd.read_csv(data_path)

    print(
        f"  - Загружено записей: {len(df)} "
        f"(уникальных пользователей: {df['user_id'].nunique()})"
    )

    metrics_df = calculate_metrics(df)
    summary = get_monthly_summary(metrics_df)

    print(f"  - Рассчитано периодов: {len(metrics_df)}")
    print(f"  - Общая выручка: ${summary['total_revenue']:.2f}")
    print(f"  - Средний ARPU: ${summary['avg_arpu']:.2f}")
    print("✓ Метрики успешно рассчитаны\n")

    # Шаг 3. Проверка качества данных
    print("[3/5] Проверка качества данных...")

    validation_report = validate_data(df, metrics_df)

    print(validation_report.get_report())

    if validation_report.is_valid():
        print("✓ Проверка качества данных успешно пройдена\n")
    else:
        print("⚠ Обнаружены замечания по качеству данных\n")

    # Шаг 4. Аналитика
    print("[4/5] Формирование аналитических выводов...")

    agent = create_agent()

    analysis_method = (
        "локальный анализ"
        if agent.use_local_analysis
        else "LLM-анализ (Claude API)"
    )

    print(f"  - Используемый метод: {analysis_method}")

    analysis = agent.analyze_metrics(metrics_df, summary)

    print("✓ Анализ завершен\n")

    # Шаг 5. Формирование отчета
    print("[5/5] Подготовка итогового отчета...")

    report = agent.generate_report(
        metrics_df,
        analysis,
        validation_report.get_report(),
    )

    os.makedirs(
        os.path.dirname(output_report_path) or ".",
        exist_ok=True,
    )

    with open(output_report_path, "w", encoding="utf-8") as report_file:
        report_file.write(report)

    print(f"✓ Отчет сохранен: {output_report_path}\n")

    print("=" * 70)
    print(report)
    print("=" * 70)

    return report


def main():
    """
    Точка входа в приложение.
    """

    script_dir = os.path.dirname(os.path.abspath(__file__))

    data_path = os.path.join(
        script_dir,
        "data",
        "subscriptions.csv",
    )

    report_path = os.path.join(
        os.path.dirname(script_dir),
        "report.md",
    )

    try:
        run_pipeline(
            data_path=data_path,
            output_report_path=report_path,
        )

        print("\n✅ Формирование отчета успешно завершено")
        return 0

    except Exception as error:
        print(f"\n❌ Ошибка выполнения: {error}")

        import traceback
        traceback.print_exc()

        return 1


if __name__ == "__main__":
    sys.exit(main())
