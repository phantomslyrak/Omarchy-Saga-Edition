# Omarchy Saga Edition

Исходники стабильной **v1.0**, перенесённые из работающей Omarchy на Xiaomi
RedmiBook 16 2025 для разработки v1.1. Это перенос исходников: установленные
компоненты не заменялись, повторная сборка системы не выполнялась.

| Компонент | Исходники | Назначение |
| --- | --- | --- |
| SagaBoot | `components/sagaboot/` | Plymouth, QML-макеты, Saga Runes, текстовый fallback, процедуры UKI/addon и Console Recovery |
| SagaLock | `components/sagalock/` | QML, руны, MPRIS, погода, телеметрия и интеграция со штатным lock host |
| SagaSDDM | `components/sagasddm/` | Установленная QML-тема и исходные процедуры установки/обновления |
| Desktop Reveal | `components/desktop-reveal/` | Патч Hyprland, изменённые четыре файла, тесты, controller и launchers; переход 700 мс |

Быстрая безопасная проверка из корня:

```bash
python3 -B scripts/test/check-sources.py
python3 -B scripts/test/run-unit-tests.py
```

Проверки создают временные файлы только в `.local/` этого репозитория.
Не запускайте install/rollback/session/control helpers при обычной проверке.

- [Архитектура](docs/architecture/README.md)
- [Разработка, зависимости и сборка](docs/development/README.md)
- [Происхождение и выбор версий](docs/development/PROVENANCE.md)
- [Установка: границы и порядок подготовки](docs/installation/README.md)
- [Восстановление](docs/recovery/README.md)
- [Ресурсы и сторонние лицензии](assets/README.md)
- [Результаты переноса](releases/v1.0/MIGRATION.md)

**Ограничения:** artwork и шрифты не распространяются; нужны внешние зависимости.
Boot-комплект требует приватных входных файлов, отсутствующих в Git. Исторические
установщики не являются универсальным установщиком v1.1. Лицензия собственного
кода проекта ещё не выбрана; корневой LICENSE намеренно не создан. Условия
скопированного стороннего кода сохранены отдельно.

*A TRUE WARRIOR NEEDS NO SWORD.*
