# Импорт предварительных заявок

---

## Импорт данных заявки с сайта orgeo.ru

Текущая версия поддерживает импорт из файлов формата IOF XML v3 и CSV.

Преимущество импорта из файла IOF XML v3 в том,
что автоматически устанавливаются Свойства соревнований.

Файл CSV в свою очередь можно подготовить в табличном процессоре Excel или LibreOffice Calc.

### Формат файла CSV

Разделитель полей — точка с запятой (`;`).
Каждый участник указывается на отдельной строке.
В первой строке должны находится следующие названия столбцов:

- `Группа`
- `Имя`
- `Фамилия`
- `Пол` — `М` или `Ж`
- `Дата рождения` или `Год` — формат `ГГГГ-ММ-ДД` или `ГГГГ`
- `Номер чипа` — опционально
- `Команда` — необходимо для командных соревнований
- `Номер команды` или `Номер заявки` — необходимо для командных соревнований
- `Примечания` — опционально

Порядок столбцов произвольный.
Участники объединяются в команды по Номеру команды (номеру заявки), а не по названию команды.
Таким образом в списке команд может быть несколько разных команд с одинаковым названием.

### Импорт IOF XML v3

- На странице заявки вида `http://www.orgeo.ru/event/participants/...` в поле "Выгрузить в файл для программы"
выбрать **IOF XML 3, SportOrg**.
- Сохраните файл.
- В SportOrgPlus `Файл -> Импорт -> IOF XML` и укажите путь к сохранённому файлу.

### Импорт Orgeo CSV

- На странице заявки вида `http://www.orgeo.ru/event/participants/...` в поле "Выгрузить в файл для программы:"
выбрать **Excel CSV (кодировка UTF-8)** или **Excel CSV (кодировка Windows-1251)**.
- Сохраните файл.
- В SportOrgPlus `Файл -> Импорт -> Orgeo CSV` и укажите путь к сохранённому файлу.

