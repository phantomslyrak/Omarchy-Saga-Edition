# Восстановление

Процедуры ниже предназначены для будущей согласованной операции. При переносе
откат не выполнялся. Хеши и device paths нельзя обновлять вслепую.

При проблеме lock/desktop перейти в штатный авторизованный TTY. Не отключать PAM,
не убивать locker и не посылать unlock-session. Для следующего входа выбирать
обычную Omarchy/Hyprland session; системный Hyprland проектом не заменён.
Текущий private `permanent-session-staging/saga-reveal-toggle` поддерживает stock
и off, но меняет marker/runtime. Запускать только по отдельному разрешению.
Шаблон toggle сохранён в components/desktop-reveal/session.

SDDM: установленный `/usr/local/sbin/saga-sddm-rollback --check` проверяет сохранённый
backup и installed SHA. Выполнение без --check восстанавливает прежний route/theme
и требует отдельно разрешённого root-доступа. Исходник сохранён в
scripts/rollback. Приватные backups находятся в `/var/lib/saga-sddm/backups/`,
pointer — `/var/lib/saga-sddm/active-backup`. Они не копировались. При отдельном
откате RuneMask нужен manifest его обновления; начальный SDDM rollback может
отказать после последующих изменений, и этот guard обходить нельзя.

Boot: сначала выбрать отдельную Console Recovery без Plymouth либо исходный
Omarchy в Limine. Это не требует пересборки. Нельзя убивать реальный Plymouth
ради проверки fallback. При полной аварии — проверенный Live USB и сохранённые
приватные original/rollback manifest. Они остаются вне репозитория.

Важно: финальный SagaBoot был установлен с последующей сменой default на SagaBoot.
Исторический rollback проверяет SHA меню до/сразу после установки, поэтому после
смены default может отказать. Нужен индивидуальный план на основе действительного
меню и проверенного original; не отключать хеш-проверки. Архивные install.py,
rollback.py/.sh и rollback-template.sh — исходники процедур, не готовый набор
восстановления для произвольной машины.

Закрытый `/boot` не читался при переносе. Побайтовое совпадение действующих EFI/UKI
с подготовленным payload не заявляется. Независимой внешней резервной копии по
release evidence нет; оригинальные локальные backups не удалялись и не менялись.
