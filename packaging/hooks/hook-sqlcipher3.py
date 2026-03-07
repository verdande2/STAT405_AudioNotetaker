# PyInstaller hook for sqlcipher3
#
# sqlcipher3 is a compiled C extension that wraps the SQLCipher library.
# PyInstaller cannot always detect its native binaries through static analysis,
# so this hook ensures everything is collected explicitly.

from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all("sqlcipher3")

# The dbapi2 submodule is imported dynamically in database.py via:
#   from sqlcipher3 import dbapi2 as sqlite
hiddenimports += ["sqlcipher3.dbapi2"]
