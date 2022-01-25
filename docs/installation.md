# Установка

## Установка на ОС Windows

1. [Загрузите](https://github.com/sembruk/sportorg-plus/releases/latest) файл установки \*.msi
для своего типа системы (win32 или win64) со страницы последнего релиза.
1. Установите программу.
По умолчанию программа будет установлена в `C:\Users\пользователь\AppData\Local\Programs\SportOrgPlus`,
и будет создан ярлык запуска на рабочем столе.

### Запуск на ОС Windows

Запустите исполняемый файл `SportOrg.exe` (или `SportOrgPlus.exe` в новых версиях)
из папки установки программы или соответствующий ярлык на рабочем столе.

## Установка на ОС GNU/Linux

Скачайте проект

```commandline
git clone https://github.com/sembruk/sportorg-plus.git
cd sportorg-plus
```

Установите зависимости

```commandline
pip3 install -r requirements.txt
```

### Запуск на ОС GNU/Linux

```commandline
cd sportorg-plus
./SportOrg.pyw
```

