from typing import TextIO, Any

import yaml
from .file_assets import FileAssets


def yaml_asset_loader(file: TextIO) -> Any:
    """
    Parse the yaml from passed <file> into a Python object

    :param file: an opened file to read from
    :return: the parsed object
    """
    return yaml.safe_load(file)


def yaml_asset_dumper(file: TextIO, value: Any):
    """
    Serialize the <value> into yaml and write to <file>

    :param file: an opened file to write to
    :param value: a value to be serialized
    """
    yaml.dump(value, file, allow_unicode=True)


def yaml_assets(assets: FileAssets):
    """
    Extend the passed <assets> instance with *.yaml dumper and loader

    :param assets: an instance of FileAssets to extend
    :return: the passed <assets> instance
    """
    assets.loader(yaml_asset_loader)
    assets.dumper(yaml_asset_dumper)
    return assets
