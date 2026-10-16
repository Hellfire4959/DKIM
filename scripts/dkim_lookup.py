"""Look up DKIM TXT records for selected selectors and export results to Excel."""
import argparse
import json
from pathlib import Path
import sys
import dns.exception
import dns.resolver
import pandas as pd

DEFAULT_SELECTORS = ['google', 'selector1', 'selector2', 'mxvault', 'mandrill',
    'sendgrid', 's1', 'pp', 'dkim', 'amazonses', 'key1', 'spf', 'yahoo',
    'sparkpost', 'zoho', 'authsmtp', 'dynect', 'socketlabs', 'turbosmtp',
    'vzrelay', 'emarsys', 'yandex', 'postmark', 'emarsys1', 'emarsys2', 'emarsys3']

def get_dkim_record(domain, selectors=None, resolver=None):
    resolver = resolver if resolver is not None else dns.resolver.Resolver()
    selectors = DEFAULT_SELECTORS if selectors is None else selectors
    ascii_domain = domain.strip().rstrip('.').encode('idna').decode('ascii')
    records, found_selectors, errors = [], [], []
    for selector in selectors:
        try:
            answers = resolver.resolve(f'{selector}._domainkey.{ascii_domain}', 'TXT')
            # One TXT record can be split into several character strings.
            for answer in answers:
                value = b''.join(answer.strings).decode('utf-8', errors='replace')
                records.append({'selector': selector, 'value': value})
            if answers: found_selectors.append(selector)
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            continue
        except dns.exception.DNSException as error:
            errors.append(f'{selector}: {type(error).__name__}')
    advisory = 'TXT record found for tested selector(s)' if records else (
        'Lookup incomplete; review errors' if errors else 'No TXT record found for tested selectors')
    return {'Name': domain, 'DkimRecord': json.dumps(records, ensure_ascii=False),
        'DkimSelector': '; '.join(found_selectors), 'DKIMAdvisory': advisory,
        'LookupErrors': '; '.join(errors)}

def audit(input_file, output_file, selectors=None, resolver=None):
    if Path(input_file).resolve() == Path(output_file).resolve():
        raise ValueError('Input and output paths must be different.')
    data = pd.read_excel(input_file, keep_default_na=False)
    if 'Domain' not in data.columns:
        raise ValueError('Input worksheet must have a Domain column.')
    rows = []
    for raw in data['Domain']:
        domain = str(raw).strip()
        if not domain:
            rows.append({'Name':'', 'DkimRecord':'[]', 'DkimSelector':'',
                'DKIMAdvisory':'Blank domain', 'LookupErrors':''})
            continue
        rows.append(get_dkim_record(domain, selectors, resolver))
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    columns = ['Name','DkimRecord','DkimSelector','DKIMAdvisory','LookupErrors']
    pd.DataFrame(rows, columns=columns).to_excel(output_file, index=False)
    return len(rows)

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input_file', type=Path, help='Excel workbook with a Domain column.')
    parser.add_argument('output_file', type=Path, help='Output .xlsx workbook.')
    parser.add_argument('--selectors', nargs='+', default=DEFAULT_SELECTORS,
                        help='Selectors to query; replaces the built-in list.')
    args = parser.parse_args(argv)
    if args.output_file.suffix.lower() != '.xlsx': parser.error('output_file must end in .xlsx')
    resolver = dns.resolver.Resolver(); resolver.lifetime = 5
    try: rows = audit(args.input_file, args.output_file, args.selectors, resolver)
    except (OSError, ValueError) as error:
        print(f'Error: {error}', file=sys.stderr); return 1
    print(f'Wrote {rows} rows to {args.output_file}'); return 0

if __name__ == '__main__': sys.exit(main())
