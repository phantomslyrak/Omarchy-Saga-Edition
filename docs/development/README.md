# Разработка и сборка

Проверенная среда v1.0 — Arch/Omarchy на x86-64, не обещание совместимости
с любым rolling update. [Версии пакетов](../../releases/v1.0/VERSIONS.json)
считаны при фиксации стабильного релиза. [Внешние источники](dependencies.json)
закреплены по доступной локальной истории; сеть при переносе не использовалась.

Основные версии: Omarchy 4.0.6-1, Hyprland 0.56.2-4, Quickshell
0.3.2.r7.g2b4501a-1, Qt6 6.12.0, SDDM 0.21.0-7, Plymouth 26.134.222-3,
mkinitcpio 42.2-1, systemd 262.1-1, Limine 12.9.4-1, kernel 7.2.8-9-omarchy.

## Проверки

```bash
python3 -B scripts/test/check-sources.py
python3 -B scripts/test/run-unit-tests.py
```

Нужны Python3 stdlib, Bash, Git, Node.js, g++ с C++23, установленная
`/usr/lib/plymouth/script.so` и Qt6 qmllint. Suite не вызывает установщики,
композитор, lock/suspend и не меняет services. Plymouth тест использует
библиотеку с mock display, не daemon. Тестам погоды сеть подменена; телеметрия
читает только /proc. Все временные записи — `.local/` репозитория.
Полный QML lint/render зависит от Quickshell, SDDM context и Explorer imports;
прошедшая проверка рун не означает полного runtime-теста greeter/locker.
`/usr/bin/qmllint` здесь относится к другому инструменту; применяется
`/usr/lib/qt6/bin/qmllint`.

`tools/check` и другие исторические tests не входят в автоматический suite:
некоторые ожидают старый baseline, готовый бинарник, внешние fixtures или
управляют runtime. Их запуск требует отдельного анализа.

## Desktop Reveal

