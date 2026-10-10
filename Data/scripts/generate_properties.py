import csv, random, math, hashlib
from pathlib import Path
from collections import Counter

path = Path(__file__).resolve().with_name('properties.csv')
with path.open(newline='') as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    demos = list(reader)[:10]
rng = random.Random(42)
anchors = {'Greater London':550037,'South East':380878,'South West':302298,'East of England':337518,'West Midlands':250880,'East Midlands':242274,'North West':221445,'North East':166943,'Yorkshire and The Humber':209116,'Wales':215037}
type_prices = {'Detached':444936,'Semi-detached':278555,'Terraced':231945,'Flat':192704}
areas = {'Detached':(128,19,65,240),'Semi-detached':(101,18,51,200),'Terraced':(86,16,45,170),'Flat':(63,16,30,130)}
age_means = {'Detached':52,'Semi-detached':60,'Terraced':82,'Flat':38}
types = ['Detached']*17+['Semi-detached']*26+['Terraced']*26+['Flat']*21
regions = [r for r in anchors for _ in range(10-sum(d['region']==r for d in demos))]
rng.shuffle(types); rng.shuffle(regions)
electric_indices = set(rng.sample(range(90),5))
heatpump_indices = set(rng.sample(sorted(electric_indices),2))
def choose(options, weights):
    return rng.choices(options,weights=weights,k=1)[0]
def generate():
    rows = [dict(d) for d in demos]
    for j,(kind,region) in enumerate(zip(types,regions)):
        mean,sd,low,high = areas[kind]
        area = round(min(high,max(low,rng.gauss(mean,sd))),1)
        age = round(min(180,max(1,rng.gauss(age_means[kind],34))))
        bedrooms = choose([1,2],[.75,.25]) if area<55 else choose([2,3],[.8,.2]) if area<90 else choose([3,4],[.8,.2]) if area<140 else choose([4,5,6],[.65,.3,.05])
        insulation = choose(['Poor','Average','Good'],[.01,.04,.95] if age<=26 else [.10,.45,.45] if age<40 else [.30,.50,.20] if age<=81 else [.50,.35,.15])
        glazing = choose(['Single','Double','Triple'],[.005,.845,.15] if age<=26 else [.08,.87,.05] if age<60 else [.25,.72,.03])
        if j in electric_indices:
            heating = 'Heat pump' if j in heatpump_indices else 'Electric resistance'
        else:
            heating = choose(['Old gas boiler','Modern gas boiler'],[.02,.98] if age<=26 else [.2,.8] if age<60 else [.45,.55])
        solar = rng.random() < {'Detached':.18,'Semi-detached':.12,'Terraced':.08,'Flat':.02}[kind]
        controls = rng.random() < (.85 if heating=='Heat pump' else .5 if age<=26 else .3)
        score = 50+{'Poor':-12,'Average':8,'Good':20}[insulation]+{'Single':-10,'Double':5,'Triple':10}[glazing]+{'Old gas boiler':-8,'Modern gas boiler':3,'Heat pump':12,'Electric resistance':-5}[heating]+8*solar+4*controls+(5 if age<=26 else 0)+rng.gauss(0,5)
        rating = next((label for threshold,label in [(85,'A'),(75,'B'),(65,'C'),(50,'D'),(35,'E'),(20,'F')] if score>=threshold),'G')
        # HPI averages are anchors; all adjustments below are synthetic assumptions.
        value = anchors[region]*(type_prices[kind]/272611)*(area/mean)**.55*(1+.02*(bedrooms-3))*(1.04 if age<=10 else 1)*math.exp(rng.gauss(-.5*.18**2,.18))
        row = [f'P{j+11:05d}',f'C{j+11:05d}',kind,age,area,bedrooms,rating,heating,insulation,glazing,str(solar).lower(),str(controls).lower(),region,int(round(max(50000,value)/1000)*1000),'synthetic',42]
        rows.append(dict(zip(fields,row)))
    return rows
rows = generate()
assert len(rows)==100 and len(fields)==16
assert rows[:10]==demos
assert len({r['property_id'] for r in rows})==100
assert len({r['customer_id'] for r in rows})==100
assert all(set(r)==set(fields) and all(str(v)!='' for v in r.values()) for r in rows)
for r in rows:
    assert r['property_type'] in areas and r['region'] in anchors
    assert str(r['energy_rating']) in list('ABCDEFG')
    assert r['heating'] in ['Old gas boiler','Modern gas boiler','Heat pump','Electric resistance']
    assert r['insulation'] in ['Poor','Average','Good'] and r['glazing'] in ['Single','Double','Triple']
    assert str(r['solar']) in ['true','false'] and str(r['smart_controls']) in ['true','false']
    assert 1<=int(r['age'])<=180 and 30<=float(r['floor_area_m2'])<=350 and 1<=int(r['bedrooms'])<=6
    assert float(r['current_value_estimate_gbp'])>0 and r['data_status']=='synthetic' and int(r['generation_seed'])==42
with path.open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n'); writer.writeheader(); writer.writerows(rows)
gas_houses=[r for r in rows if r['property_type']!='Flat' and 'gas boiler' in r['heating']]
inside=sum(51<=float(r['floor_area_m2'])<=150 for r in gas_houses)
print({'rows':len(rows),'columns':len(fields),'property_types':dict(Counter(r['property_type'] for r in rows)),'ratings':dict(Counter(r['energy_rating'] for r in rows)),'heating':dict(Counter(r['heating'] for r in rows)),'gas_houses_51_150_m2':f'{inside}/{len(gas_houses)}','sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
