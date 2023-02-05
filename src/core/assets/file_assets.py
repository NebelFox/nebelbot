from __future__ import annotations

import os
from typing import Any, Iterable, Tuple, TextIO, Callable, Dict, Optional, \
    Literal, Union

from core.assets.assets import Assets


class FileAssets(Assets):
    """
    Assets that read and write files
    """
    _loader_function_suffix = '_asset_loader'

    LoaderType = Callable[[TextIO], Any]
    DumperType = Callable[[TextIO, Any], None]

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
        """
        Search for a file with name <key>,
        and return it's content loaded with the loader for the file extension.

        If there is no loader available for the file extension,
        an exception is raised.

        If there are multiple files with same name but different extension,
        an exception is raised.

        :param key: file name, without extension
        :return: the result of the matched loader execution on file content
        """
        file, ext = self._open(key, 'loader')
        with file:
            return self._loaders[ext](file)

    def set(self, key: str, value: Any):
        """
        Search for a file with name <key>,
        and overwrite it with the dumper for the file extension
        applied to the <value>

        :param key: file name to overwrite
        :param value: argument for dumper
        """
        file, ext = self._open(key, 'dumper')
        with file:
            self._dumpers[ext](file, value)

    def loader(self,
               loader: LoaderType) -> LoaderType:
        """
        Decorator for adding custom loader function.
        The file extension this loader is for is inferred
        from the passed function name by removing the <loader_function_suffix>
        from the end of it.

        :param loader: a function that reads from a file
        and deserializes its content
        """
        return self._decorator('loader',
                               loader,
                               self._loaders,
                               self._loader_function_suffix)

    def dumper(self, dumper: DumperType) -> DumperType:
        """
        Decorator for adding custom dumper function.
        The file extension this dumper is for is inferred
        from the passed function name by removing the <dumper_function_suffix>
        from the end of it.

        :param dumper: a function that serializes its argument <value>
        and writes it into passed file
        """
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
        """
        Combines this FileAssets instance with another instance,
        using loaders and dumpers from both.

        If both have a loader or dumper for the same extension,
        an exception is raised.

        The base_dir, loader and dumper function suffixes are taken
        from this instance, not from the <other>.

        :param other:
        :return:
        """
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
