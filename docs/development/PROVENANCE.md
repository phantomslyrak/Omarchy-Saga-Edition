# Происхождение и актуальность

Основа отбора — локальный `releases/Omarchy-Saga-Edition-v1.0/RELEASE.md`,
VERSIONS.json и manifest 511 установленных файлов, зафиксированные 27.10.2026.
Исходная база: `$HOME/.local/share/omarchy-saga-edition`.
[Машинный manifest](provenance.json) содержит для каждой копии исходный путь,
SHA256 оригинала, SHA256 копии и преобразование. `$HOME` в metadata — обозначение,
не требование определённого имени пользователя.

| Область | Выбранная версия и основание |
| --- | --- |
| SagaLock | Фактический `$HOME/.config/omarchy/lock-designs/SagaLock.qml` и четыре saga-подкаталога; release snapshot совпадает с установленным дизайном |
| SagaSDDM | `/usr/share/sddm/themes/saga-sddm`, включая финальный RuneMask; проверено против work/saga-sddm-v1/saga-sddm |
| SagaBoot | releases/SagaBoot-v1.0: source, theme, tools, native tests; позднее исправление fallback из work/sagaboot-final-deployment-20261027/patch |
| Boot deployment | Финальные исходники сборки и install-kit от 27.10; более ранние fallback/VM деревья не переносились |
| Desktop Reveal | saga-desktop-reveal.patch и четыре изменённых файла из work/desktop-reveal-prototype/source; SHA patch совпадает с исходным manifest, базовый upstream commit закреплён |
| Session | Установленный public wrapper и фактический permanent-session-staging launcher; alternative сохранён отдельно |
| Lock integration | Установленные Omacale scripts/lock-screen и handover.py; GPL-3.0-only. Omacale 0.55.1 не имеет локальной Git-истории, commit неизвестен |

Личные абсолютные home-пути заменены токеном `@SAGA_HOME@`; такие файлы имеют
суффикс `.in`, их нельзя запускать без отдельной адаптации и review. Остальные
перенесённые рабочие исходники побайтно сохранены. Только пути тестовых данных
в weather/telemetry/policy тестах адаптированы для репозитория, что отмечено в manifest.

`manifest.json.in` Desktop Reveal и `source-verification.json` — исторические
свидетельства сборки. Поле deployed=false описывает этап подготовки; текущий
статус Stable основан на позднем release и аппаратной приёмке пользователя.
Исторические результаты не выдаются за новые тесты этого переноса.

Отдельные старые preview/recovery Python utilities и VM harness не входят в
каноническую разработку: зависят от прежних fixture/work-каталогов, управляют
действующим locker либо являются промежуточными вариантами. Их оригиналы
сохранены на месте. Не переносились private manifests и полные личные настройки.
