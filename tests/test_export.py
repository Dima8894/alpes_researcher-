import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('exporter', ROOT/'scripts/export_report.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT/'examples/demo_report.json').read_text())

    def test_valid_example(self):
        m.validate(self.data)

    def test_fact_requires_source(self):
        self.data['summary'][0]['kind'] = 'fact'
        with self.assertRaisesRegex(ValueError, 'источник'): m.validate(self.data)

    def test_unknown_reference(self):
        self.data['summary'][0]['sources'] = ['S99']
        with self.assertRaisesRegex(ValueError, 'неизвестный источник'): m.validate(self.data)

    def test_unverified_fact_rejected(self):
        self.data['summary'][0].update(kind='fact', sources=['S01'])
        with self.assertRaisesRegex(ValueError, 'непроверенный'): m.validate(self.data)

    def test_duplicate_source(self):
        self.data['sources'].append(copy.deepcopy(self.data['sources'][0]))
        with self.assertRaisesRegex(ValueError, 'Дублирующийся'): m.validate(self.data)

    def test_hypothesis_requires_alternative(self):
        self.data['sections'][2]['items'][0].pop('alternative')
        with self.assertRaises(ValueError): m.validate(self.data)

    def test_invalid_links(self):
        for url in ['javascript:alert(1)', 'file:///private/secret', 'https://user:pass@example.org', 'https://example.org/ a']:
            with self.subTest(url=url), self.assertRaises(ValueError): m.safe_url(url)

    def test_dates(self):
        self.data['date'] = '2026-02-30'
        with self.assertRaises(ValueError): m.validate(self.data)

    def test_file_material(self):
        self.data['sources'][0]['url'] = ''
        m.validate(self.data)

    def test_export_three_files_and_same_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)/'result'
            m.export(self.data, dest)
            self.assertEqual({p.name for p in dest.iterdir()}, {'REPORT.pdf', 'REPORT.docx', 'SOURCES.txt'})
            from pypdf import PdfReader
            reader = PdfReader(dest/'REPORT.pdf')
            pdftext = ''.join(page.extract_text() for page in reader.pages)
            with zipfile.ZipFile(dest/'REPORT.docx') as archive:
                xml = ET.fromstring(archive.read('word/document.xml'))
                doctext = ''.join(xml.itertext())
                self.assertIn('https://example.org/', archive.read('word/_rels/document.xml.rels').decode())
                core = archive.read('docProps/core.xml').decode()
                self.assertIn('Alpes Researcher', core)
            for kind, value in m.blocks(self.data):
                if kind != 'refs':
                    for rendered in (pdftext, doctext):
                        self.assertIn(''.join(value.split()), ''.join(rendered.split()))
            uris = [str(a.get_object().get('/A', {}).get('/URI','')) for p in reader.pages for a in p.get('/Annots', [])]
            self.assertIn('https://example.org/', uris)
            with self.assertRaisesRegex(ValueError, 'уже существует'): m.export(self.data, dest)

    def test_source_ledger_is_plain_text(self):
        self.data['title'] = '<script>alert("x")</script> & Кириллица'
        self.data['sources'][0]['note'] = '<img src=x onerror=alert(1)>'
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)/'result'; m.export(self.data, dest)
            ledger = (dest/'SOURCES.txt').read_text()
            self.assertTrue(ledger.startswith(self.data['title']))
            self.assertIn('https://example.org/', ledger)
            self.assertIn(self.data['sources'][0]['note'], ledger)
            self.assertNotIn('<!doctype html>', ledger)
            self.assertEqual(list(dest.glob('*.html')), [])

    def test_failed_validation_creates_nothing(self):
        self.data['summary'] = []
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)/'result'
            with self.assertRaises(ValueError): m.export(self.data, dest)
            self.assertFalse(dest.exists())


if __name__ == '__main__': unittest.main()
