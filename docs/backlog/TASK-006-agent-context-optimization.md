# TASK-006: Оптимизация контекста агентов пайплайна

## Статус: Done

## Приоритет: Critical

## Описание

Агенты пайплайна (py-quality, py-security, py-test-writer, py-doc-manager) при запуске читали 2-4 skill-файла, загружая 4000-12000 токенов знаний в контекст. Это приводило к пропуску инструкций, неполным отчётам и медленной работе.

Решение: паттерн "Critical rules inline, details on demand" — критичные правила (severity, формат отчёта, top-5 проверок) встроены прямо в агент-файлы, ссылки на skill-файлы сохранены для деталей.

Дополнительно: добавлена единая таблица Unified Severity Mapping в pipeline.md для согласования severity между агентами.

## Связанные артефакты

- CHANGELOG.md (Unreleased)
- Report: docs/reports/2026-03-17-agent-context-optimization.md
