# Онлайн на локальном компьютере

Для создания онлайн результатов на локальном компьютере может помочь 
проект [LiveOrg](https://github.com/sportorg/liveorg).

## Зачем это нужно?

Как только вы захотели вывести результаты на отдельном мониторе
с автоматическим обновлением после каждого финиша.

## Начало работы

- Загрузить проект [LiveOrg](https://github.com/sportorg/liveorg)
- Ввести команды

```
pip install -r requirements.txt

python server.py
```

- Посмотреть [вопрос по этой теме](https://github.com/sportorg/liveorg/issues/1)
- В файле  `pysport/scripts/liveorg.py` программы SportOrg ввести:

```python
CONFIG = {
    'type': 'live',
    'enabled': True, # Поменять значение на True, было False
}
```

- Зайти на страницу `http://127.0.0.1:5000/admin`
    - Скопировать длинный url в программу SportOrg
    - На второй зайти