Точная база: [Hyprland efb50993780079460b0cbed1363e2166a2de1d9f](https://github.com/hyprwm/Hyprland/tree/efb50993780079460b0cbed1363e2166a2de1d9f)
(tag v0.56.2, установленный Arch пакет 0.56.2-4).
Патч `components/desktop-reveal/saga-desktop-reveal.patch`, SHA256
`6c55cef9d00d548462325ae8ce8b1d334821a50b7dd353131f78a66adad58f09`.
Он меняет SessionLockManager.cpp, Renderer.cpp/.hpp и добавляет SagaRevealPolicy.hpp.
Папка source содержит только эти четыре файла, не полную копию upstream.

Для ручной подготовки отдельного checkout (внутри `.local/`, не установленного
work-каталога) применяется `git apply --check /absolute/path/to/patch`, затем
`git apply /absolute/path/to/patch`. До применения checkout должен быть чистым
и иметь точный HEAD выше. Проверить результат можно скриптом
`scripts/test/check-reveal-patch.py /absolute/path/to/pristine/Hyprland`.
Он не меняет указанный checkout, проверяет исходные Git blob SHA и применяет/
снимает patch в новом временном дереве внутри `.local/`.

Сборочный helper сам получает отдельный checkout и submodules в
`components/desktop-reveal/build-source/`, применяет Saga patch, проверяет четыре
результирующих файла и добавляет compatibility patch протокола. Он не устанавливает
Hyprland. Для локального origin допускается `--from-repository /path/to/pristine/git`;
origin должен содержать настоящий полный commit, не маленький synthetic Git прототипа.
Существующая сеть и заранее подготовленные зависимости требуются отдельно.

До сборки подготовьте зависимости в `components/desktop-reveal/vendor/`:

| Каталог | Источник/версия |
| --- | --- |
| glaze | https://github.com/stephenberry/glaze, v7.2.0 (требуется 7.x, не 9.x) |
| hyprwayland-scanner | https://github.com/hyprwm/hyprwayland-scanner, v0.4.6 |

Точные Git tree SHA этих снимков — в dependencies.json. Сверьте
`git rev-parse HEAD^{tree}` с закреплёнными значениями. Они обозначают tree, не
подменяйте ими commit SHA. Scanner соберётся и установится только в локальный
`components/desktop-reveal/local-tools/`. Для сборки scanner нужны CMake, Ninja,
C++ toolchain и его upstream зависимости (в частности pugixml).
udis86 submodule — `5336633af70f3917760a6d441ff02d93477b0c86`, protocol submodule
0.7.0. Input-capture XML взят из
[protocols 76f3fa7bced84268f4a39c43c633b77ae68b727f](https://github.com/hyprwm/hyprland-protocols/tree/76f3fa7bced84268f4a39c43c633b77ae68b727f),
его BSD notice сохранён в XML. В исходной сборке 64 generated headers совпадали
с пакетом -4; новый helper также проверяет input-capture header. Полное совпадение
всех неизвестных downstream C++ патчей Arch -4 не доказано.

Нужны CMake/Ninja/GCC (C++26 в Hyprland), pkg-config, Wayland scanner/protocols,
OpenGL/EGL/GLES, glslang, Cairo/Pango/Pixman, libdrm/libinput/xkbcommon,
libdisplay-info/libeis, XWayland/XCB и остальные зависимости CMakeLists точного upstream.
Проверенная связка библиотек: Aquamarine 0.15.1, Hyprlang 0.6.8,
Hyprutils 0.14.2, Hyprcursor 0.1.13, Hyprgraphics 0.5.1.
Пакеты этим репозиторием автоматически не устанавливаются.

```bash
bash scripts/build/desktop-reveal.sh --jobs 2
```

Этот command предназначен для будущей разработки; при переносе не запускался.
Профилирование Tracy выключено. Результат — отдельный `bin/Hyprland-saga-reveal`
в компоненте. Он исключён из Git. Не запускать бинарник в действующей сессии,
не делать `cmake --install` для Hyprland и не заменять /usr/bin/Hyprland.
После изменения патча синхронизировать четыре эталонных source-файла осознанно,
проверить diff; старый provenance остаётся историей импорта, а не новым baseline.

## SagaLock / SagaSDDM

Это QML без компиляции проекта. Для локального offscreen staging скопировать
`lock-designs/` рядом с `plugins/io.github.sirjul1337.lock-explorer/` точного commit
из dependencies.json. Полный Explorer и его необходимые дизайны/API получить отдельно
с сохранением MIT notice. Нельзя указывать staging на действующие writable configs.
Потребуются Quickshell.Io, Shapes, MPRIS, curl, coreutils timeout/df и Noto/Liberation.
Настройки дизайна — [пример](../../configs/sagalock/explorer.example.json).
Новые настройки объединять с тестовым профилем, не заменять личный config этим примером.

SDDM содержит окончательные Main.qml, RuneMask.qml и NorthernFrame.qml из /usr/share.
Для preview требуются QtQuick.Controls.Basic, QtQuick.Shapes и SDDM context/greeter
в отдельном offscreen fixture. [Файлы ресурсов](../../assets/README.md) поставляются
пользователем. Прежние preview.sh/capture.cpp сохранены как исходники, их нельзя
принимать за готовый portable harness без прежних fixture-каталогов.

## SagaBoot

QML source + конфигурация → генератор custom/generate.sh Lock Explorer →
`tools/finish-theme.py` → Plymouth theme → EFI addon через Explorer root-theme.sh.
QML-макеты и конфигурация `.in` содержат отмеченные исходные пути; их нужно
адаптировать в локальной копии. Полный плагин и изображения — внешние зависимости.
Генератор и build_addon входят в закреплённый Explorer; его установленные tracked
файлы не имели локальных изменений при переносе.

`theme/omarchy-boot.script` — канонический готовый **текстовый исходник** темы.
Его native callback-тест не требует картинок. Малые dot/placeholder можно
восстановить исходным finish-theme.py с ImageMagick и доступным Noto Sans;
остальные изображения этим скриптом не создаются. Старый stage-only.sh.in требует
полного staging, source SHA manifest и previews: без них он намеренно не запускается.

Поздний fallback hook добавляет fontconfig policy, fc-match и Liberation Mono
в initramfs; `zz-plymouth-fallback.conf` фиксирует дополнительные зависимости.
Это исходник сборочного hook, не команда установки на текущем хосте.
`deployment/` содержит реальные процедуры получения финальных UKI через изменение
только допустимых PE sections оригинала. Приватные оригиналы, cmdline, readiness,
deployment/rollback manifests и payload исключены. **Полное восстановление идентичных
UKI из публичного clone невозможно.** Нельзя выдумывать эти входы или обходить SHA guards.
