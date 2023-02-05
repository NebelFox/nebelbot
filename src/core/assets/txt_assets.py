from .file_assets import FileAssets


def txt_asset_loader(file):
    return file.read().strip().split('\n')


def txt_asset_dumper(file, value):
    file.write('\n'.join(str(x) for x in value))


def txt_assets(assets: FileAssets):
    assets.loader(txt_asset_loader)
    assets.dumper(txt_asset_dumper)
    return assets
