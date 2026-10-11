import {test} from 'node:test';
import assert from 'node:assert/strict';
import {baselineOnlyOptimization, emptyPlan, groupedPackages, orderedRecommendations, uniqueText} from '../lib/planner.ts';
import type {PackageTradeoff, Recommendation} from '../lib/types.ts';

test('identical packages merge across objectives and selected priority comes first', () => {
  const base = {installation_cost_gbp:1700, carbon_reduction_kg_co2e:415, net_energy_savings_kwh:2279, annual_bill_savings_gbp:137, simple_payback_years:12.4};
  const options: PackageTradeoff[] = [
    {...base, objective:'shortest_payback', retrofits:['smart_thermostat']},
    {...base, objective:'carbon_reduction', retrofits:['loft_insulation','smart_thermostat']},
    {...base, objective:'energy_reduction', retrofits:['smart_thermostat','loft_insulation']},
  ];
  const rows=groupedPackages(options,'energy_reduction');
  assert.equal(rows.length,2); assert.equal(rows[0].chosen,true);
  assert.deepEqual(rows[0].objectives,['carbon_reduction','energy_reduction']);
  assert.equal(rows[0].option.objective,'energy_reduction');
});
test('recommended measures keep backend priority and excluded options stay last',()=>{
  const rows=[{retrofit:'heat_pump',recommended:false,priority:null},{retrofit:'smart_thermostat',recommended:true,priority:2},{retrofit:'loft_insulation',recommended:true,priority:1}] as Recommendation[];
  assert.deepEqual(orderedRecommendations(rows).map(row=>row.retrofit),['loft_insulation','smart_thermostat','heat_pump']);
  assert.equal(rows[0].retrofit,'heat_pump');
});
test('fresh snapshot plans have no stale estimates and duplicated evidence is removed',()=>{
  assert.equal(emptyPlan('new-property-version').optimization,null);
  assert.deepEqual(emptyPlan('new-property-version').selected,[]);
  assert.equal(emptyPlan('new-property-version').recommendationsChecked,false);
  assert.deepEqual(uniqueText([' Same reason ', 'Same reason', '']),['Same reason']);
});

test('baseline-only search does not imply a validated upgrade recommendation',()=>{
  const result={best_scenario:{applied_retrofits:[]},ranked_packages:[{}]};
  assert.equal(baselineOnlyOptimization(result),true);
  assert.equal(baselineOnlyOptimization({...result, ranked_packages:[{},{}]}),false);
  assert.equal(baselineOnlyOptimization({...result,best_scenario:null}),false);
});
