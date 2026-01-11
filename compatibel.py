import sys
import platform
import winreg

def get_python_version():
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

def get_windows_arch():
    arch = platform.machine()
    return "64-bit" if arch == "AMD64" else ("32-bit" if arch == "x86" else arch)

def get_vc_redist_version():
    """Retrieve Microsoft Visual C++ Redistributable version from registry."""
    for key_path in [
        r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64",
        r"SOFTWARE\WOW6432Node\Microsoft\VisualStudio\14.0\VC\Runtimes\x86",
        r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\X64",  # case-insensitive fallback
    ]:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                version, _ = winreg.QueryValueEx(key, "Version")
                installed, _ = winreg.QueryValueEx(key, "Installed")
                if installed == 1:
                    arch = "x64" if "x64" in key_path.lower() else "x86"
                    return f"{arch}: {version}"
        except FileNotFoundError:
            continue
        except Exception:
            continue
    return "Not found"

def main():
    print("=== System & Runtime Information ===")
    print(f"Python Version       : {get_python_version()}")
    print(f"Windows Architecture : {get_windows_arch()}")
    print(f"VC++ Redistributable : {get_vc_redist_version()}")
    print("=====================================")

    if get_vc_redist_version() == "Not found":
        print("\n⚠️  WARNING: Microsoft Visual C++ Redistributable not found!")
        print("   This may prevent .pyd modules from loading.")
        print("   Download: https://aka.ms/vs/17/release/vc_redist.x64.exe")

if __name__ == "__main__":
    main()