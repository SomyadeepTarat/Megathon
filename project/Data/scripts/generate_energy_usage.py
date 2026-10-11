"""Generate complete synthetic calendar-year meter imports; Python standard library."""
import csv
import hashlib
import random
from collections import defaultdict
from pathlib import Path
from statistics import median

SEED = 42
YEAR = 2025
FIELDS = ['property_id', 'month', 'electricity_kwh', 'gas_kwh', 'reading_status', 'electricity_demand_kwh', 'solar_generation_kwh', 'solar_self_consumed_kwh', 'solar_export_kwh', 'space_heating_demand_kwh', 'hot_water_demand_kwh', 'physical_inputs_status', 'reading_source']
HEAT = [.17,.145,.12,.08,.04,.015,.005,.005,.035,.085,.13,.17]
APPLIANCES = [.095,.085,.085,.08,.08,.075,.075,.075,.08,.085,.09,.095]
SOLAR = [.025,.04,.075,.10,.125,.135,.135,.115,.09,.065,.035,.025]
CLIMATE = {'Greater London':.95,'South East':.97,'South West':.95,'East of England':1.0,'West Midlands':1.04,'East Midlands':1.05,'North West':1.08,'North East':1.12,'Yorkshire and The Humber':1.10,'Wales':1.06}
YIELD = {'Greater London':950,'South East':980,'South West':1000,'East of England':950,'West Midlands':900,'East Midlands':900,'North West':850,'North East':850,'Yorkshire and The Humber':870,'Wales':880}

def boolean(value):
    if str(value).lower() not in ('true','false'):
        raise ValueError(f'Invalid boolean: {value}')
    return str(value).lower() == 'true'

def normalize(values):
    total = sum(values)
    assert total > 0
    return [x/total for x in values]

def annual_components(p, behavior=1.0):
    area = float(p['floor_area_m2'])
    age = max(0,int(p['age'])-1)  # approximate age during the 2025 scenario
    bedrooms = int(p['bedrooms'])
    assert area > 0 and bedrooms >= 0
    occupants = min(5,max(1,bedrooms))  # assumed, not observed
    thermal = (area*65 * {'Poor':1.30,'Average':1.0,'Good':.75}[p['insulation']]
               * {'Single':1.15,'Double':1.0,'Triple':.90}[p['glazing']]
               * (1 + .0015*min(age,120))
               * {'Detached':1.10,'Semi-detached':.95,'Terraced':.85,'Flat':.70}[p['property_type']]
               * CLIMATE[p['region']]
               * (.94 if boolean(p['smart_controls']) else 1.0) * behavior)
    hot_water = (600+350*occupants)*behavior
    appliances = (800+500*occupants+1.0*area)*behavior
    generation = (min(5,max(2,area*.025))*YIELD[p['region']]) if boolean(p['solar']) else 0.0
    return thermal,hot_water,appliances,generation

def monthly_components(p, behavior=1.0, heat_share=None, appliance_share=None):
    thermal,hot_water,appliances,generation = annual_components(p,behavior)
    hs = normalize(heat_share or HEAT)
    es = normalize(appliance_share or APPLIANCES)
    ss = normalize(SOLAR)
    result=[]
    for m in range(12):
        heat=thermal*hs[m]; water=hot_water/12
        demand=appliances*es[m]
        if p['heating'] in ('Old gas boiler','Modern gas boiler'):
            efficiency=.72 if p['heating']=='Old gas boiler' else .90
            gas=(heat+water)/efficiency
        elif p['heating']=='Heat pump':
            gas=0.0; demand+=heat/3.0+water/2.5
        elif p['heating']=='Electric resistance':
            gas=0.0; demand+=heat+water
        else:
            raise ValueError(f'Unsupported heating system: {p["heating"]}')
        self_consumed=min(demand,.45*generation*ss[m])
        grid=max(0.0,demand-self_consumed)
        result.append({'grid':grid,'gas':gas,'demand':demand,'solar_self_consumed':self_consumed,'thermal':heat,'hot_water':water,'generation':generation*ss[m],'export':generation*ss[m]-self_consumed})
    return result

