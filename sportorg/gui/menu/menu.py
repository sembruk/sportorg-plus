from sportorg import config
from sportorg.language import _


def menu_list():
    return [
        {
            'title': _('File'),
            'actions': [
                {
                    'title': _('New'),
                    'shortcut': 'Ctrl+N',
                    'icon': config.icon_dir('file.svg'),
                    'action': 'NewAction'
                },
                {
                    'title': _('Save'),
                    'shortcut': 'Ctrl+S',
                    'icon': config.icon_dir('save.svg'),
                    'action': 'SaveAction'
                },
                {
                    'title': _('Open'),
                    'shortcut': 'Ctrl+O',
                    'icon': config.icon_dir('folder.svg'),
                    'action': 'OpenAction'
                },
                {
                    'title': _('Open Recent'),
                    'shortcut': 'Ctrl+Shift+O',
                    'id': 'open_recent',
                    'actions': []
                },
                {
                    'title': _('Save As'),
                    'shortcut': 'Ctrl+Shift+S',
                    'icon': config.icon_dir('save.svg'),
                    'action': 'SaveAsAction'
                },
                {
                    'type': 'separator',
                },
                {
                    'title': _('Settings'),
                    'shortcut': 'Ctrl+Alt+S',
                    'icon': config.icon_dir('settings.svg'),
                    'id': 'settings_action',
                    'action': 'SettingsAction'
                },
                {
                    'title': _('Event Settings'),
                    'icon': config.icon_dir('form.svg'),
                    'action': 'EventSettingsAction'
                },
                {
                    'type': 'separator',
                },
                {
                    'title': _('Import'),
                    'actions': [
                        {
                            'title': _('Import from SportOrg file'),
                            'action': 'ImportSportOrgAction'
                        },
                        {
                            'title': _('CSV Winorient'),
                            'icon': config.icon_dir('csv.svg'),
                            'action': 'CSVWinorientImportAction'
                        },
                        {
                            'title': _('WDB Winorient'),
                            'action': 'WDBWinorientImportAction'
                        },
                        {
                            'title': _('Orgeo CSV'),
                            'action': 'CSVOrgeoImportAction'
                        },
                        {
                            'title': _('Ocad txt v8'),
                            'action': 'OcadTXTv8ImportAction'
                        },
                        {
                            'title': _('CP coordinates'),
                            'action': 'CpCoordinatesImportAction'
                        },
                        {
                            'title': _('IOF xml'),
                            'action': 'IOFEntryListImportAction'
                        },
                    ]
                },
                {
                    'title': _('Export'),
                    'actions': [
                        {
                            'title': _('WDB Winorient'),
                            'action': 'WDBWinorientExportAction'
                        },
                        # {
                        #     'title': 'IOF xml',
                        #     'actions': [
                        #         {
                        #             'title': _('ResultList'),
                        #             'action': 'IOFResultListExportAction'
                        #         }
                        #     ]
                        # },
                    ]
                }
            ]
        },
        {
            'title': _('Edit'),
            'actions': [
                {
                    'title': _('Add object'),
                    'tabs': list(range(6)),
                    'shortcut': ['insert', 'i'],
                    'icon': config.icon_dir('add.svg'),
                    'action': 'AddObjectAction'
                },
                {
                    'title': _('Delete'),
                    'shortcut': 'Del',
                    'tabs': list(range(6)),
                    'icon': config.icon_dir('delete.svg'),
                    'action': 'DeleteAction'
                },
                {
                    'title': _('Copy'),
                    'shortcut': 'Ctrl+C',
                    'tabs': list(range(6)),
                    'action': 'CopyAction'
                },
                {
                    'title': _('Duplicate'),
                    'shortcut': 'Ctrl+D',
                    'tabs': list(range(6)),
                    'action': 'DuplicateAction'
                },
                {
                    'title': _('Text exchange'),
                    'action': 'TextExchangeAction'
                },
                {
                    'title': _('Mass edit'),
                    'tabs': [0],
                    'action': 'MassEditAction'
                }
            ]
        },
        {
            'title': _('View'),
            'actions': [
                {
                    'title': _('Refresh'),
                    'icon': config.icon_dir('refresh.svg'),
                    'shortcut': 'F5',
                    'action': 'RefreshAction'
                },
                {
                    'title': _('Filter'),
                    'shortcut': 'F2',
                    'tabs': [0, 1],
                    'icon': config.icon_dir('filter.svg'),
                    'action': 'FilterAction'
                },
                {
                    'title': _('Search'),
                    'shortcut': 'Ctrl+F',
                    'tabs': list(range(6)),
                    'icon': config.icon_dir('search.svg'),
                    'action': 'SearchAction'
                },
                {
                    'type': 'separator',
                },
                {
                    'title': _('Start Preparation'),
                    'shortcut': 'Ctrl+1',
                    'action': 'ToStartPreparationAction'
                },
                {
                    'title': _('Race Results'),
                    'shortcut': 'Ctrl+2',
                    'action': 'ToRaceResultsAction'
                },
                {
                    'title': _('Groups'),
                    'shortcut': 'Ctrl+3',
                    'action': 'ToGroupsAction'
                },
                {
                    'title': _('Courses'),
                    'shortcut': 'Ctrl+4',
                    'action': 'ToCoursesAction'
                },
                {
                    'title': _('Teams'),
                    'shortcut': 'Ctrl+5',
                    'action': 'ToTeamsAction'
                },
                {
                    'title': _('Controls'),
                    'shortcut': 'Ctrl+6',
                    'action': 'ToControlPointsAction'
                },
                {
                    'title': _('Log'),
                    'shortcut': 'Ctrl+7',
                    'action': 'ToLogAction'
                }
            ]
        },
        {
            'title': _('Start Preparation'),
            'actions': [
                {
                    'title': _('Start Preparation'),
                    'action': 'StartPreparationAction'
                },
                {
                    'title': _('Guess courses'),
                    'action': 'GuessCoursesAction'
                },
                {
                    'title': _('Guess corridors'),
                    'action': 'GuessCorridorsAction'
                },
                {
                    'title': _('Relay number assign mode'),
                    'tabs': [0],
                    'action': 'RelayNumberAction'
                },
                {
                    'title': _('Start time change'),
                    'action': 'StartTimeChangeAction'
                },
                {
                    'title': _('Handicap start time'),
                    'action': 'StartHandicapAction'
                },
                {
                    'title': _('Clone relay legs'),
                    'action': 'RelayCloneAction'
                },
                {
                    'title': _('Replace bib with card number'),
                    'action': 'CopyBibToCardNumber'
                },
                {
                    'title': _('Replace card number with bib'),
                    'action': 'CopyCardNumberToBib'
                },
                {
                    'title': _('Split teams'),
                    'action': 'SplitTeamsAction'
                },
                {
                    'title': _('Update subgroups'),
                    'action': 'UpdateSubroups'
                },
                {
                    'title': _('Merge groups'),
                    'tabs': [2],
                    'action': 'MergeGroupsAction'
                }
            ]
        },
        {
            'title': _('Race'),
            'actions': [
                {
                    'title': _('Manual finish'),
                    'shortcut': 'F3',
                    'icon': config.icon_dir('flag.svg'),
                    'action': 'ManualFinishAction'
                },
                {
                    'title': _('Add SPORTident result'),
                    'action': 'AddSPORTidentResultAction',
                    'shortcut': 'Ctrl+I',

                },
            ]
        },
        {
            'title': _('Results'),
            'actions': [
                {
                    'title': _('Create report'),
                    'shortcut': 'Ctrl+P',
                    'action': 'CreateReportAction'
                },
                {
                    'title': _('Split printout'),
                    'shortcut': 'Ctrl+L',
                    'action': 'SplitPrintoutAction'
                },
                {
                    'type': 'separator',
                },
                {
                    'title': _('Rechecking'),
                    'shortcut': 'Ctrl+R',
                    'action': 'RecheckingAction'
                },
                {
                    'title': _('Find group by punches'),
                    'tabs': [1],
                    'action': 'GroupFinderAction'
                },
                {
                    'title': _('Penalty calculation'),
                    'action': 'PenaltyCalculationAction'
                },
                {
                    'title': _('Penalty removing'),
                    'action': 'PenaltyRemovingAction'
                },
                {
                    'title': _('Change status'),
                    'shortcut': 'F4',
                    'tabs': [1],
                    'action': 'ChangeStatusAction'
                },
                {
                    'title': _('Set DNS numbers'),
                    'action': 'SetDNSNumbersAction'
                },
                {
                    'title': _('Delete CP'),
                    'action': 'CPDeleteAction'
                },
                {
                    'title': _('Assign result by bib'),
                    'action': 'AssignResultByBibAction'
                },
                {
                    'title': _('Assign result by card number'),
                    'action': 'AssignResultByCardNumberAction'
                },
            ]
        },
        {
            'title': _('Service'),
            'actions': [
                {
                    'title': _('on/off SPORTident readout'),
                    'icon': config.icon_dir('sportident.png'),
                    'shortcut': 'F8',
                    'action': 'SPORTidentReadoutAction'
                },
                {
                    'title': _('on/off Sportiduino readout'),
                    'icon': config.icon_dir('sportiduino.png'),
                    'shortcut': 'F9',
                    'action': 'SportiduinoReadoutAction'
                },
                {
                    'title': _('on/off SFR readout'),
                    'icon': config.icon_dir('sfr.png'),
                    'shortcut': 'F10',
                    'action': 'SFRReadoutAction'
                },
                {
                    'title': _('Teamwork'),
                    'icon': config.icon_dir('network.svg'),
                    'actions': [
                        {
                            'title': _('Send selected'),
                            'shortcut': 'Ctrl+Shift+K',
                            'tabs': list(range(5)),
                            'action': 'TeamworkSendAction'
                        },
                        {
                            'type': 'separator',
                        },
                        {
                            'title': _('On/Off'),
                            'action': 'TeamworkEnableAction'
                        }
                    ]
                },
                {
                    'title': _('Telegram'),
                    'actions': [
                        {
                            'title': _('Send results'),
                            'tabs': [1],
                            'action': 'TelegramSendAction'
                        },
                    ]
                },
                {
                    'title': _('Online'),
                    'actions': [
                        {
                            'title': _('Send selected'),
                            'shortcut': 'Ctrl+K',
                            'tabs': [0, 1, 2, 3, 4],
                            'action': 'OnlineSendAction',
                        },
                    ],
                },
            ]
        },
        {
            'title': _('Options'),
            'actions': [
                {
                    'title': _('Timekeeping settings'),
                    'icon': config.icon_dir('stopwatch.svg'),
                    'action': 'TimekeepingSettingsAction'
                },
                {
                    'title': _('Teamwork'),
                    'icon': config.icon_dir('network.svg'),
                    'action': 'TeamworkSettingsAction'
                },
                {
                    'title': _('Printer settings'),
                    'icon': config.icon_dir('printer.svg'),
                    'action': 'PrinterSettingsAction'
                },
                {
                    'title': _('Live'),
                    'icon': config.icon_dir('live.svg'),
                    'action': 'LiveSettingsAction'
                },
                {
                    'title': _('Telegram'),
                    'action': 'TelegramSettingsAction'
                },
                {
                    'title': _('Rent cards'),
                    'action': 'RentCardsAction'
                },
            ]
        },
        {
            'title': _('Help'),
            'actions': [
                {
                    'title': _('Help'),
                    'shortcut': 'F1',
                    'action': 'HelpAction'
                },

                {
                    'title': _('About'),
                    'action': 'AboutAction'
                },
                {
                    'title': _('Check updates'),
                    'action': 'CheckUpdatesAction'
                },
            ]
        },
    ]
