# DKIM record lookup

Query DNS TXT records at selected `selector._domainkey.domain` names for a list of domains, then export the results to Excel. Useful when you have a domain inventory and a known set of mail-provider selectors.

## Setup

Requires Python 3.11 or later and access to your configured DNS resolver.

```bash
git clone https://github.com/Hellfire4959/DKIM.git
cd DKIM
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Use

Create an Excel workbook whose first sheet has a column named **Domain**:

| Domain |
| --- |
| example.org |
| example.net |

```bash
python scripts/dkim_lookup.py domains.xlsx output/dkim-results.xlsx
python scripts/dkim_lookup.py domains.xlsx output/dkim-results.xlsx --selectors selector1 selector2
```

`--selectors` replaces the default selector list. Obtain the actual selectors from the domain's mail configuration or signed-message headers when possible. Each DNS query has a five-second lifetime in the CLI.

## Results and interpretation

| Column | Meaning |
| --- | --- |
| `Name` | Input domain |
| `DkimRecord` | JSON array containing each queried selector and its returned TXT value |
| `DkimSelector` | Selectors that returned TXT records |
| `DKIMAdvisory` | Found, not found among tested selectors, incomplete lookup, or blank input |
| `LookupErrors` | DNS failures such as timeout or unavailable nameservers |

TXT fragments belonging to one record are joined before export. A negative result covers only the tested selectors. The utility retrieves TXT values; it does not validate DKIM key syntax, verify a message signature, or establish that a domain has no other selector. Review `LookupErrors` even when another selector returned a record.

The output path is created if needed; an existing output workbook is replaced. Input and output must be different files.

## Files and development

- [scripts/dkim_lookup.py](scripts/dkim_lookup.py) — lookup and workbook CLI; replaces the original extensionless `Python script`.
- [requirements.txt](requirements.txt) — pandas, openpyxl and dnspython.
- [tests/](tests/) — mocked DNS and workbook tests, including split TXT records and lookup failures.

```bash
python -m unittest discover -s tests -v
```

Tests do not send DNS queries. Include representative selector responses and expected output when proposing a change.
