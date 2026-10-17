"""Combine the verified v25 source and Windows EXE into a complete 7z download."""
from pathlib import Path
import hashlib
import json
import shutil
import tempfile
import zipfile

import py7zr

ROOT = Path(__file__).resolve().parents[1]
EXE_SHA256 = '0aa1cbbe123be3c59f4db2d68c5471aef382e0e618ce258766b0c0b574910675'
SOURCE_SHA256 = '787ba46a738a807caadcafc23f3b7b4690a4d2ef465015c907496244c448f2c4'
BUILD_RUN = 'https://github.com/matglow2-pixel/test/actions/runs/39059794211'


def main():
    source = ROOT / 'LoongLens-WindowsBuild-v25.zip'
    binary = ROOT / 'download/LoongLens.exe'
    assert hashlib.sha256(source.read_bytes()).hexdigest() == SOURCE_SHA256, 'Wrong source package'
    assert hashlib.sha256(binary.read_bytes()).hexdigest() == EXE_SHA256, 'Wrong Windows EXE'
    out = ROOT / 'dist/LoongLens-v25-Full.7z'
    out.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='loonglens-full-') as temporary:
        folder = Path(temporary)
        with zipfile.ZipFile(source) as archive:
            assert archive.testzip() is None
            for entry in archive.infolist():
                assert (folder / entry.filename).resolve().is_relative_to(folder.resolve())
            archive.extractall(folder)
        app = folder / 'LoongLens'
        shutil.copy2(binary, app / 'LoongLens.exe')
        reports = app / 'windows-validation'
        reports.mkdir()
        for mode in ('self-check', 'gui-check', 'input-check'):
            report = ROOT / 'validation' / f'{mode}.json'
            assert json.loads(report.read_text('utf-8-sig'))['passed'] is True
            shutil.copy2(report, reports / report.name)
        shutil.copy2(ROOT / 'validation/tests-result.txt', reports / 'tests-result.txt')
        info = {'version': 'v25 ADB test build',
                'source_commit': '378c41bb8be3b89b366b6f7b6503c1d9902bab07',
                'windows_build_run': BUILD_RUN, 'exe_sha256': EXE_SHA256,
                'tests': {'passed': 372, 'skipped': 3},
                'live_bluestacks_validation': 'Pending on target PC'}
        (app / 'BUILD-INFO.json').write_text(json.dumps(info, indent=2) + '\n', encoding='utf-8')
        (app / 'START-HERE-v25.txt').write_text(
            'Loong Lens v25 - complete Windows folder\n\n'
            'Close the old app. Extract the entire LoongLens folder and run LoongLens.exe.\n'
            'Source, models, images, icons, launchers, tests and tools are included.\n\n'
            'For mouse-free Gem Sniping, enable BlueStacks Settings > Advanced > Android Debug Bridge.\n'
            'In Loong Lens Sniping settings choose ADB and enter 127.0.0.1:5555.\n'
            'Use Pick game area, Test connection / preview, and calibrate the map buttons. Save settings.\n'
            'Read README.md for details. First test a short Snipe pass on your PC.\n'
            'Keep the game active inside Android; minimized rendering remains unverified.\n'
            'Settings/history remain in %LOCALAPPDATA%\\LoongLens; do not delete that folder.\n\n'
            'Windows CI passed 372 tests, skipped 3, and passed frozen resource/GUI/input/icon checks.\n'
            'Live BlueStacks input, swipes and capture latency still need testing on your PC.\n',
            encoding='utf-8')
        manifest = {p.relative_to(app).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted(app.rglob('*')) if p.is_file()}
        (app / 'PACKAGE-SHA256.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
        with py7zr.SevenZipFile(out, 'w', filters=[{'id': py7zr.FILTER_LZMA2, 'preset': 6}]) as archive:
            archive.writeall(app, 'LoongLens')
        with py7zr.SevenZipFile(out) as archive:
            archive.extractall(folder / 'verified')
        for name, digest in manifest.items():
            assert hashlib.sha256((folder / 'verified/LoongLens' / name).read_bytes()).hexdigest() == digest, name
        print(f'Verified {len(manifest) + 1} files including the Windows EXE and full source/resources.')
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    out.with_suffix('.7z.sha256').write_text(f'{digest}  {out.name}\n', encoding='ascii')
    print(f'Complete package: {out.name} ({out.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
