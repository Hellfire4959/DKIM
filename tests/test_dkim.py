import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
import dns.exception
import dns.resolver
import pandas as pd

spec = importlib.util.spec_from_file_location('dkim', Path(__file__).parents[1] / 'scripts/dkim_lookup.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)

class DkimTests(unittest.TestCase):
    def test_joins_txt_fragments_and_keeps_each_selector(self):
        resolver = Mock(); resolver.resolve.return_value = [Mock(strings=(b'v=DKIM1; ', b'p=example'))]
        row = module.get_dkim_record('example.org', ['s1','s2'], resolver)
        self.assertEqual(row['DkimSelector'], 's1; s2')
        self.assertEqual([r['value'] for r in json.loads(row['DkimRecord'])], ['v=DKIM1; p=example'] * 2)

    def test_absent_selector_does_not_claim_domain_has_no_dkim(self):
        resolver = Mock(); resolver.resolve.side_effect = dns.resolver.NXDOMAIN()
        row = module.get_dkim_record('example.org', ['not-a-selector'], resolver)
        self.assertEqual(row['DKIMAdvisory'], 'No TXT record found for tested selectors')

    def test_dns_timeout_is_not_reported_as_absent_record(self):
        resolver = Mock(); resolver.resolve.side_effect = dns.exception.Timeout()
        row = module.get_dkim_record('example.org', ['s1'], resolver)
        self.assertIn('incomplete', row['DKIMAdvisory']); self.assertIn('Timeout', row['LookupErrors'])

    def test_workbook_preserves_blank_rows_without_queries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); src = root / 'input.xlsx'; dst = root / 'output.xlsx'
            pd.DataFrame({'Domain':['example.org','','example.net']}).to_excel(src,index=False)
            resolver = Mock(); resolver.resolve.side_effect = dns.resolver.NoAnswer()
            self.assertEqual(module.audit(src,dst,['s1'],resolver), 3)
            result = pd.read_excel(dst,keep_default_na=False)
            self.assertEqual(result.loc[1,'DKIMAdvisory'], 'Blank domain')
            self.assertEqual(resolver.resolve.call_count, 2)

if __name__ == '__main__': unittest.main()
