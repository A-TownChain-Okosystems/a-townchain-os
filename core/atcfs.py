"""
ATCFS Compat-Shim (v3.2.1)
Dieses Modul wurde nach modules/kernel/atcfs/atcfs.py verschoben.
Bitte Imports aktualisieren auf:  from modules.kernel.atcfs.atcfs import ATCFileSystem, ATCFS
"""
import warnings
warnings.warn(
    "core.atcfs ist deprecated seit v3.2.1. "
    "Bitte nutze: from modules.kernel.atcfs.atcfs import ATCFileSystem, ATCFS",
    DeprecationWarning, stacklevel=2,
)
from modules.kernel.atcfs.atcfs import (  # noqa: F401
    ATCFileSystem, ATCFSNode, ATCObject, ATCFS,
    FilePermission, get_vfs, get_atcfs,
)
# Legacy-Alias
ATCFileSystem = ATCFileSystem  # noqa
