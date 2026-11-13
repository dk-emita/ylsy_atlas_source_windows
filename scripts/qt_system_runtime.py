"""Load Windows ICU before Qt so an unrelated bundled ICU cannot shadow it."""
import ctypes
import os


if os.name == 'nt':
    # Qt's Windows wheel imports unversioned ICU symbols such as ucnv_open.
    # A dependency scan can also collect an ICU DLL exporting suffixed (_78)
    # symbols. Loading that DLL first prevents QtCore from loading at all.
    # Load the OS implementation by absolute path and retain its handle for
    # the process lifetime; no system files or search paths are modified.
    _system_dir = ctypes.create_unicode_buffer(32768)
    _kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    _kernel32.GetSystemDirectoryW.argtypes = (ctypes.c_wchar_p, ctypes.c_uint)
    _kernel32.GetSystemDirectoryW.restype = ctypes.c_uint
    if not _kernel32.GetSystemDirectoryW(_system_dir, len(_system_dir)):
        raise ctypes.WinError(ctypes.get_last_error())
    _windows_icu = ctypes.WinDLL(
        os.path.join(_system_dir.value, 'icuuc.dll'), winmode=0x800
    )
    getattr(_windows_icu, 'ucnv_open')
