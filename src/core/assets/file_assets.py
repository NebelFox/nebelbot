from __future__ import annotations

import os
from typing import Any, Iterable, Tuple, TextIO, Callable, Dict, Optional, \
    Literal, Union, NewType

from core.assets.assets import Assets


class FileAssets(Assets):
    _loader_function_suffix = '_asset_loader'

    LoaderType = NewType('Loader', Callable[[TextIO], Any])
    DumperType = NewType('Dumper', Callable[[TextIO, Any], None])

    Loaders = Dict[str, LoaderType]
    Dumpers = Dict[str, DumperType]

    def __init__(self,
                 base_dir: str,
                 loaders: Optional[Loaders] = None,
                 loader_function_suffix: str = '_asset_loader',
                 dumpers: Optional[Dumpers] = None,
                 dumper_function_suffix: str = '_asset_dumper'):
        self._base_dir = base_dir
        self._loader_function_suffix = loader_function_suffix
        self._loaders = dict(loaders or ())
        self._dumper_function_suffix = dumper_function_suffix
        self._dumpers = dict(dumpers or ())

    def get(self, key: str) -> Any:
        file, ext = self._open(key, 'loader')
        with file:
            return self._loaders[ext](file)

    def set(self, key: str, value: Any):
        file, ext = self._open(key, 'dumper')
        with file:
            self._dumpers[ext](file, value)

    def loader(self,
               loader: LoaderType) -> LoaderType:
        return self._decorator('loader',
                               loader,
                               self._loaders,
                               self._loader_function_suffix)

    def dumper(self, dumper: DumperType) -> DumperType:
        return self._decorator('dumper',
                               dumper,
                               self._dumpers,
                               self._dumper_function_suffix)

    @staticmethod
    def _decorator(kind: Literal['loader', 'dumper'],
                   f: Union[LoaderType, DumperType],
                   registry: Union[Loaders, Dumpers],
                   function_suffix: str) -> Callable:
        name = f.__name__
        if not name.endswith(function_suffix):
            kind_capital = f'{kind[0].upper()}{kind[1:]}'
            raise ValueError(f'{kind_capital} function name must be in format '
                             f'"{{extension}}{function_suffix}"')
        ext = name[:len(name) - len(function_suffix)]
        if ext in registry:
            raise ValueError(f'A {kind} for {ext} extension is already added')
        registry[ext] = f
        return f

    def _open(self, key: str, for_kind: str) -> Tuple[TextIO, str]:
        path, ext = self._find(key)
        if ext not in self._loaders:
            raise ValueError(f'No {for_kind} available for {ext} extension '
                             f'of asset with key {key} located at ({path})')
        mode = for_kind == 'loader' and 'r' or for_kind == 'dumper' and 'w'
        return open(path, mode=mode, encoding='utf-8'), ext

    def _find(self, key: str) -> Tuple[str, str]:
        matches = [m for m in self._list_files() if m[0] == key]
        if len(matches) < 1:
            raise FileNotFoundError(f'No asset found with key "{key}" '
                                    f'in {self._base_dir}')
        if len(matches) > 1:
            matches_str = ', '.join(f'"{m[0]}.{m[1]}"' for m in matches)
            raise LookupError(f'The key "{key}" is ambiguous. '
                              f'The assets-candidates are: {matches_str}')
        return self._from_base_dir(matches[0][0], matches[0][1]), matches[0][1]

    def _from_base_dir(self, path: str, extension: str):
        return f"{os.path.join(self._base_dir, path)}.{extension}"

    def _list_files(self) -> Iterable[Tuple[str, str]]:
        for path, names, files in os.walk(self._base_dir):
            if not names:
                yield from self._explode(path, files)

    @staticmethod
    def _explode(path: str,
                 files: Iterable[str]) -> Iterable[Tuple[str, str]]:
        for file in files:
            parts = file.rsplit('.', maxsplit=1)
            if len(parts) == 2:
                yield parts[0], parts[1]

    # def narrow(self, path: str) -> FileAssets:
    #     return FileAssets(
    #         base_dir=os.path.join(self._base_dir, path),
    #         loaders=self._loaders,
    #         loader_function_suffix=self._loader_function_suffix,
    #         dumpers=self._dumpers,
    #         dumper_function_suffix=self._dumper_function_suffix)

    def extend(self,
               other: FileAssets):
        if common_loaders := set(self._loaders).intersection(other._loaders):
            raise ValueError(f"FileAssets contain conflicting loaders: "
                             f"{', '.join(common_loaders)}")
        if common_dumpers := set(self._dumpers).intersection(other._dumpers):
            raise ValueError(f"FileAssets contain conflicting dumpers: "
                             f"{', '.join(common_dumpers)}")
        return FileAssets(
            base_dir=self._base_dir,
            loaders={**self._loaders, **other._loaders},
            loader_function_suffix=self._loader_function_suffix,
            dumpers={**self._dumpers, **other._dumpers},
            dumper_function_suffix=self._dumper_function_suffix)
