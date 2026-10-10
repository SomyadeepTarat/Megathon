"""Extract selected kg CO2e/kWh rows from the corrected official DESNZ flat XLSX."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

SOURCE = 'https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026'
DOWNLOAD = 'https://assets.publishing.service.gov.uk/media/6a6c9748862aaf18d9c62ac9/ghg-conversion-factors-2026-flat-format-revised.xlsx'
ROWS = {'7_400_4000_5_1': ('electricity', 'Scope 2 location-based UK generation; excludes transmission/distribution and well-to-tank emissions'),
        '1_100_1004_6_1': ('gas', 'Scope 1 natural gas combustion; gross calorific value; excludes well-to-tank emissions')}


def extract(path):
    ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    result = []
    with ZipFile(path) as archive:
        strings = [''.join(si.itertext()) for si in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
        for name in archive.namelist():
            if not name.startswith('xl/worksheets/sheet') or not name.endswith('.xml'):
                continue
            for row in ET.fromstring(archive.read(name)).findall('.//s:row', ns):
                values = {}
                for cell in row.findall('s:c', ns):
                    value = cell.find('s:v', ns)
                    text = '' if value is None else value.text
                    if cell.get('t') == 's':
                        text = strings[int(text)]
                    values[''.join(c for c in cell.get('r') if c.isalpha())] = text
                if values.get('A') not in ROWS:
                    continue
                if values.get('I') != 'kg CO2e' or values.get('H') not in ('kWh', 'kWh (Gross CV)'):
                    raise ValueError('Unexpected source units')
                fuel, boundary = ROWS[values['A']]
                result.append(dict(fuel=fuel, kg_co2e_per_kwh=format(float(values['J']), '.8g'),
                    source=SOURCE, source_year=2026, accounting_boundary=boundary,
                    version='DESNZ-2026-flat-revised-2026-07-31', source_row_id=values['A'],
                    units='kg CO2e/kWh', source_sheet=name, source_excel_row=row.get('r')))
    if len(result) != 2 or {row['fuel'] for row in result} != {'electricity', 'gas'}:
        raise ValueError('Expected exactly two official factor rows')
    return sorted(result, key=lambda r: r['fuel'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path('Data/csv/emission_factors_2026.csv'))
    args = parser.parse_args()
    rows = extract(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader(); writer.writerows(rows)
    args.output.with_suffix('.provenance.json').write_text(json.dumps({
        'publication': SOURCE, 'download': DOWNLOAD, 'license': 'Open Government Licence v3.0; Crown copyright',
        'source_sha256': hashlib.sha256(args.input.read_bytes()).hexdigest(),
        'extracted_rows': rows,
        'limitations': 'Operational emissions only, not lifecycle retrofit emissions. 2026 factors applied as scenario assumptions; supplied meter year is 2025.'}, indent=2))
    print(json.dumps(rows, indent=2))

if __name__ == '__main__':
    main()
