"""Owner: backend developer 1 (diagnosis engine)."""
from __future__ import annotations

import ctypes
import threading
from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np
import pandas as pd
from numpy.ctypeslib import ndpointer

from backend.diagnosis import build

OK, CAUTION, CRITICAL = 0, 1, 2
SUPPORTED_ENGINE_VERSION = 1


class EngineError(RuntimeError):
    pass


@dataclass(frozen=True)
class Finding:

    code: str
    severity: int
    zone: str


class _Engine:

    def __init__(self, library: ctypes.CDLL) -> None:
        self._lib = library
        self._declare_signatures()
        version = library.diag_engine_version()
        if version != SUPPORTED_ENGINE_VERSION:
            raise EngineError(
                f"library version {version} does not match the Python bridge "
                f"(expected {SUPPORTED_ENGINE_VERSION}); rebuild it with "
                "`python -m backend.diagnosis.build`"
            )
        self.metrics = self._names(library.diag_metric_count(), library.diag_metric_name)
        self.environments = self._names(library.diag_environment_count(),
                                        library.diag_environment_name)
        self.codes = self._names(library.diag_code_count(), library.diag_code_name)
        zones = self._names(library.diag_code_count(), library.diag_code_zone)
        self.zone_of = dict(zip(self.codes, zones))

    def _declare_signatures(self) -> None:
        lib = self._lib
        vector = ndpointer(dtype=np.float64, ndim=1, flags="C_CONTIGUOUS")
        result = ndpointer(dtype=np.int32, ndim=1, flags="C_CONTIGUOUS")
        for counter in (lib.diag_engine_version, lib.diag_metric_count,
                        lib.diag_environment_count, lib.diag_code_count):
            counter.argtypes = []
            counter.restype = ctypes.c_int
        for namer in (lib.diag_metric_name, lib.diag_environment_name,
                      lib.diag_code_name, lib.diag_code_zone):
            namer.argtypes = [ctypes.c_int]
            namer.restype = ctypes.c_char_p
        lib.diag_evaluate.argtypes = [vector, vector, ctypes.c_int, ctypes.c_int,
                                      ctypes.c_int, result, result, ctypes.c_int]
        lib.diag_evaluate.restype = ctypes.c_int

    @staticmethod
    def _names(count: int, getter) -> tuple[str, ...]:
        names = []
        for index in range(count):
            raw = getter(index)
            if not raw:
                raise EngineError(f"the library has no name for item {index}; rebuild it")
            names.append(raw.decode("ascii"))
        return tuple(names)

    def vector(self, values: Mapping[str, Any]) -> np.ndarray:
        series = pd.Series(dict(values), dtype=object).reindex(self.metrics)
        return np.ascontiguousarray(pd.to_numeric(series, errors="coerce"), dtype=np.float64)

    def evaluate(self, current: Mapping[str, Any], baseline: Mapping[str, Any],
                 environment: str, flight_day: int) -> list[Finding]:
        if environment not in self.environments:
            raise ValueError(f"unknown environment: {environment!r}")
        codes = np.zeros(len(self.codes), dtype=np.int32)
        severities = np.zeros(len(self.codes), dtype=np.int32)
        count = self._lib.diag_evaluate(
            self.vector(current), self.vector(baseline), len(self.metrics),
            self.environments.index(environment), int(flight_day),
            codes, severities, len(codes),
        )
        if count < 0:
            raise EngineError(f"diag_evaluate failed with code {count}")
        found = [
            Finding(self.codes[code], int(severity), self.zone_of[self.codes[code]])
            for code, severity in zip(codes[:count], severities[:count])
        ]
        return sorted(found, key=lambda finding: -finding.severity)


_engine: _Engine | None = None
_lock = threading.Lock()


def _load() -> _Engine:
    global _engine
    with _lock:
        if _engine is None:
            try:
                path = build.ensure_built()
            except build.BuildError as error:
                raise EngineError(str(error)) from error
            try:
                library = ctypes.CDLL(str(path))
            except OSError as error:
                raise EngineError(
                    f"cannot load {path.name}: {error}. If it was built for another "
                    "processor type than your Python (32/64-bit), rebuild it with a "
                    "matching compiler: `python -m backend.diagnosis.build`"
                ) from error
            _engine = _Engine(library)
        return _engine


def is_available() -> bool:
    try:
        _load()
    except EngineError:
        return False
    return True


def metric_order() -> tuple[str, ...]:
    return _load().metrics


def environments() -> tuple[str, ...]:
    return _load().environments


def codes() -> tuple[str, ...]:
    return _load().codes


def zone_of(code: str) -> str:
    return _load().zone_of[code]


def zones() -> tuple[str, ...]:
    return tuple(dict.fromkeys(_load().zone_of.values()))


def evaluate(current: Mapping[str, Any], baseline: Mapping[str, Any],
             environment: str, flight_day: int) -> list[Finding]:
    return _load().evaluate(current, baseline, environment, flight_day)
