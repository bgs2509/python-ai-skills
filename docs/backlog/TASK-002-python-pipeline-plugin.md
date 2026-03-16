# TASK-002: Python Pipeline плагин с оркестрацией и агентами

## Статус

Done

## Описание

Создать python-pipeline плагин для Claude Code, который оркестрирует 8 фаз
разработки (intake → commit) с помощью 4 специализированных агентов
(py-quality, py-security, py-test-writer, py-doc-manager). Плагин автоматически
применяет skill-стандарты проекта через Routing Table и запускает параллельный
Quality Gate.

## Приоритет

High

## Связанные артефакты

- План: Нет
- ADR: Нет (архитектура описана в commands/pipeline.md)
- Отчёт: docs/reports/2026-03-16-python-pipeline-plugin.md
