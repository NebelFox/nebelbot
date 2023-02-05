from typing import TextIO, List, Iterable

from .file_assets import FileAssets


def txt_asset_loader(file: TextIO) -> List[str]:
    """
    Read a file and return the lines without newline character

    :param file: an opened file to read from
    :return: the lines read
    """
    return file.read().strip().split('\n')


def txt_asset_dumper(file: TextIO, value: Iterable):
    """
    Write each item of <value> as a separate line to the <file>

    :param file: an opened file to write to
    :param value: an iterable to be written
    """
    file.write('\n'.join(str(x) for x in value))


def txt_assets(assets: FileAssets):
    """
    Extend the passed <assets> instance with *.txt dumper and loader

    :param assets: an instance of FileAssets to extend
    :return: the passed <assets> instance
    """
    assets.loader(txt_asset_loader)
    assets.dumper(txt_asset_dumper)
    return assets
