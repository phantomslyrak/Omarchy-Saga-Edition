# Архитектура v1.0

Последовательность запуска: Limine → отдельный SagaBoot UKI + EFI addon →
SDDM SagaSDDM → public session wrapper → private guarded launcher →
UWSM/start-hyprland → отдельный Hyprland с Desktop Reveal.
Console Recovery использует отдельный UKI без Plymouth. Исходный Omarchy и
его системный Hyprland остаются самостоятельным вариантом запуска.

SagaLock загружается Lock Explorer 2.0.9 как my-sagalock. Его DesignBase,
PasswordField, LockInput и CoverArt остаются внешним API. Сохраняется структура
`lock-designs/` рядом с `plugins/io.github.sirjul1337.lock-explorer/`: относительные
импорты в QML намеренно оставлены как в установленном дизайне.
В чистом clone этой внешней директории нет.

RuneMask получает только длину и положение курсора, без пароля. Ошибка визуальной
маски возвращает штатное отображение поля. WeatherPanel запускает Python stdlib
adapter Open-Meteo с фиксированным городом Казань (публичный preset дизайна,
не измеренная геолокация). MPRIS только читает метаданные. Телеметрия читает
/proc/stat, /proc/meminfo, df / и BAT0; внешние устройства не опрашиваются.
Анимация Explorer zoom — 1200 мс, последующий compositor reveal — 700 мс.

Reveal снимает lock surface и subsurfaces в framebuffer при штатном unlock.
Первый кадр desktop полностью покрыт снимком, затем OutCubic меняет alpha.
Патч не добавляет собственный ввод и не разрешает аутентификацию. Повторный lock
очищает декоративное состояние. Ошибка framebuffer, HDR/зеркала и несовместимость
выходов приводят к обычному unlock без эффекта. Бюджет снимков — 64 МиБ.
Controller использует защищённый файл в /run/user/UID; его команды меняют runtime.

Рабочий wrapper вызывает `work/desktop-reveal-prototype/permanent-session-staging/`.
`permanent/saga-session.py` — альтернативная реализация, не фактический маршрут SDDM.
Launcher сверяет package version и приватный runtime manifest; обновлять его
автоматически при изменении пакетов нельзя. Проект не заменяет /usr/bin/Hyprland.
