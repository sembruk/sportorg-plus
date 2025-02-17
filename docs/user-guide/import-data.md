# Импорт данных

---

## Импортирование данных заявки (сделана на сайте orgeo.ru)

Текущая версия по умолчанию поддерживает формат «CSV Winorient с представителями».

Формат полей:

* Группа
* ФИО
* Коллектив
* Представитель
* Разряд
    * 0 = б/р
    * 1 = Iю
    * 2 = IIю
    * 3 = IIIю
    * 4 = I
    * 5 = II
    * 6 = III
    * 7 = КМС
    * 8 = МС
    * 9 = МСМК
    * 10 = ЗМС  // В программе будет указано МСМК
* Номер
* Год рождения
* Номер чипа
* Комментарий

![Screenshot](img/6.png)
![Screenshot](img/7.png)
![Screenshot](img/8.png)
![Screenshot](img/9.png)
![Screenshot](img/10.png)

## Импортирование данных о дистанциях (OCAD Courses v8)

![Screenshot](img/11.png)
![Screenshot](img/12.png)
![Screenshot](img/13.png)

## IOF XML 3.0

`Файл -> Импорт -> IOF XML`

Поддерживается `EntryList` - список участников

## Присвоение дистанций для групп

В SportOrg есть опция подбора дистанций по имени – если имя дистанции содержит в себе имя группы, то они связываются. Например, группа “Ж12” свяжется с дистанцией “М12,Ж12”

![Screenshot](img/14.png)
![Screenshot](img/15.png)
![Screenshot](img/16.png)

Из примера видно, что для МЭ и ЖЭ нужно указать дистанции вручную

Для редактирования группы 2 раза кликаем по ней или нажимаем Enter после выделения

![Screenshot](img/17.png)
![Screenshot](img/18.png)

Во всех выпадающих списках применяется фильтрация по введенному значению

![Screenshot](img/19.png)

## Присвоение коридоров для групп

Теперь можно прописать коридоры для групп

Есть также автоматическое присвоение коридоров, но оно нам сейчас не совсем подойдет, у нас 1 группа = 1 дистанция.

![Screenshot](img/20.png)

Присваиваем коридоры и порядок в коридоре согласно положению о соревнованиях

![Screenshot](img/21.jpg)
![Screenshot](img/22.png)
![Screenshot](img/23.png)

## Работа с участниками – фильтрация

Для отображения части участников, принадлежащих к одной группе или коллективу, можно использовать фильтрацию.

В текущей версии программы есть возможность фильтровать участников по группам и/или коллективам.

Для сброса фильтра необходимо установить пустые значения для поиска в диалоге фильтрации.

![Screenshot](img/24.png)
![Screenshot](img/25.png)
![Screenshot](img/26.png)
![Screenshot](img/27.png)
![Screenshot](img/28.png)
![Screenshot](img/29.png)
![Screenshot](img/30.png)
![Screenshot](img/31.png)
![Screenshot](img/32.png)
![Screenshot](img/33.png)
