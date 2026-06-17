# Python Development Rules

## Стиль кода
- Используй 4 пробела для отступов (не табы)
- Предпочитай типизацию (TypeScript, Python type hints)
- Write code comments in English

## Git
- Коммит-сообщения на английском
- Формат: Conventional Commits + GRACE MODULE_ID как scope — `<type>(<MODULE_ID>): <description>` для кода, `<type>(<short-name>):` для meta (docs/chore/ci)
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `build`, `ci` — type обязателен всегда
- Делай коммит без подтверждения пользователя (когда работа atomic и проверена)
- НЕ делай `git push` кода автоматически — только по явному запросу пользователя
- `bd dolt push` (Beads persistence) разрешён автоматически в session close protocol

## Окружение
- Основной язык: Python 3.11+
- Пакетный менеджер: uv/pip
- ОС: Linux (Ubuntu)

## Документация
- Не создавай README.md без явного запроса
- Документируй только сложную логику, не очевидное

## Тестирование
- Используй pytest для Python
- TDD-подход: RED → GREEN → REFACTOR
- Не писать production-код без failing теста

## Производительность
- Не оптимизируй преждевременно
- Замеряй перед оптимизацией (профилирование)

## Зависимости
- Закрепляй версии в production строго через `==` (не `>=`, не `~=`, не `^`)
- При добавлении/обновлении зависимости — проверяй uv.lock на точное соответствие
- Context7 (`resolve-library-id` → `query-docs`) — обязателен в Design-фазе feature-workflow (steps 4, 7) для всех затрагиваемых библиотек + по 4 триггерам в Execution: (a) first contact с библиотекой в текущей сессии, (b) version bump vs design, (c) unknown/unfamiliar method, (d) library error в тестах. При следовании approved плану с pre-verified API — Context7 не требуется
- Регулярно обновляй зависимости для безопасности
- Минимизируй размер Docker образов
- Не добавляй лишние зависимости

## Формат планов в режиме планирования
> SSoT для планирования: skill `superpowers:writing-plans`.
> Использовать его для формата и структуры планов.