def generate(properties):
    rows=[]
    for p in sorted(properties,key=lambda x:x['property_id']):
        # Stable per-property seed: adding/reordering properties preserves existing readings.
        seed=int.from_bytes(hashlib.sha256(f'{SEED}:{p["property_id"]}'.encode()).digest()[:8],'big')
        rng=random.Random(seed)
        behavior=rng.uniform(.90,1.10)
        heat_share=[x*rng.uniform(.95,1.05) for x in HEAT]
        appliance_share=[x*rng.uniform(.95,1.05) for x in APPLIANCES]
        monthly=monthly_components(p,behavior,heat_share,appliance_share)
        for m,v in enumerate(monthly,1):
            rows.append(dict(zip(FIELDS,[p['property_id'],f'{YEAR}-{m:02d}',f'{v["grid"]:.2f}',f'{v["gas"]:.2f}','synthetic',f'{v["demand"]:.6f}',f'{v["generation"]:.6f}',f'{v["solar_self_consumed"]:.6f}',f'{v["export"]:.6f}',f'{v["thermal"]:.6f}',f'{v["hot_water"]:.6f}','synthetic_modelled','generate_energy_usage.py v1; no observed meter record'])))
    return rows

def validate(properties,rows):
    assert len({p['property_id'] for p in properties})==len(properties)
    assert len(rows)==12*len(properties)
    groups=defaultdict(list)
    for r in rows:
        assert list(r)==FIELDS and r['reading_status']=='synthetic'
        assert float(r['electricity_kwh'])>=0 and float(r['gas_kwh'])>=0
        groups[r['property_id']].append(r)
    assert set(groups)=={p['property_id'] for p in properties}
    assert len({(r['property_id'],r['month']) for r in rows})==len(rows)
    for p in properties:
        records=groups[p['property_id']]
        assert {r['month'] for r in records}=={f'{YEAR}-{m:02d}' for m in range(1,13)}
        if p['heating'] in ('Heat pump','Electric resistance'):
            assert all(float(r['gas_kwh'])==0 for r in records)
        else:
            assert all(float(r['gas_kwh'])>0 for r in records)
    # Controlled paired comparisons, rather than confounded sample correlations.
    base=dict(properties[0],floor_area_m2='100',solar='false',smart_controls='false',heating='Modern gas boiler',insulation='Average',glazing='Double')
    def totals(p):
        records=monthly_components(p)
        return sum(r['grid'] for r in records),sum(r['gas'] for r in records),sum(r['demand'] for r in records),sum(r['thermal'] for r in records)
    assert totals(dict(base,insulation='Poor'))[3]>totals(dict(base,insulation='Good'))[3]
    assert totals(dict(base,glazing='Single'))[3]>totals(dict(base,glazing='Triple'))[3]
    solar=totals(dict(base,solar='true')); no_solar=totals(base)
    assert solar[0]<no_solar[0] and solar[2:]==no_solar[2:] and solar[1]==no_solar[1]
    hp=totals(dict(base,heating='Heat pump'))
    assert hp[0]>no_solar[0] and hp[1]==0<no_solar[1]
    assert hp[0]<totals(dict(base,heating='Electric resistance'))[0]
    large=totals(dict(base,floor_area_m2='200'))
    assert sum(large[:2])>sum(no_solar[:2])
    assert sum(large[:2])/200<=sum(no_solar[:2])/100
    winter=monthly_components(base)
    assert winter[0]['gas']>winter[6]['gas']
    return groups

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--properties', type=Path, default=Path(__file__).resolve().parents[1] / 'csv/properties.csv')
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'csv/energy_usage.csv')
    args = parser.parse_args()
    with args.properties.open(newline='') as f:
        properties=list(csv.DictReader(f))
    rows=generate(properties)
    assert rows==generate(properties)
    groups=validate(properties,rows)
    output=args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS,lineterminator='\n');writer.writeheader();writer.writerows(rows)
    gas_totals=[sum(float(r['gas_kwh']) for r in groups[p['property_id']]) for p in properties if 'gas boiler' in p['heating']]
    electricity_totals=[sum(float(r['electricity_kwh']) for r in groups[p['property_id']]) for p in properties]
    print(f'Validated {len(rows)} rows, {len(properties)} properties, 12 months each; all paired physical checks passed.')
    print(f'Median annual gas among gas-heated homes: {median(gas_totals):.0f} kWh; median grid electricity across all homes: {median(electricity_totals):.0f} kWh.')
    print(f'SHA256: {hashlib.sha256(output.read_bytes()).hexdigest()}')
    for pid in ('P00001','P00002','P00003','P00006','P00009','P00010'):
        if pid in groups:
            print(pid,round(sum(float(r['electricity_kwh']) for r in groups[pid])),round(sum(float(r['gas_kwh']) for r in groups[pid])))

if __name__=='__main__':
    main()
