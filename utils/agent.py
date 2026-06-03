"""
Модуль генерации аналитической отчетности.

Использует LLM для анализа бизнес-метрик подписочной модели,
формирования выводов и рекомендаций.
"""

import os
import json
from typing import Optional
import pandas as pd


class AgenticReportingAgent:
    """
    Агент для формирования бизнес-аналитики по подписочной модели.

    Этапы работы:
    1. Подготовка данных — преобразование метрик в структурированный контекст.
    2. Анализ — выявление трендов и закономерностей.
    3. Проверка корректности — контроль согласованности выводов.
    4. Формирование отчета — подготовка итогового отчета для бизнеса.
    """
    
    def __init__(self):
        """Инициализация агента"""
        self.model = "claude-3-5-sonnet-20241022"
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not self.api_key:
            # Если API недоступен, используется локальный анализ
            self.use_local_analysis = True
        else:
            self.use_local_analysis = False
            try:
                import anthropic as anthropic_module
                self.client = anthropic_module.Anthropic(api_key=self.api_key)
            except ImportError:
                print("Предупреждение: пакет anthropic не установлен, будет использован локальный анализ")
                self.use_local_analysis = True
    
    def analyze_metrics(self, metrics_df: pd.DataFrame, summary: dict) -> dict:
        """
        Выполняет анализ метрик и формирует выводы.

        Args:
            metrics_df: таблица с помесячными метриками
            summary: агрегированные показатели

        Returns:
            Результаты анализа
        """
        
        if self.use_local_analysis:
            return self._local_analysis(metrics_df, summary)
        else:
            return self._agentic_analysis(metrics_df, summary)
    
    def _agentic_analysis(self, metrics_df: pd.DataFrame, summary: dict) -> dict:
        """
        Анализ данных с помощью Claude API.
        """
        
        # Подготовка данных для передачи в модель
        metrics_json = metrics_df.to_json(orient='records', indent=2)
        
        # Этап 1. Анализ динамики показателей
        trends_prompt = f"""
            Ты работаешь бизнес-аналитиком в финтех-компании.

            Проанализируй данные подписочной модели и определи основные тенденции.

            ДАННЫЕ:

            {metrics_json}

            СВОДНЫЕ ПОКАЗАТЕЛИ:

            {json.dumps(summary, indent=2)}

            Верни результат строго в формате JSON:

            {{
                "revenue_trend": "описание динамики выручки",
                "churn_trend": "описание динамики оттока",
                "user_trend": "описание динамики активных пользователей",
                "arpu_trend": "описание динамики ARPU",
                "key_inflection_points": [
                    "месяц и причина изменения",
                    ...
                ]
            }}
        """
        
        try:
            trends_response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": trends_prompt}]
            )
            trends_text = trends_response.content[0].text
            trends = json.loads(trends_text)
        except Exception as e:
            print(f"Ошибка анализа трендов: {e}")
            trends = self._local_trend_analysis(metrics_df)
        
        # Этап 2. Формирование выводов и рекомендаций
        insights_prompt = f"""
            На основе метрик и выявленных тенденций сформируй от 3 до 5 ключевых выводов.

            МЕТРИКИ:

            {metrics_json}

            ТРЕНДЫ:

            {json.dumps(trends, indent=2)}

            Сосредоточься на следующих вопросах:

            1. Возможные причины изменений оттока.
            2. Точки роста выручки.
            3. Возможности повышения удержания пользователей.
            4. Особенности пользовательского поведения.
            5. Потенциальные риски и возможности.

            Верни результат строго в формате JSON:

            {{
                "insights": [
                    {{
                        "insight": "вывод",
                        "business_impact": "влияние на бизнес",
                        "recommendation": "рекомендация"
                    }}
                ]
            }}
        """
        
        try:
            insights_response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": insights_prompt}]
            )
            insights_text = insights_response.content[0].text
            insights = json.loads(insights_text)
        except Exception as e:
            print(f"Ошибка формирования рекомендаций: {e}")
            insights = {"insights": []}
        
        return {
            "trends": trends,
            "insights": insights,
            "method": "agentic_analysis"
        }
    
    def _local_analysis(self, metrics_df: pd.DataFrame, summary: dict) -> dict:
        """
        Локальный анализ без использования внешних моделей.
        """
        
        trends = self._local_trend_analysis(metrics_df)
        insights = self._local_insight_generation(metrics_df, trends)
        
        return {
            "trends": trends,
            "insights": {"insights": insights},
            "method": "local_analysis"
        }
    
    def _local_trend_analysis(self, metrics_df: pd.DataFrame) -> dict:
        """Анализ трендов на основе статистических расчетов."""
        
        revenue_change = (
            (metrics_df['monthly_revenue'].iloc[-1] - metrics_df['monthly_revenue'].iloc[0]) /
            metrics_df['monthly_revenue'].iloc[0] * 100
        )
        
        churn_trend = "растет" if metrics_df['churn_rate'].iloc[-1] > metrics_df['churn_rate'].iloc[0] else "убывает"
        user_trend = "снижается" if metrics_df['active_users'].iloc[-1] < metrics_df['active_users'].iloc[0] else "стабилен"
        
        return {
            "revenue_trend": f"Выручка {'увеличилась' if revenue_change > 0 else 'снизилась'} на {abs(revenue_change):.1f}% за анализируемый период",
            "churn_trend": f"Отток пользователей {churn_trend}",
            "user_trend": f"Количество активных пользователей {user_trend}",
            "arpu_trend": "Изменения ARPU связаны с изменением структуры пользовательской базы",
            "key_inflection_points": [
                f"Месяц {int(metrics_df['monthly_revenue'].idxmax()) + 1}: максимальная выручка",
                f"Месяц {int(metrics_df['churn_rate'].idxmax()) + 1}: максимальный отток"
            ]
        }
    
    def _local_insight_generation(self, metrics_df: pd.DataFrame, trends: dict) -> list:
        """Формирование выводов без использования LLM."""
        
        insights = []
        
        # Инсайт 1: Отток пользователей
        total_churned = metrics_df['churned_users'].sum()
        insights.append({
            "insight": f"За период отток составил {total_churned} пользователей",
            "business_impact": "Снижение клиентской базы оказывает влияние на темпы роста",
            "recommendation": "Рекомендуется провести анализ групп пользователей с высоким риском оттока"
        })
        
        # Инсайт 2: Стабильность выручки
        revenue_std = metrics_df['monthly_revenue'].std()
        insights.append({
            "insight": f"Выручка демонстрирует {'высокую' if revenue_std > metrics_df['monthly_revenue'].mean() * 0.2 else 'низкую'} вариативность по месяцам",
            "business_impact": "Влияет на точность прогнозирования финансовых показателей",
            "recommendation": "Рекомендуется определить причины колебаний и оценить необходимость корректировки тарифов"
        })
        
        # Инсайт 3: ARPU динамика
        final_arpu = metrics_df['arpu'].iloc[-1]
        initial_arpu = metrics_df['arpu'].iloc[0]
        insights.append({
            "insight": f"ARPU {'вырос' if final_arpu > initial_arpu else 'снизился'} с ${initial_arpu:.2f} до ${final_arpu:.2f}",
            "business_impact": f"Средняя ценность пользователя {'увеличивается' if final_arpu > initial_arpu else 'снижается'}",
            "recommendation": "Проверить эффективность тарифной сетки и механик допродаж"
        })
        
        return insights
    
    def generate_report(
        self,
        metrics_df: pd.DataFrame,
        analysis: dict,
        validation_report_text: str,
    ) -> str:
        """
        Формирует итоговый аналитический отчет по подписочной модели.
        """

        summary = {
            "total_revenue": metrics_df["monthly_revenue"].sum(),
            "avg_active_users": metrics_df["active_users"].mean(),
            "total_churned": metrics_df["churned_users"].sum(),
            "avg_churn_rate": metrics_df["churn_rate"].mean(),
            "final_retention_rate": 100 - metrics_df["churn_rate"].iloc[-1],
        }

        report = "# Отчет по ключевым метрикам подписочной модели\n\n"

        report += "## Краткое резюме\n\n"
        report += (
            f"- **Суммарная выручка за период:** "
            f"${summary['total_revenue']:.2f}\n"
        )
        report += (
            f"- **Среднее количество активных пользователей:** "
            f"{summary['avg_active_users']:.0f}\n"
        )
        report += (
            f"- **Количество пользователей с оттоком:** "
            f"{summary['total_churned']:.0f}\n"
        )
        report += (
            f"- **Средний уровень оттока:** "
            f"{summary['avg_churn_rate']:.2f}%\n"
        )
        report += (
            f"- **Удержание пользователей в последнем месяце:** "
            f"{summary['final_retention_rate']:.2f}%\n\n"
        )

        report += "## Динамика показателей по месяцам\n\n"

        report += (
            "| Месяц | Выручка | Активные пользователи | "
            "Отток | ARPU |\n"
        )
        report += (
            "|--------|---------|----------------------|--------|------|\n"
        )

        for _, row in metrics_df.iterrows():
            report += (
                f"| {int(row['month'])} "
                f"| ${row['monthly_revenue']:.2f} "
                f"| {int(row['active_users'])} "
                f"| {row['churn_rate']:.2f}% "
                f"| ${row['arpu']:.2f} |\n"
            )

        report += "\n"

        trends = analysis.get("trends", {})

        report += "## Анализ динамики\n\n"
        report += (
            f"**Выручка:** "
            f"{trends.get('revenue_trend', 'Данные отсутствуют')}\n\n"
        )
        report += (
            f"**Отток пользователей:** "
            f"{trends.get('churn_trend', 'Данные отсутствуют')}\n\n"
        )
        report += (
            f"**Активная аудитория:** "
            f"{trends.get('user_trend', 'Данные отсутствуют')}\n\n"
        )
        report += (
            f"**ARPU:** "
            f"{trends.get('arpu_trend', 'Данные отсутствуют')}\n\n"
        )

        report += "## Основные выводы и рекомендации\n\n"

        insights_list = analysis.get("insights", {}).get("insights", [])

        for i, insight in enumerate(insights_list, start=1):
            if not isinstance(insight, dict):
                continue

            final_arpu = metrics_df["arpu"].iloc[-1]
            initial_arpu = metrics_df["arpu"].iloc[0]

            impact_text = insight.get(
                "business_impact",
                "Не указано",
            )

            impact_text = impact_text.replace(
                "{'improving' if final_arpu > initial_arpu else 'declining'}",
                (
                    "улучшается"
                    if final_arpu > initial_arpu
                    else "снижается"
                ),
            )

            report += (
                f"**{i}. "
                f"{insight.get('insight', 'Описание отсутствует')}**\n"
            )
            report += (
                f"   - Влияние на бизнес: {impact_text}\n"
            )
            report += (
                f"   - Рекомендация: "
                f"{insight.get('recommendation', 'Не указана')}\n\n"
            )

        report += "## Проверка качества данных\n\n"
        report += validation_report_text

        report += "\n## Методика анализа\n\n"

        method = analysis.get("method", "unknown")

        if method == "agentic_analysis":
            report += (
                "Отчет подготовлен с использованием языковой модели "
                "для анализа динамики показателей, поиска закономерностей "
                "и формирования рекомендаций по улучшению бизнес-метрик.\n"
            )
        else:
            report += (
                "Отчет подготовлен на основе локального статистического "
                "анализа без использования внешних моделей.\n"
            )

        return report


def create_agent() -> AgenticReportingAgent:
    """
    Создает экземпляр агента для формирования аналитической отчетности.
    """
    return AgenticReportingAgent()
