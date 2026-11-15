from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = (HERE / "diagnosis.c", HERE / "diagnosis.h")

if sys.platform == "win32":
    LIBRARY_NAME = "diagnosis.dll"
elif sys.platform == "darwin":
    LIBRARY_NAME = "libdiagnosis.dylib"
else:
    LIBRARY_NAME = "libdiagnosis.so"


class BuildError(RuntimeError):
    pass


def library_path() -> Path:
    return HERE / LIBRARY_NAME


def needs_build() -> bool:
    library = library_path()
    if not library.exists():
        return True
    built = library.stat().st_mtime
    return any(source.exists() and source.stat().st_mtime > built for source in SOURCES)


def find_compiler() -> str | None:
    candidates = [os.environ.get("CC"), "gcc", "clang", "cc"]
    if sys.platform == "win32":
        candidates.append("cl")
    for candidate in candidates:
        if candidate and shutil.which(candidate):
            return shutil.which(candidate)
    return None


def _command(compiler: str, output: Path) -> list[str]:
    source = str(SOURCES[0])
    if Path(compiler).stem.lower() == "cl":
        return [compiler, "/nologo", "/O2", "/LD", source, f"/Fe:{output}"]
    command = [compiler, "-std=c99", "-O2", "-Wall", "-Wextra", "-shared"]
    if sys.platform == "win32":
        command.append("-static-libgcc")
    else:
        command.append("-fPIC")
    command += ["-o", str(output), source]
    if sys.platform != "win32":
        command.append("-lm")
    return command


def build() -> Path:
    compiler = find_compiler()
    if compiler is None:
        raise BuildError(
            "no C compiler found. Install gcc (on Windows: MinGW-w64, 64-bit) "
            "or set the CC environment variable, then run "
            "`python -m backend.diagnosis.build`."
        )
    library = library_path()
    with tempfile.TemporaryDirectory() as scratch:
        staged = Path(scratch) / LIBRARY_NAME
        result = subprocess.run(_command(compiler, staged), cwd=scratch,
                                capture_output=True, text=True)
        if result.returncode != 0 or not staged.exists():
            details = (result.stderr or result.stdout or "").strip()
            raise BuildError(f"{Path(compiler).name} failed:\n{details}")
        incoming = library.with_name(library.name + ".new")
        try:
            shutil.copyfile(staged, incoming)
            os.replace(incoming, library)
        except PermissionError:
            incoming.unlink(missing_ok=True)
            raise BuildError(
                f"cannot replace {library.name}: it is in use. Stop the app and build again."
            ) from None
    return library


def ensure_built() -> Path:
    return build() if needs_build() else library_path()


def main() -> int:
    try:
        library = build()
    except BuildError as error:
        print(f"Build failed: {error}", file=sys.stderr)
        return 1
    print(f"Built {library}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
