# RowStrength (BeeWare/Briefcase + Toga)

## Быстрый старт (локально)
```bash
python -m pip install briefcase toga
briefcase dev
```

## Сборка под iOS
```bash
briefcase create iOS
briefcase build iOS
briefcase run iOS  # симулятор
```
После сборки открой Xcode-проект из папки `iOS` (или через Organizer архивируй и загружай в App Store Connect).

## Где лежат данные
JSON-файлы: `rowstrength/data/`
- `data_for_rowing_app.json`
- `data_for_strength_app.json`

## Конфиденциальность
Файл `ios/PrivacyInfo.xcprivacy` добавлен как базовый шаблон (отсутствие трекинга/сборов).