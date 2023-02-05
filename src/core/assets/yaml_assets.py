from typing import TextIO, Any

import yaml
from .file_assets import FileAssets


def yaml_asset_loader(file: TextIO):
    return yaml.safe_load(file)


def yaml_asset_dumper(file: TextIO, value: Any):
    yaml.dump(value, file, allow_unicode=True)


def yaml_assets(assets: FileAssets):
    assets.loader(yaml_asset_loader)
    assets.dumper(yaml_asset_dumper)
    return assets
