"""Inspect/extract official reference tables using a read-only workbook reader."""
import csv
import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'generated/london_public_references'
NS = {'table': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
      'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0'}


def ods_tables(path):
    with zipfile.ZipFile(path) as archive:
        tree = ET.fromstring(archive.read('content.xml'))
    for table in tree.findall('.//table:table', NS):
        rows = []
        for row in table.findall('table:table-row', NS):
            values = []
            for cell in row:
                value = cell.get(f'{{{NS["office"]}}}value')
                value = value if value is not None else ''.join(cell.itertext()).strip()
                repeat = min(128, int(cell.get(f'{{{NS["table"]}}}number-columns-repeated', 1)))
                values.extend([value] * repeat)
            while values and values[-1] == '':
                values.pop()
            if values:
                rows.append(values)
        yield table.get(f'{{{NS["table"]}}}name'), rows


def prepare():
    import openpyxl
    with (RAW / 'hpi_property_type.csv').open(newline='', encoding='utf-8-sig') as stream:
        prices = [r for r in csv.DictReader(stream) if r['Date'] == '2026-07-01' and (r['Region_Name'] == 'London' or r['Area_Code'].startswith('E09'))]
    mapping = {'Detached': 'Detached_Average_Price', 'Semi-detached': 'Semi_Detached_Average_Price',
               'Terraced': 'Terraced_Average_Price', 'Flat': 'Flat_Average_Price'}
    london = next(r for r in prices if r['Region_Name'] == 'London')
    result = {'retrieved': '2026-10-11', 'raw_sources': json.loads((RAW / 'downloads.json').read_text()),
              'price_period': '2026-07',
              'london_type_prices_gbp': {k: float(london[v]) for k, v in mapping.items()},
              'borough_type_prices_gbp': {r['Region_Name']: {k: float(r[v]) for k, v in mapping.items() if r[v] and float(r[v]) > 0}
                                          for r in prices if r['Area_Code'].startswith('E09')},
              'housing_mix_counts': {'Detached': 208078, 'Semi-detached': 636084, 'Terraced': 727673, 'Flat': 1847649},
              'age_bands': [[1850, 1918, .276], [1919, 1944, .223], [1945, 1964, .128],
                            [1965, 1980, .146], [1981, 1990, .029], [1991, 2002, .078], [2003, 2021, .120]],
              'post_2002_flat_share': .867,
              'housing_source': {'url': 'https://www.london.gov.uk/media/107179/download',
                                 'title': "London's Housing Stock, November 2024", 'pages': '10-12 (printed)',
                                 'mix_period': 'Census 2021', 'age_period': 'English Housing Survey 2021',
                                 'exclusions': '4,406 mobile/temporary households outside the existing type schema',
                                 'assumptions': 'Uniform build years inside bands; pre-1919 truncated at 1850. No stock extrapolation to 2026.'}}
    for name, rows in ods_tables(RAW / 'epc_existing.ods'):
        if name == 'EB1_by_Region':
            selected = [r for r in rows if r[0] == 'London' and r[1].startswith('2025/')]
            if len(selected) != 4:
                raise ValueError('Expected four London 2025 quarters')
            result['epc_existing_2025'] = {'sheet': name, 'quarters': [r[1] for r in selected],
                'certificate_count': sum(int(r[2]) for r in selected),
                'floor_area_total_m2': sum(float(r[3]) for r in selected),
                'rating_counts': {rating: sum(int(r[4+i]) for r in selected) for i, rating in enumerate('ABCDEFG')},
                'population': 'Existing-dwelling certificate lodgements, not unique homes or a stock-representative sample.'}
    workbook = openpyxl.load_workbook(RAW / 'need_headline.xlsx', read_only=True, data_only=True)
    for sheet in workbook:
        rows = list(sheet.values)
        if sheet.title in ('Table_15', 'Table_16'):
            r = next(r for r in rows if r[0] == 2024)
            if rows[6][7] != 'London' or rows[6][35] != 'London':
                raise ValueError('Unexpected NEED layout')
            fuel = 'gas' if sheet.title == 'Table_15' else 'electricity'
            result.setdefault('need_london_2024', {})[fuel] = {'sample_dwellings': r[7], 'mean_kwh': r[21],
                                                           'median_kwh': r[35], 'sheet': sheet.title, 'row': 27,
                                                           'columns': 'H sample, V mean, AJ median'}
    workbook.close()
    target = ROOT / 'manifests/london_reference_v1.json'
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print('Prepared', target, '; 33 boroughs, London EPC 2025 and NEED 2024 references')


if __name__ == '__main__':
    prepare()
