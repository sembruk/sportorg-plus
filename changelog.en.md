# SportOrgPlus Changelog

## v1.5.0 - 2025-01-20

* Added tab with control points coordinates and scores
* Implemented import of control points coordinates from IOF XML v3, GPX and CSV files
* Fixed import of courses from OCAD v8 txt files
* Added ability to add and remove participants through the dialog for editing the team
* Added check for updates every week at startup
* Implemented restoration of data read from cards after the program's premature termination (experimental function)
* Updated splits templates
* English interface language by default, if the system language differs from Russian
* Fixed known bugs

[All changes](https://github.com/sembruk/sportorg-plus/compare/v1.4.2...v1.5.0)

## v1.4.2 - 2024-08-21

* Add support for closing split edit and result edit dialogs with Ctrl+Enter and Escape
* Now, when opening the timekeeping settings and the Bluetooth turned on the program does not freeze
* Added CTRL+I combination for quick creation of SPORTident result

[All changes](https://github.com/sembruk/sportorg-plus/compare/v1.4.1...v1.4.2)

## v1.4.1 - 2024-03-19

* Update filter dialog (F2) from upstream
* Fix bug in person edit dialog
* If printing splits for more than 5 rows show question
* Switch SI icon after connecting SI station

[All changes](https://github.com/sembruk/sportorg-plus/compare/v1.4.0...v1.4.1)

## v1.4.0 - 2024-03-04

* Course with variable number of CPs (e.g. `*[]`, `*(31-45) 100 *(46-99)[]`) 
* Import entry list from IOF XML v3 (Tested with Orgeo)
* `Open Recent` menu option
* Updated Orgeo Live for rogaining and team race
* Set numbers for persons and teams separately
* Added setting for using card number as bib
* Save columns order between sessions
* Protect existing file from overwriting with empty file
* Prevent editing JSON file from 2 or more instances of the software
* Fix build for Windows

[All changes](https://github.com/sembruk/sportorg-plus/compare/v1.3.0...v1.4.0)

## v1.3.0 - 2024-02-07

* Export results to CSV file using jinja2 template
* Orgeo CSV import improved
* Start preparation dialog updated

[All changes](https://github.com/sembruk/sportorg-plus/compare/v1.2.2...v1.3.0)

## v1.2.2 - 2023-08-31

* If change group for person also change group for team
* Remove birth dates from reports
* If start time source is 'group' and a result has start time from station use station time

## v1.2.1 - 2022-07-06

* Fixed file loading with invalid scores_array
* Fixed Orgeo CSV import
* Subgroups in start report

[All changes](https://github.com/sembruk/sportorg-plus/compare/v1.2.0...v1.2.1)

## v1.2.0 - 2022-05-13

* Subgroups
* Updated report templates
* UTF-8 for JSON file
* Fix Orgeo CSV import
* Fix team result update after manual result edit

[All changes](https://github.com/sembruk/sportorg-plus/compare/v1.1.1...v1.2.0)

## v1.1.1 - 2021-12-23

* Autobuild for Windows

## v1.1.0 - 2021-11-29

* Split-teams action
* CP coords for splits from course description (e.g. '\*|31;100;200')
* Use sex of a participant
* Check mandatory CPs for rogaining
* Update templates of reports and splits
* Restore icons, autosave, statusbar, toolbar and logs tab from SportOrg v1.5
* Fixed bugs
* Translation update

[All changes](https://github.com/sembruk/sportorg-plus/compare/v1.0.0...v1.1.0)

## v1.0.0 - 2021-04-22

* Added rogaining full support (teams)
* Added some columns at tabs
* Updated Sportiduino lib
* Fixed some bugs

[All changes](https://github.com/sembruk/sportorg-plus/compare/3a69d94...v1.0.0)
