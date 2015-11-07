# -*- mode: python -*-

block_cipher = None


a = Analysis(['start.py'],
             pathex=['/Users/nchen/Projects/OSF-Offline'],
             binaries=None,
             datas=None,
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None,
             excludes=None,
             win_no_prefer_redirects=None,
             win_private_assemblies=None,
             cipher=block_cipher)
a.datas += [('circle_logo.ico','/Users/nchen/Projects/OSF-Offline/circle_logo.ico','DATA')]
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='OSF-Offline',
          debug=False,
          strip=None,
          upx=True,
          console=False , icon='/Users/nchen/Projects/OSF-Offline/circle_logo.ico')
app = BUNDLE(exe,
             name='OSF-Offline.app',
             icon='/Users/nchen/Projects/OSF-Offline/circle_logo.ico',
             bundle_identifier=None)
