import sys
import os
from cx_Freeze import setup, Executable
from sportorg import config

base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

include_files = [
    config.LOCALE_DIR,
    config.TEMPLATE_DIR,
    config.IMG_DIR,
    config.SOUND_DIR,
    config.STYLE_DIR, 
    config.base_dir('sportorg'),
    config.base_dir('docs'),
    config.base_dir('LICENSE'),
    config.base_dir('changelog.en.md'),
    config.base_dir('changelog.ru.md'),
    config.base_dir('configs'), 
]

includes = ['atexit', 'codecs']
excludes = ['Tkinter']

build_exe_options = {
    'includes': includes,
    'excludes': excludes,
    'packages': ['idna', 'requests', 'encodings', 'asyncio'],
    'include_files': include_files,
    'include_msvcr': True,
    'silent': 1
}

shortcut_table = [
    ("DesktopShortcut",        # Shortcut
     "DesktopFolder",          # Directory_
     config.NAME,              # Name
     "TARGETDIR",              # Component_
     "[TARGETDIR]SportOrgPlus.exe", # Target
     None,                     # Arguments
     None,                     # Description
     None,                     # Hotkey
     None,                     # Icon
     None,                     # IconIndex
     None,                     # ShowCmd
     'TARGETDIR'               # WkDir
     ),
    #("StartupShortcut",        # Shortcut
    # "StartupFolder",          # Directory_
    # config.NAME,              # Name
    # "TARGETDIR",              # Component_
    # "[TARGETDIR]SportOrgPlus.exe", # Target
    # None,                     # Arguments
    # None,                     # Description
    # None,                     # Hotkey
    # None,                     # Icon
    # None,                     # IconIndex
    # None,                     # ShowCmd
    # 'TARGETDIR'               # WkDir
    # ),
]

bdist_msi_options = {
    #'initial_target_dir': r'[ProgramFilesFolder]\%s' % config.NAME,
    'all_users': False,
    'data': {'Shortcut': shortcut_table}
}

options = {
    'build_exe': build_exe_options,
    'bdist_msi': bdist_msi_options
}

executables = [
    Executable(
        'SportOrgPlus.pyw',
        base=base,
        icon=config.icon_dir('sportorg.ico'),
        copyright='GNU GENERAL PUBLIC LICENSE {}'.format(config.NAME)
    )
]

version = os.getenv('VERSION', '') 
if not version:
    version = str(config.VERSION)

setup(
    name=config.NAME,
    version=version,
    description=config.NAME,
    options=options,
    executables=executables
)
