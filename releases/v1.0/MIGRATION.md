# Перенос v1.0 в Git

27 октября 2026. Основа — установленная и принятая пользователем v1.0 на
Xiaomi RedmiBook 16 2025. Повторная аппаратная приёмка не выполнялась.

Перенесены все четыре компонента: SagaBoot (QML/Plymouth, hooks, финальные
build/install/rollback исходники), SagaLock (QML, руны, telemetry JS, weather
Python, Omacale integration), SagaSDDM (фактическая установленная QML-тема,
исходники начального install и последующего rune update), Desktop Reveal
(переносимый patch, четыре изменённых C++ файла, тесты, build/control/session).

Файлы сравнивались с установленными версиями и release/work counterparts.
SagaLock.qml совпадает с SagaLock-v1.0 snapshot; Main.qml и RuneMask.qml SDDM —
с финальными work-файлами. SHA Desktop Reveal patch совпадает с manifest.
Его применение и снятие проверены в локальной копии точных upstream Git blobs;
все четыре результата совпали с переносимыми source-файлами. Обнаруженное в старой
upstream-копии лишнее завершающее newline не использовано как эталон: взята
исправленная baseline из локальной истории и проверена по Git tree upstream.

Каждая копия имеет source SHA256 и SHA256 результата в
[provenance.json](../../docs/development/provenance.json). `.in` означает шаблон:
личный home заменён `@SAGA_HOME@`, имя пользователя — `@SAGA_USER@`.
Пути отдельных тестов адаптированы к репозиторию. Других изменений production
исходников при импорте не вносилось.

## Исключения

Не включены private UKI backups, EFI/UKI/addon payload, initramfs и распакованные
деревья, cmdline/уникальные идентификаторы дисков, LUKS/TPM сведения, recovery
information, приватные deployment/runtime manifests, autologin User, личные
Hyprland/Omarchy configs, кэши, старые логи и screenshots, VM artifacts, бинарники
и полный upstream Hyprland. .ssh не исследовался. SummaWay не копировался.
Все изображения/шрифты оставлены в исходных локальных расположениях вне Git;
права на artwork Vinland Saga и производные не подтверждены.

## Проверки этого переноса

- Python AST и Bash syntax для исходников и шаблонов.
- Проверки SHA всех импортированных файлов, ссылок Markdown и локальных QML imports.
- 16 изолированных weather unit tests, 34 telemetry parser checks.
- Native Plymouth callbacks: 2560×1600, 2048×1280, 1280×800 и 1920×1080 с двумя
  heads; negative control отклоняет неисправную маску.
- C++ policy tests: duration bounds, OutCubic/первый кадр/повторный timeline,
  owner/mode/symlink/FIFO/oversize checks и удаление локального test-флага.
- Четыре чистых/mocked session unit cases; watchdog с внешним launcher и реальная
  graphical launch проверка не запускались.
- Qt6 qmllint RuneMask/NorthernFrame для SDDM и SagaLock без замечаний.
- Точный patch apply/reverse, без полной пересборки Hyprland.
- Проверки списка Git, текстового содержимого, размеров и известных secret patterns;
  ручной просмотр личных путей и исключаемых типов. Pattern scanner не доказывает
  отсутствие произвольных неизвестных секретов.

Полной сборки, установки, VM, lock/suspend, reboot, перезапуска сервисов и обновления
пакетов не было. Корневой LICENSE намеренно не создан: лицензия собственного
кода не выбрана; копии upstream license notices сохранены.

## Воспроизводимость и неизменность системы

Зависимости и версии закреплены в [инструкции разработки](../../docs/development/README.md).
Полный clone без внешних artwork/fonts, Explorer/Omacale/Omarchy runtime,
зависимостей C++ и приватных boot inputs не воспроизводит идентичный установленный
образ. Старые install-kit scripts сохранены честно; универсальный безопасный
установщик для другой машины ещё предстоит разработать. Сборочный helper требует
полной точной базы Hyprland и scanner/glaze snapshots, а не локальной synthetic Git-истории.

Перед/после проверены SHA256 **982 доступных исходных и установленных файлов**:
изменений нет. Для **21007 записей SummaWay** совпали mode/size/mtime/ctime и
symlink targets без чтения его содержимого. Все выполненные агентом операции записи
направлены исключительно внутрь нового репозитория.
`/boot/limine.conf` недоступен для чтения; ESP/UKI не перехешировались, root-доступ
не запрашивался. Отсутствие записей агентом подтверждается выполненными командами;
полная побайтовая проверка закрытого ESP не заявляется.
Машинная сводка — [migration-checks.json](migration-checks.json).

Первый локальный коммит создаётся с сообщением
`feat: перенести исходники Omarchy Saga Edition v1.0`.
Remote не добавляется, push не выполняется.

`git diff --check` отмечает исходные пробелы в сохранённых upstream XML/Plymouth
и context-строках patch/diff. Они оставлены побайтно ради provenance и применения
патчей; это не ошибки синтаксических проверок. Новая документация и новые helpers
проверены отдельно без этих исторических файлов.
