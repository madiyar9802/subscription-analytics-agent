import os
import random
import pandas as pd


def generate_subscriptions_csv(
    file_path="./data/subscriptions.csv",
    n_users=1000,
    n_months=12,
):
    if os.path.exists(file_path):
        print(f"Файл уже существует: {file_path}")
        return

    plans = {
        "basic": 10,
        "standard": 20,
        "premium": 40,
    }

    rows = []

    for user_id in range(1, n_users + 1):

        plan = random.choices(
            population=["basic", "standard", "premium"],
            weights=[0.6, 0.3, 0.1],
            k=1,
        )[0]

        price = plans[plan]
        active = True

        for month in range(1, n_months + 1):

            if not active:
                break

            churn_probability = 0.03 + month * 0.005
            payment_failed_probability = 0.04

            payment_status = (
                "failed"
                if random.random() < payment_failed_probability
                else "paid"
            )

            amount_paid = price if payment_status == "paid" else 0

            row = {
                "user_id": user_id,
                "month": month,
                "plan": plan,
                "monthly_price": price,
                "payment_status": payment_status,
                "amount_paid": amount_paid,
                "is_active": 1,
            }

            rows.append(row)

            if random.random() < churn_probability:
                rows[-1]["is_active"] = 0
                active = False

    df = pd.DataFrame(rows)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    df.to_csv(file_path, index=False)

    print(f"Файл создан: {file_path}")


if __name__ == "__main__":
    generate_subscriptions_csv()