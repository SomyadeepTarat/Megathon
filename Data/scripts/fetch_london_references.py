"""Download small official reference tables, never household/sales bulk records."""
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
URLS = {
    'hpi_property_type.csv': 'https://publicdata.landregistry.gov.uk/market-trend-data/house-price-index-data/Average-prices-Property-Type-2026-07.csv',
    'hpi_borough.csv': 'https://publicdata.landregistry.gov.uk/market-trend-data/house-price-index-data/England-annual-price-change-by-London-Borough-2026-07.csv',
    'epc_existing.ods': 'https://assets.publishing.service.gov.uk/media/6a69c5e816bc92f51e1a42d7/EB1-_Existing_Domestic_Properties.ods',
    'need_headline.xlsx': 'https://assets.publishing.service.gov.uk/media/6a2827843b15d05a7ce31fa7/Consumption_headline_EW_2024.xlsx',
}


def main():
    output = ROOT / 'generated/london_public_references'
    output.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, url in URLS.items():
        request = Request(url, headers={'User-Agent': 'Kew-hackathon-reference-audit/1.0'})
        with urlopen(request, timeout=45) as response:
            data = response.read(20_000_001)
        if len(data) > 20_000_000:
            raise ValueError('Reference exceeds small-download limit')
        (output / name).write_bytes(data)
        manifest[name] = {'url': url, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data), 'retrieved': '2026-10-11'}
        print(name, len(data), 'bytes')
    (output / 'downloads.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
