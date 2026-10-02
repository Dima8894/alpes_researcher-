import importlib.util
from pathlib import Path
import re
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('builder',ROOT/'scripts/build_chatgpt_pack.py')
b=importlib.util.module_from_spec(spec); spec.loader.exec_module(b)


class DistributionTests(unittest.TestCase):
    def test_exporter_in_sync(self):
        self.assertEqual((ROOT/'chatgpt/04_EXPORTER.txt').read_text(),b.generated())

    def test_instructions_compact(self):
        content=(ROOT/'chatgpt/00_PROJECT_INSTRUCTIONS.txt').read_text()
        self.assertLess(len(content),8000)
        for filename in re.findall(r'0[1-4]_[A-Z]+\.txt',content):
            self.assertTrue((ROOT/'chatgpt'/filename).exists())

    def test_pack_is_allowlisted(self):
        with zipfile.ZipFile(ROOT/'dist/ALPES-ChatGPT-Starter.zip') as archive:
            expected={'START_HERE.txt','LICENSE','ATTRIBUTION.md'} | {f'chatgpt/{p.name}' for p in (ROOT/'chatgpt').glob('*.txt')}
            self.assertEqual(set(archive.namelist()),expected)
            for name in archive.namelist():
                self.assertNotIn('private/',name)
                self.assertNotIn('.env',name)

    def test_no_previous_research_or_local_paths(self):
        # Reject local usernames in paths and credential-shaped tokens.
        pattern=re.compile(r'/Users/[^/\s]+/|/home/[^/\s]+/|gh[pousr]_[A-Za-z0-9]{20}',re.I)
        for folder in ['chatgpt','docs','examples']:
            for path in (ROOT/folder).glob('*'):
                if path.is_file(): self.assertIsNone(pattern.search(path.read_text()), str(path))


if __name__ == '__main__': unittest.main()
