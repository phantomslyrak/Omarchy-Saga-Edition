# Ресурсы и права

Art Vinland Saga, фон с Торфинном, производные изображения, previews/screenshots
и файлы шрифтов **не включены в Git**. Утверждение «original» в старых metadata
не считается доказательством прав. Оригинальные локальные ресурсы не менялись.
Все растровые файлы и шрифты исключены .gitignore; не использовать git add -f.
Даже небольшие spin/dot/placeholder PNG оставлены вне Git: общей проверки прав
для всех растров этого релиза нет. dot/placeholder можно создать исходным
`components/sagaboot/tools/finish-theme.py` в изолированном staging.

Для локальной разработки используйте собственный рисунок или ресурс с
подтверждённой лицензией. Локальные копии помещаются в игнорируемый `.local/assets/`;
для испытания на отдельной системе нужно сохранить следующие runtime-пути:

| Потребитель | Ожидаемые файлы |
| --- | --- |
| SagaLock | `$HOME/.local/share/omarchy-saga-edition/assets/lock/fjord-clean-no-logo-v1.png` |
| SagaSDDM staging | `components/sagasddm/saga-sddm/assets/fjord-clean-no-logo-v1.png`, `NotoSans-Regular.ttf`, `NotoSerif-Regular.ttf` |
| Boot QML source | `components/sagaboot/source/plain.png`, `prompt.png` (пути шаблонов адаптировать в локальной копии) |
| Plymouth theme | `components/sagaboot/theme/bg.png`, `bg-plain.png`, `spin1.png` … `spin12.png`, `dot.png`, `placeholder.png`, `preview.png` |

Для SDDM нужны самостоятельно предоставленные Noto Sans/Serif с соответствующей
лицензией; проверяйте условия именно выбранного пакета шрифтов. Для fallback
нужны установленные Liberation Mono Regular/Bold; hook лишь ссылается на них.
Рабочие источники изображений находятся в исходном Saga `assets/lock/`, в
`releases/SagaBoot-v1.0/{source,theme}/` и установленном SDDM `assets/`.
Они не копируются автоматически в новую установку и не получают новую лицензию.

Сторонний код:

- Lock Explorer: MIT, закреплённый commit в [dependencies.json](../docs/development/dependencies.json);
  его сгенерированный Plymouth script и API имеют [исходное уведомление](../third_party/licenses/lock-explorer-MIT.txt).
- Четыре файла и patch Hyprland: [BSD upstream](../third_party/licenses/Hyprland-BSD.txt).
- Input-capture XML содержит собственный BSD copyright и условия прямо в файле.
- Omacale integration: [GPL-3.0](../third_party/licenses/Omacale-GPL-3.0.txt),
  источник Omacale 0.55.1, автор AyushKr2003. Остальные его плагины и artwork не копировались.

Лицензия собственного Saga-кода не выбрана. Корневой LICENSE не подготовлен;
это не снимает действующие обязанности по сторонним лицензиям и не объявляет
собственный код открыто лицензированным. До публичной публикации требуется
решение владельца о лицензии и проверка совместимости производных частей.
