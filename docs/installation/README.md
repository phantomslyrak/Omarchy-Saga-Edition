# Подготовка установки

Этот перенос не содержит универсального установщика. При переносе ни одна
установочная процедура не запускалась. До любого изменения действующей системы
нужно отдельное разрешение пользователя и конкретный reviewable staging.

Порядок будущей установки:

1. Проверить исходники и права ресурсов, подготовить зависимости и чистый staging.
2. Собрать отдельно Desktop Reveal на закреплённой базе; проверить patch, ABI,
   protocol headers и совместимость с целевой Omarchy. Системный Hyprland сохранить.
3. Проверить QML SagaLock/SDDM offscreen. Затем отдельно согласовать тестовую
   сессию и аппаратную проверку. Сам перенос опирается на уже принятую v1.0.
4. До копирования в системные пути сохранить проверенные originals вне Git,
   составить manifest, предусмотреть stock session и доступ к TTY/Live USB.
5. Согласовать точные целевые файлы и план отката. Не перезапускать SDDM в рабочей
   сессии. Desktop Reveal должен оставаться отдельной сессией с compatibility guard.
6. Для boot требуется отдельный план: приватный original UKI, актуальный kernel,
   initramfs/cmdline, original Limine и проверенная процедура PE sections.
   Никогда не переносить их в Git и не применять RedmiBook device paths к другому ПК.

Исторические процедуры сохранены для анализа:

| Файлы | Граница применимости |
| --- | --- |
| sagasddm/install.sh + tools/install-system.py.in | Начальная установка до RuneMask; список payload не содержит RuneMask. Ожидает прежнюю omarchy theme/session и private protected manifest; не переустанавливать поверх Stable |
| sagasddm/rune-password-v1/update.py | Отдельное последующее обновление Main/RuneMask; требует original-theme/update SHA manifests и root backup, которые не включены |
| desktop-reveal/session/*.in | Фактический guarded launcher и toggle как шаблоны; runtime manifest остаётся приватным |
| desktop-reveal/session/alternative/ | Другой механизм, не текущий маршрут SDDM; без compatibility.json не воспроизводится |
| sagaboot/deployment/ | Финальный install-kit, а не общий установщик Arch. Привязан к прежней раскладке устройства и приватным inputs |
| sagalock/integration/lock-screen.py | Реальный изменённый Omacale integration helper; при выполнении меняет пользовательские плагины. Не запускать для lint/test |

Пути назначения в действующей v1.0: `/usr/share/sddm/themes/saga-sddm`,
`/etc/sddm.conf.d/zzzzz-saga-sddm-theme.conf`,
`/usr/share/wayland-sessions/omarchy-saga.desktop`,
`/usr/local/libexec/saga-session-launcher`, `/usr/local/sbin/saga-sddm-rollback`.
`configs/sessions/` фиксирует public route без личного имени; `.in` — шаблоны,
не активные конфигурации. Autologin User и личные Hyprland configs не копировались.
Сам reveal не требует нового Hyprland config-фрагмента: это compositor patch.
