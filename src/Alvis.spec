# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['main.py'],
             pathex=['E:\\ALVIS\\ALVIS'],
             binaries=[],
             datas=[('assets', 'assets'),('alvis.kv','.'),('alvis.ini','.'),('Demo','Demo')],
             hiddenimports=['win32file', 'win32timezone'],
             hookspath=[],
             runtime_hooks=[],
             excludes=['matplotlib', 'tcl','Tkinter','_tkinter','cv2', 'tk', 'wx', 'notebook', 'IPython', 'PyQt5','botocore','Crypto','psutil','scipy'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='ALVIS',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False , icon='assets/images/kivy-icon-512.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='ALVIS')
