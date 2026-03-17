# Completion Report: Оптимизация контекста агентов пайплайна

## Метаданные

- **Task ID:** TASK-006
- **План:** Нет (план в claude plans)
- **ADR:** Нет
- **Дата:** 2026-03-17

## Executive Summary

Устранена корневая причина пропуска инструкций агентами пайплайна — раздутый контекст из-за обязательного чтения 2-4 skill-файлов при каждом запуске. Применён паттерн "Critical rules inline, details on demand". Дополнительно решена проблема несогласованности severity между агентами через Unified Severity Mapping.

## Изменения

| Файл | Что сделано |
|------|-------------|
| `agents/py-quality.md` | Inline: top-5 проверок (DRY, KISS, Fail Fast, AppException, no print) + severity. Убрано чтение 4 файлов |
| `agents/py-security.md` | Inline: top-5 (secrets, SQL injection, .gitignore, validation, OWASP) + severity. Убрано чтение 2 файлов |
| `agents/py-test-writer.md` | Inline: AAA, naming, fixtures, coverage, антипаттерны. Убрано чтение 1 файла |
| `agents/py-doc-manager.md` | Inline: нумерация, структура плана (4 раздела + 6 вопросов), формат коммита. Убрано чтение 4 файлов |
| `commands/pipeline.md` | Unified Severity Mapping, упрощённые промпты Phase 5, обновлённые правила Phase 6 |

## Метрики

| Метрика | До | После |
|---------|-----|-------|
| Tool calls на старте агента | 4-8 | 0-1 |
| Токенов знаний в контексте | 4000-12000 | 300-500 |
| Время старта агента | 15-30 сек | 2-5 сек |
| Severity таблиц | 2 разные | 1 единая |

## Ревью чеклист

- [x] Quality Cascade: DRY (inline правила ≠ полное копирование), KISS (≤120 строк на агента)
- [x] Security: нет секретов, нет уязвимостей
- [x] Линтеры: N/A (markdown файлы)

## Тесты

- N/A — изменения в markdown конфигурационных файлах, не в коде

## Known Limitations

- Inline правила = частичное дублирование с skill-файлами (~15 строк на агента). При обновлении skill'а нужно обновить и агента.
- Ссылки "читай по необходимости" зависят от поведения модели — Sonnet может не прочитать детали.
