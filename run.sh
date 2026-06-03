#!/usr/bin/env sh

# Запуск:
#   ./run.sh [YOUR_ANTHROPIC_API_KEY]
# Если ключ задан, он будет установлен в переменную окружения для текущего сеанса.
# Если нет, скрипт запустится с локальным анализом.

if [ -n "$1" ]; then
  export ANTHROPIC_API_KEY="$1"
  echo "Using provided ANTHROPIC_API_KEY"
else
  echo "No ANTHROPIC_API_KEY provided; running without Anthropic key."
fi

cd "$(dirname "$0")"
python utils/main.py
