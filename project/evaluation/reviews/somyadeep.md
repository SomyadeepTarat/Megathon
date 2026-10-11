# Advisor review for Somyadeep

These are actual recorded answers. Fill each `review` field in the JSON with `true` or `false`; leave unresolved judgements `null`. Add notes for failures. A named reviewer with null labels does not count as a completed review.

Check groundedness (claims supported by supplied evidence), factual accuracy (values, units and attribution), completeness (answers the question), tool invocation (what-if uses fresh simulation; conditional packages are blocked), unavailable handling (no invented replacement), and no unsupported claims (including nonnumeric promises). Do not approve merely because the numeric check passes.

Recorded source SHA256: `46bc5280d898292e9f95231aa27cf12662afb1452851ad5bd2a8e8c42e51e6d5`

After reviewing: `python -m evaluation.evaluate_explanations --input evaluation/reviews/somyadeep.json`

The PRD targets are ≥90% groundedness, ≥90% factual accuracy and <5% unsupported claims. Existing answers may fail completeness; mark that accurately and fix/rerecord failing cases before claiming success.

## LLM01: Why is my score low?

Status: success; mode: grounded_llm; tools: assessment.

Baseline Green Home Score: 22 points (backend estimate).
Baseline purchased electricity: 2997.41 kWh/year (backend estimate).
Baseline gas: 27040.56 kWh/year (backend estimate).
Valuation estimate is unavailable. Synthetic training data cannot support real-world value uplift
Issues: Insulation is poor.
Issues: An old gas boiler is recorded.
Issues: Windows are single glazed.
Issues: No renewable contribution is recorded.
Issues: No smart energy controls are recorded.
Issues: Purchased-energy intensity exceeds the supplied benchmark.
Warnings: Score uses a synthetic reference benchmark, not an official consumption standard.
Warnings: Heating subtype is a disclosed synthetic modeling input, not survey evidence.
Warnings: Confirm alignment of the property snapshot and energy period; see source methodology.
Warnings: Energy data quality: synthetic.
Sources: Property dataset: synthetic; Data/csv/properties.csv and Data/csv/energy_usage.csv
Sources: Annual energy: synthetic; Sum of 12 monthly purchased-energy readings for 2025; incomplete fuel totals remain null
Sources: Synthetic fixed reference model v1; not an official NEED benchmark
Energy efficiency: subscore 20.0; weighted contribution 5.0 points. Recorded evidence: energy rating: F.
Consumption intensity: subscore 45.850612582173056; weighted contribution 9.170122516434612 points. Recorded evidence: intensity kwh m2 year: 202.95925675675676; benchmark kwh m2 year: 128.212778; benchmark source: Synthetic fixed reference model v1; not an official NEED benchmark.
Insulation: subscore 20.0; weighted contribution 3.0 points. Recorded evidence: insulation: poor.
Heating system: subscore 20.0; weighted contribution 3.0 points. Recorded evidence: heating system: old_gas_boiler.
Windows: subscore 20.0; weighted contribution 2.0 points. Recorded evidence: glazing: single.
Renewable energy: subscore 0.0; weighted contribution 0.0 points. Recorded evidence: renewable contribution: none.
Smart management: subscore 0.0; weighted contribution 0.0 points. Recorded evidence: smart controls: none.
Negative fuel savings mean increased consumption. Property-value associations do not prove a causal retrofit premium.

### Structured evidence

```json
{
  "property_id": "P00001",
  "status": "success",
  "score": {
    "status": "available",
    "unrounded_score": 22.17012251643461,
    "classification": "Very poor",
    "components": [
      {
        "name": "energy_efficiency",
        "subscore": 20.0,
        "weight": 0.25,
        "contribution": 5.0,
        "evidence": {
          "energy_rating": "F"
        }
      },
      {
        "name": "consumption_intensity",
        "subscore": 45.850612582173056,
        "weight": 0.2,
        "contribution": 9.170122516434612,
        "evidence": {
          "intensity_kwh_m2_year": 202.95925675675676,
          "benchmark_kwh_m2_year": 128.212778,
          "benchmark_source": "Synthetic fixed reference model v1; not an official NEED benchmark"
        }
      },
      {
        "name": "insulation",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "insulation": "poor"
        }
      },
      {
        "name": "heating_system",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "heating_system": "old_gas_boiler"
        }
      },
      {
        "name": "windows",
        "subscore": 20.0,
        "weight": 0.1,
        "contribution": 2.0,
        "evidence": {
          "glazing": "single"
        }
      },
      {
        "name": "renewable_energy",
        "subscore": 0.0,
        "weight": 0.1,
        "contribution": 0.0,
        "evidence": {
          "renewable_contribution": "none"
        }
      },
      {
        "name": "smart_management",
        "subscore": 0.0,
        "weight": 0.05,
        "contribution": 0.0,
        "evidence": {
          "smart_controls": "none"
        }
      }
    ],
    "missing_fields": [],
    "methodology_version": "greenprint-score-v1",
    "baseline": 22
  },
  "issues": [
    "Insulation is poor.",
    "An old gas boiler is recorded.",
    "Windows are single glazed.",
    "No renewable contribution is recorded.",
    "No smart energy controls are recorded.",
    "Purchased-energy intensity exceeds the supplied benchmark."
  ],
  "warnings": [
    "Score uses a synthetic reference benchmark, not an official consumption standard.",
    "Heating subtype is a disclosed synthetic modeling input, not survey evidence.",
    "Confirm alignment of the property snapshot and energy period; see source methodology.",
    "Energy data quality: synthetic."
  ],
  "energy": {
    "baseline_electricity_kwh": 2997.41,
    "baseline_gas_kwh": 27040.56
  },
  "carbon": {
    "status": "available",
    "electricity_kg_co2e": 392.5408136,
    "gas_kg_co2e": 4929.764493600001,
    "total_kg_co2e": 5322.3053072,
    "reason": null,
    "factors": {
      "electricity": {
        "fuel": "electricity",
        "kg_co2e_per_kwh": 0.13096,
        "source": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026",
        "source_year": 2026,
        "accounting_boundary": "Scope 2 location-based UK generation; excludes transmission/distribution and well-to-tank emissions",
        "version": "DESNZ-2026-flat-revised-2026-07-31"
      },
      "gas": {
        "fuel": "gas",
        "kg_co2e_per_kwh": 0.18231,
        "source": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026",
        "source_year": 2026,
        "accounting_boundary": "Scope 1 natural gas combustion; gross calorific value; excludes well-to-tank emissions",
        "version": "DESNZ-2026-flat-revised-2026-07-31"
      }
    }
  },
  "valuation": {
    "status": "unavailable",
    "reason": "Synthetic training data cannot support real-world value uplift",
    "value_before": null,
    "value_after": null,
    "uplift_range": null,
    "baseline_value_gbp": null,
    "after_value_gbp": null,
    "baseline_range_gbp": null,
    "after_range_gbp": null,
    "value_change_gbp": null,
    "value_change_range_gbp": null,
    "confidence_level": null,
    "method": null,
    "warnings": []
  },
  "sources": [
    "Property dataset: synthetic; Data/csv/properties.csv and Data/csv/energy_usage.csv",
    "Annual energy: synthetic; Sum of 12 monthly purchased-energy readings for 2025; incomplete fuel totals remain null",
    "Synthetic fixed reference model v1; not an official NEED benchmark"
  ]
}
```

## LLM02: Explain all seven score components.

Status: success; mode: grounded_llm; tools: assessment.

Baseline Green Home Score: 22 points (backend estimate).
Baseline purchased electricity: 2997.41 kWh/year (backend estimate).
Baseline gas: 27040.56 kWh/year (backend estimate).
Valuation estimate is unavailable. Synthetic training data cannot support real-world value uplift
Issues: Insulation is poor.
Issues: An old gas boiler is recorded.
Issues: Windows are single glazed.
Issues: No renewable contribution is recorded.
Issues: No smart energy controls are recorded.
Issues: Purchased-energy intensity exceeds the supplied benchmark.
Warnings: Score uses a synthetic reference benchmark, not an official consumption standard.
Warnings: Heating subtype is a disclosed synthetic modeling input, not survey evidence.
Warnings: Confirm alignment of the property snapshot and energy period; see source methodology.
Warnings: Energy data quality: synthetic.
Sources: Property dataset: synthetic; Data/csv/properties.csv and Data/csv/energy_usage.csv
Sources: Annual energy: synthetic; Sum of 12 monthly purchased-energy readings for 2025; incomplete fuel totals remain null
Sources: Synthetic fixed reference model v1; not an official NEED benchmark
Energy efficiency: subscore 20.0; weighted contribution 5.0 points. Recorded evidence: energy rating: F.
Consumption intensity: subscore 45.850612582173056; weighted contribution 9.170122516434612 points. Recorded evidence: intensity kwh m2 year: 202.95925675675676; benchmark kwh m2 year: 128.212778; benchmark source: Synthetic fixed reference model v1; not an official NEED benchmark.
Insulation: subscore 20.0; weighted contribution 3.0 points. Recorded evidence: insulation: poor.
Heating system: subscore 20.0; weighted contribution 3.0 points. Recorded evidence: heating system: old_gas_boiler.
Windows: subscore 20.0; weighted contribution 2.0 points. Recorded evidence: glazing: single.
Renewable energy: subscore 0.0; weighted contribution 0.0 points. Recorded evidence: renewable contribution: none.
Smart management: subscore 0.0; weighted contribution 0.0 points. Recorded evidence: smart controls: none.
Negative fuel savings mean increased consumption. Property-value associations do not prove a causal retrofit premium.

### Structured evidence

```json
{
  "property_id": "P00001",
  "status": "success",
  "score": {
    "status": "available",
    "unrounded_score": 22.17012251643461,
    "classification": "Very poor",
    "components": [
      {
        "name": "energy_efficiency",
        "subscore": 20.0,
        "weight": 0.25,
        "contribution": 5.0,
        "evidence": {
          "energy_rating": "F"
        }
      },
      {
        "name": "consumption_intensity",
        "subscore": 45.850612582173056,
        "weight": 0.2,
        "contribution": 9.170122516434612,
        "evidence": {
          "intensity_kwh_m2_year": 202.95925675675676,
          "benchmark_kwh_m2_year": 128.212778,
          "benchmark_source": "Synthetic fixed reference model v1; not an official NEED benchmark"
        }
      },
      {
        "name": "insulation",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "insulation": "poor"
        }
      },
      {
        "name": "heating_system",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "heating_system": "old_gas_boiler"
        }
      },
      {
        "name": "windows",
        "subscore": 20.0,
        "weight": 0.1,
        "contribution": 2.0,
        "evidence": {
          "glazing": "single"
        }
      },
      {
        "name": "renewable_energy",
        "subscore": 0.0,
        "weight": 0.1,
        "contribution": 0.0,
        "evidence": {
          "renewable_contribution": "none"
        }
      },
      {
        "name": "smart_management",
        "subscore": 0.0,
        "weight": 0.05,
        "contribution": 0.0,
        "evidence": {
          "smart_controls": "none"
        }
      }
    ],
    "missing_fields": [],
    "methodology_version": "greenprint-score-v1",
    "baseline": 22
  },
  "issues": [
    "Insulation is poor.",
    "An old gas boiler is recorded.",
    "Windows are single glazed.",
    "No renewable contribution is recorded.",
    "No smart energy controls are recorded.",
    "Purchased-energy intensity exceeds the supplied benchmark."
  ],
  "warnings": [
    "Score uses a synthetic reference benchmark, not an official consumption standard.",
    "Heating subtype is a disclosed synthetic modeling input, not survey evidence.",
    "Confirm alignment of the property snapshot and energy period; see source methodology.",
    "Energy data quality: synthetic."
  ],
  "energy": {
    "baseline_electricity_kwh": 2997.41,
    "baseline_gas_kwh": 27040.56
  },
  "carbon": {
    "status": "available",
    "electricity_kg_co2e": 392.5408136,
    "gas_kg_co2e": 4929.764493600001,
    "total_kg_co2e": 5322.3053072,
    "reason": null,
    "factors": {
      "electricity": {
        "fuel": "electricity",
        "kg_co2e_per_kwh": 0.13096,
        "source": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026",
        "source_year": 2026,
        "accounting_boundary": "Scope 2 location-based UK generation; excludes transmission/distribution and well-to-tank emissions",
        "version": "DESNZ-2026-flat-revised-2026-07-31"
      },
      "gas": {
        "fuel": "gas",
        "kg_co2e_per_kwh": 0.18231,
        "source": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026",
        "source_year": 2026,
        "accounting_boundary": "Scope 1 natural gas combustion; gross calorific value; excludes well-to-tank emissions",
        "version": "DESNZ-2026-flat-revised-2026-07-31"
      }
    }
  },
  "valuation": {
    "status": "unavailable",
    "reason": "Synthetic training data cannot support real-world value uplift",
    "value_before": null,
    "value_after": null,
    "uplift_range": null,
    "baseline_value_gbp": null,
    "after_value_gbp": null,
    "baseline_range_gbp": null,
    "after_range_gbp": null,
    "value_change_gbp": null,
    "value_change_range_gbp": null,
    "confidence_level": null,
    "method": null,
    "warnings": []
  },
  "sources": [
    "Property dataset: synthetic; Data/csv/properties.csv and Data/csv/energy_usage.csv",
    "Annual energy: synthetic; Sum of 12 monthly purchased-energy readings for 2025; incomplete fuel totals remain null",
    "Synthetic fixed reference model v1; not an official NEED benchmark"
  ]
}
```

## LLM03: Why prioritize insulation?

Status: success; mode: grounded_llm; tools: assessment.

Valuation estimate is unavailable. Synthetic training data cannot support real-world value uplift
Issues: Insulation is poor.
Issues: Windows are single glazed.
Issues: Purchased-energy intensity exceeds the supplied benchmark.
Warnings: Score uses a synthetic reference benchmark, not an official consumption standard.
Warnings: Heating subtype is a disclosed synthetic modeling input, not survey evidence.
Warnings: Confirm alignment of the property snapshot and energy period; see source methodology.
Warnings: Energy data quality: synthetic.
Sources: Property dataset: synthetic; Data/csv/properties.csv and Data/csv/energy_usage.csv
Sources: Annual energy: synthetic; Sum of 12 monthly purchased-energy readings for 2025; incomplete fuel totals remain null
Sources: Synthetic fixed reference model v1; not an official NEED benchmark
Insulation: subscore 20.0; weighted contribution 3.0 points. Recorded evidence: insulation: poor.
Heating system: subscore 20.0; weighted contribution 3.0 points. Recorded evidence: heating system: old_gas_boiler.
Windows: subscore 20.0; weighted contribution 2.0 points. Recorded evidence: glazing: single.
Negative fuel savings mean increased consumption. Property-value associations do not prove a causal retrofit premium.

### Structured evidence

```json
{
  "property_id": "P00001",
  "status": "success",
  "score": {
    "status": "available",
    "unrounded_score": 22.17012251643461,
    "classification": "Very poor",
    "components": [
      {
        "name": "energy_efficiency",
        "subscore": 20.0,
        "weight": 0.25,
        "contribution": 5.0,
        "evidence": {
          "energy_rating": "F"
        }
      },
      {
        "name": "consumption_intensity",
        "subscore": 45.850612582173056,
        "weight": 0.2,
        "contribution": 9.170122516434612,
        "evidence": {
          "intensity_kwh_m2_year": 202.95925675675676,
          "benchmark_kwh_m2_year": 128.212778,
          "benchmark_source": "Synthetic fixed reference model v1; not an official NEED benchmark"
        }
      },
      {
        "name": "insulation",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "insulation": "poor"
        }
      },
      {
        "name": "heating_system",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "heating_system": "old_gas_boiler"
        }
      },
      {
        "name": "windows",
        "subscore": 20.0,
        "weight": 0.1,
        "contribution": 2.0,
        "evidence": {
          "glazing": "single"
        }
      },
      {
        "name": "renewable_energy",
        "subscore": 0.0,
        "weight": 0.1,
        "contribution": 0.0,
        "evidence": {
          "renewable_contribution": "none"
        }
      },
      {
        "name": "smart_management",
        "subscore": 0.0,
        "weight": 0.05,
        "contribution": 0.0,
        "evidence": {
          "smart_controls": "none"
        }
      }
    ],
    "missing_fields": [],
    "methodology_version": "greenprint-score-v1",
    "baseline": 22
  },
  "issues": [
    "Insulation is poor.",
    "An old gas boiler is recorded.",
    "Windows are single glazed.",
    "No renewable contribution is recorded.",
    "No smart energy controls are recorded.",
    "Purchased-energy intensity exceeds the supplied benchmark."
  ],
  "warnings": [
    "Score uses a synthetic reference benchmark, not an official consumption standard.",
    "Heating subtype is a disclosed synthetic modeling input, not survey evidence.",
    "Confirm alignment of the property snapshot and energy period; see source methodology.",
    "Energy data quality: synthetic."
  ],
  "energy": {
    "baseline_electricity_kwh": 2997.41,
    "baseline_gas_kwh": 27040.56
  },
  "carbon": {
    "status": "available",
    "electricity_kg_co2e": 392.5408136,
    "gas_kg_co2e": 4929.764493600001,
    "total_kg_co2e": 5322.3053072,
    "reason": null,
    "factors": {
      "electricity": {
        "fuel": "electricity",
        "kg_co2e_per_kwh": 0.13096,
        "source": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026",
        "source_year": 2026,
        "accounting_boundary": "Scope 2 location-based UK generation; excludes transmission/distribution and well-to-tank emissions",
        "version": "DESNZ-2026-flat-revised-2026-07-31"
      },
      "gas": {
        "fuel": "gas",
        "kg_co2e_per_kwh": 0.18231,
        "source": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026",
        "source_year": 2026,
        "accounting_boundary": "Scope 1 natural gas combustion; gross calorific value; excludes well-to-tank emissions",
        "version": "DESNZ-2026-flat-revised-2026-07-31"
      }
    }
  },
  "valuation": {
    "status": "unavailable",
    "reason": "Synthetic training data cannot support real-world value uplift",
    "value_before": null,
    "value_after": null,
    "uplift_range": null,
    "baseline_value_gbp": null,
    "after_value_gbp": null,
    "baseline_range_gbp": null,
    "after_range_gbp": null,
    "value_change_gbp": null,
    "value_change_range_gbp": null,
    "confidence_level": null,
    "method": null,
    "warnings": []
  },
  "sources": [
    "Property dataset: synthetic; Data/csv/properties.csv and Data/csv/energy_usage.csv",
    "Annual energy: synthetic; Sum of 12 monthly purchased-energy readings for 2025; incomplete fuel totals remain null",
    "Synthetic fixed reference model v1; not an official NEED benchmark"
  ]
}
```

## LLM04: What if I install only insulation?

Status: conditional; mode: deterministic; tools: feasibility.

This package is not confirmed feasible. Review the backend feasibility details before proceeding.

### Structured evidence

```json
{
  "feasibility": {
    "status": "available",
    "all_feasible": false,
    "rejected_retrofits": [],
    "conditional_retrofits": [
      "loft_insulation"
    ],
    "items": [
      {
        "retrofit": "loft_insulation",
        "status": "conditional",
        "reason": "roof_suitable_for_loft is unknown; confirm site suitability."
      }
    ],
    "reason": null
  }
}
```

## LLM05: What if I install only solar?

Status: conditional; mode: deterministic; tools: feasibility.

This package is not confirmed feasible. Review the backend feasibility details before proceeding.

### Structured evidence

```json
{
  "feasibility": {
    "status": "available",
    "all_feasible": false,
    "rejected_retrofits": [],
    "conditional_retrofits": [
      "solar_panels"
    ],
    "items": [
      {
        "retrofit": "solar_panels",
        "status": "conditional",
        "reason": "roof_suitable_for_solar is unknown; confirm site suitability."
      }
    ],
    "reason": null
  }
}
```

## LLM06: What if I install only a heat pump?

Status: conditional; mode: deterministic; tools: feasibility.

This package is not confirmed feasible. Review the backend feasibility details before proceeding.

### Structured evidence

```json
{
  "feasibility": {
    "status": "available",
    "all_feasible": false,
    "rejected_retrofits": [],
    "conditional_retrofits": [
      "heat_pump"
    ],
    "items": [
      {
        "retrofit": "heat_pump",
        "status": "conditional",
        "reason": "heat_pump_compatible must be confirmed."
      }
    ],
    "reason": null
  }
}
```

## LLM07: What if I install double glazing?

Status: partial; mode: grounded_llm; tools: feasibility, simulate.

Baseline purchased electricity: 2997.41 kWh/year (backend estimate).
Baseline gas: 27040.56 kWh/year (backend estimate).
Post-retrofit purchased electricity: 2997.423337 kWh/year (backend estimate).
Post-retrofit gas: 24618.93825225 kWh/year (backend estimate).
Electricity savings: -0.013337000000319676 kWh/year (backend estimate).
Gas savings: 2421.621747750003 kWh/year (backend estimate).
Net purchased-energy savings: 2421.608410750003 kWh/year (backend estimate).
Purchased-energy reduction: 8.06182445335022 % (backend estimate).
Carbon reduction: 441.48411421878336 kg CO2e/year (backend estimate).
Valuation estimate is unavailable. No supported projected EPC estimate; the existing valuation model uses recorded EPC as its energy feature.
Issues: Insulation is poor.
Issues: An old gas boiler is recorded.
Issues: Windows are single glazed.
Assumptions: Reduces remaining space-heating demand by 10% (brief range 8–12%); hot-water demand is unchanged.
Warnings: Score uses a synthetic reference benchmark, not an official consumption standard.
Warnings: Heating subtype is a disclosed synthetic modeling input, not survey evidence.
Warnings: Confirm alignment of the property snapshot and energy period; see source methodology.
Warnings: Energy data quality: synthetic.
Warnings: Score uses a synthetic reference benchmark, not an official consumption standard.
Warnings: Heating subtype is a disclosed synthetic modeling input, not survey evidence.
Warnings: Confirm alignment of the property snapshot and energy period; see source methodology.
Warnings: Physical component totals differ from rounded monthly purchased-energy totals by at most 0.06 kWh; the small residual was capped at zero.
Warnings: Installation cost unavailable; P4 catalogue does not supply documented costs.
Warnings: Physical input thermal_demand_kwh has no per-field source metadata.
Warnings: Physical input thermal_demand_scope has no per-field source metadata.
Warnings: Physical input space_heating_demand_kwh has no per-field source metadata.
Warnings: Physical input hot_water_demand_kwh has no per-field source metadata.
Warnings: Physical input base_appliance_electricity_kwh has no per-field source metadata.
Warnings: Physical input annual_electricity_demand_kwh has no per-field source metadata.
Warnings: Physical input gas_space_heating_kwh has no per-field source metadata.
Warnings: Physical input gas_hot_water_kwh has no per-field source metadata.
Warnings: Physical input electric_space_heating_kwh has no per-field source metadata.
Warnings: Physical input electric_hot_water_kwh has no per-field source metadata.
Warnings: Physical input boiler_efficiency has no per-field source metadata.
Warnings: Physical input solar_generation_kwh has no per-field source metadata.
Warnings: Physical input solar_self_consumed_kwh has no per-field source metadata.
Sources: Property dataset: synthetic; Data/csv/properties.csv and Data/csv/energy_usage.csv
Sources: Baseline energy: synthetic; Sum of 12 monthly purchased-energy readings for 2025; incomplete fuel totals remain null
Sources: https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026 (2026); Scope 2 location-based UK generation; excludes transmission/distribution and well-to-tank emissions
Sources: https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026 (2026); Scope 1 natural gas combustion; gross calorific value; excludes well-to-tank emissions
Negative fuel savings mean increased consumption. Property-value associations do not prove a causal retrofit premium.

### Structured evidence

```json
{
  "property_id": "P00001",
  "status": "partial",
  "score": {
    "status": "available",
    "unrounded_score": 22.17012251643461,
    "classification": "Very poor",
    "components": [
      {
        "name": "energy_efficiency",
        "subscore": 20.0,
        "weight": 0.25,
        "contribution": 5.0,
        "evidence": {
          "energy_rating": "F"
        }
      },
      {
        "name": "consumption_intensity",
        "subscore": 45.850612582173056,
        "weight": 0.2,
        "contribution": 9.170122516434612,
        "evidence": {
          "intensity_kwh_m2_year": 202.95925675675676,
          "benchmark_kwh_m2_year": 128.212778,
          "benchmark_source": "Synthetic fixed reference model v1; not an official NEED benchmark"
        }
      },
      {
        "name": "insulation",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "insulation": "poor"
        }
      },
      {
        "name": "heating_system",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "heating_system": "old_gas_boiler"
        }
      },
      {
        "name": "windows",
        "subscore": 20.0,
        "weight": 0.1,
        "contribution": 2.0,
        "evidence": {
          "glazing": "single"
        }
      },
      {
        "name": "renewable_energy",
        "subscore": 0.0,
        "weight": 0.1,
        "contribution": 0.0,
        "evidence": {
          "renewable_contribution": "none"
        }
      },
      {
        "name": "smart_management",
        "subscore": 0.0,
        "weight": 0.05,
        "contribution": 0.0,
        "evidence": {
          "smart_controls": "none"
        }
      }
    ],
    "missing_fields": [],
    "methodology_version": "greenprint-score-v1",
    "baseline": 22,
    "after": 29,
    "after_status": "available",
    "after_components": [
      {
        "name": "energy_efficiency",
        "subscore": 20.0,
        "weight": 0.25,
        "contribution": 5.0,
        "evidence": {
          "energy_rating": "F"
        }
      },
      {
        "name": "consumption_intensity",
        "subscore": 52.23149725170033,
        "weight": 0.2,
        "contribution": 10.446299450340065,
        "evidence": {
          "intensity_kwh_m2_year": 186.59703776520269,
          "benchmark_kwh_m2_year": 128.212778,
          "benchmark_source": "Synthetic fixed reference model v1; not an official NEED benchmark"
        }
      },
      {
        "name": "insulation",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "insulation": "poor"
        }
      },
      {
        "name": "heating_system",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "heating_system": "old_gas_boiler"
        }
      },
      {
        "name": "windows",
        "subscore": 75.0,
        "weight": 0.1,
        "contribution": 7.5,
        "evidence": {
          "glazing": "double"
        }
      },
      {
        "name": "renewable_energy",
        "subscore": 0.0,
        "weight": 0.1,
        "contribution": 0.0,
        "evidence": {
          "renewable_contribution": "none"
        }
      },
      {
        "name": "smart_management",
        "subscore": 0.0,
        "weight": 0.05,
        "contribution": 0.0,
        "evidence": {
          "smart_controls": "none"
        }
      }
    ]
  },
  "issues": [
    "Insulation is poor.",
    "An old gas boiler is recorded.",
    "Windows are single glazed.",
    "No renewable contribution is recorded.",
    "No smart energy controls are recorded.",
    "Purchased-energy intensity exceeds the supplied benchmark."
  ],
  "warnings": [
    "Score uses a synthetic reference benchmark, not an official consumption standard.",
    "Heating subtype is a disclosed synthetic modeling input, not survey evidence.",
    "Confirm alignment of the property snapshot and energy period; see source methodology.",
    "Energy data quality: synthetic.",
    "Score uses a synthetic reference benchmark, not an official consumption standard.",
    "Heating subtype is a disclosed synthetic modeling input, not survey evidence.",
    "Confirm alignment of the property snapshot and energy period; see source methodology.",
    "Physical component totals differ from rounded monthly purchased-energy totals by at most 0.06 kWh; the small residual was capped at zero.",
    "Installation cost unavailable; P4 catalogue does not supply documented costs.",
    "Physical input thermal_demand_kwh has no per-field source metadata.",
    "Physical input thermal_demand_scope has no per-field source metadata.",
    "Physical input space_heating_demand_kwh has no per-field source metadata.",
    "Physical input hot_water_demand_kwh has no per-field source metadata.",
    "Physical input base_appliance_electricity_kwh has no per-field source metadata.",
    "Physical input annual_electricity_demand_kwh has no per-field source metadata.",
    "Physical input gas_space_heating_kwh has no per-field source metadata.",
    "Physical input gas_hot_water_kwh has no per-field source metadata.",
    "Physical input electric_space_heating_kwh has no per-field source metadata.",
    "Physical input electric_hot_water_kwh has no per-field source metadata.",
    "Physical input boiler_efficiency has no per-field source metadata.",
    "Physical input solar_generation_kwh has no per-field source metadata.",
    "Physical input solar_self_consumed_kwh has no per-field source metadata."
  ],
  "scenario_id": "8c65958e-0d15-4b68-bd59-641fcfb7ac73",
  "reason": null,
  "feasibility": {
    "status": "available",
    "all_feasible": true,
    "rejected_retrofits": [],
    "conditional_retrofits": [],
    "items": [
      {
        "retrofit": "double_glazing",
        "status": "feasible",
        "reason": "Known installation and compatibility fields permit screening; survey confirmation may still be needed."
      }
    ],
    "reason": null
  },
  "carbon": {
    "status": "available",
    "reduction_kg_co2e": 441.48411421878336,
    "factors": [
      {
        "fuel": "electricity",
        "kg_co2e_per_kwh": 0.13096,
        "source": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026",
        "source_year": 2026,
        "accounting_boundary": "Scope 2 location-based UK generation; excludes transmission/distribution and well-to-tank emissions",
        "version": "DESNZ-2026-flat-revised-2026-07-31"
      },
      {
        "fuel": "gas",
        "kg_co2e_per_kwh": 0.18231,
        "source": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026",
        "source_year": 2026,
        "accounting_boundary": "Scope 1 natural gas combustion; gross calorific value; excludes well-to-tank emissions",
        "version": "DESNZ-2026-flat-revised-2026-07-31"
      }
    ],
    "reason": null
  },
  "valuation": {
    "status": "unavailable",
    "reason": "No supported projected EPC estimate; the existing valuation model uses recorded EPC as its energy feature.",
    "value_before": null,
    "value_after": null,
    "uplift_range": null,
    "baseline_value_gbp": null,
    "after_value_gbp": null,
    "baseline_range_gbp": null,
    "after_range_gbp": null,
    "value_change_gbp": null,
    "value_change_range_gbp": null,
    "confidence_level": null,
    "method": null,
    "warnings": []
  },
  "assumptions": [
    "Reduces remaining space-heating demand by 10% (brief range 8\u201312%); hot-water demand is unchanged."
  ],
  "installation_cost_gbp": null,
  "annual_bill_savings_gbp": null,
  "bill_savings_reason": "Both electricity and gas tariffs are required to calculate annual bill savings.",
  "simple_payback_years": null,
  "payback_reason": "Documented installation cost is unavailable.",
  "carbon_savings_by_fuel_kg_co2e": {
    "electricity": -0.0017466135200418648,
    "gas": 441.48586083230305
  },
  "applied_retrofits": [
    "double_glazing"
  ],
  "versions": {
    "score": "greenprint-score-v1",
    "retrofit": "p4-carbon-package-adapter-v1",
    "simulation": "p4-carbon-package-adapter-v1"
  },
  "energy": {
    "baseline_electricity_kwh": 2997.41,
    "baseline_gas_kwh": 27040.56,
    "after_electricity_kwh": 2997.423337,
    "after_gas_kwh": 24618.93825225,
    "electricity_savings_kwh": -0.013337000000319676,
    "gas_savings_kwh": 2421.621747750003,
    "net_savings_kwh": 2421.608410750003,
    "improvement_percentage": 8.06182445335022
  },
  "sources": [
    "Property dataset: synthetic; Data/csv/properties.csv and Data/csv/energy_usage.csv",
    "Baseline energy: synthetic; Sum of 12 monthly purchased-energy readings for 2025; incomplete fuel totals remain null",
    "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026 (2026); Scope 2 location-based UK generation; excludes transmission/distribution and well-to-tank emissions",
    "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026 (2026); Scope 1 natural gas combustion; gross calorific value; excludes well-to-tank emissions"
  ]
}
```

## LLM08: What if I add smart controls?

Status: conditional; mode: deterministic; tools: feasibility.

This package is not confirmed feasible. Review the backend feasibility details before proceeding.

### Structured evidence

```json
{
  "feasibility": {
    "status": "available",
    "all_feasible": false,
    "rejected_retrofits": [],
    "conditional_retrofits": [
      "smart_thermostat"
    ],
    "items": [
      {
        "retrofit": "smart_thermostat",
        "status": "conditional",
        "reason": "controls_compatible must be confirmed."
      }
    ],
    "reason": null
  }
}
```

## LLM09: What if I combine insulation and glazing?

Status: conditional; mode: deterministic; tools: feasibility.

This package is not confirmed feasible. Review the backend feasibility details before proceeding.

### Structured evidence

```json
{
  "feasibility": {
    "status": "available",
    "all_feasible": false,
    "rejected_retrofits": [],
    "conditional_retrofits": [
      "loft_insulation"
    ],
    "items": [
      {
        "retrofit": "loft_insulation",
        "status": "conditional",
        "reason": "roof_suitable_for_loft is unknown; confirm site suitability."
      },
      {
        "retrofit": "double_glazing",
        "status": "feasible",
        "reason": "Known installation and compatibility fields permit screening; survey confirmation may still be needed."
      }
    ],
    "reason": null
  }
}
```

## LLM10: What if I combine solar and a heat pump?

Status: conditional; mode: deterministic; tools: feasibility.

This package is not confirmed feasible. Review the backend feasibility details before proceeding.

### Structured evidence

```json
{
  "feasibility": {
    "status": "available",
    "all_feasible": false,
    "rejected_retrofits": [],
    "conditional_retrofits": [
      "heat_pump",
      "solar_panels"
    ],
    "items": [
      {
        "retrofit": "heat_pump",
        "status": "conditional",
        "reason": "heat_pump_compatible must be confirmed."
      },
      {
        "retrofit": "solar_panels",
        "status": "conditional",
        "reason": "roof_suitable_for_solar is unknown; confirm site suitability."
      }
    ],
    "reason": null
  }
}
```

## LLM11: What can I do with a £5000 budget?

Status: partial; mode: grounded_llm; tools: optimize.

Valuation estimate is unavailable. No supported projected EPC estimate; the existing valuation model uses recorded EPC as its energy feature.
Issues: Insulation is poor.
Issues: An old gas boiler is recorded.
Issues: Windows are single glazed.
Issues: No renewable contribution is recorded.
Issues: No smart energy controls are recorded.
Issues: Purchased-energy intensity exceeds the supplied benchmark.
Warnings: Score uses a synthetic reference benchmark, not an official consumption standard.
Warnings: Heating subtype is a disclosed synthetic modeling input, not survey evidence.
Warnings: Confirm alignment of the property snapshot and energy period; see source methodology.
Warnings: Energy data quality: synthetic.
Warnings: Score uses a synthetic reference benchmark, not an official consumption standard.
Warnings: Heating subtype is a disclosed synthetic modeling input, not survey evidence.
Warnings: Confirm alignment of the property snapshot and energy period; see source methodology.
Warnings: Physical input thermal_demand_kwh has no per-field source metadata.
Warnings: Physical input thermal_demand_scope has no per-field source metadata.
Warnings: Physical input space_heating_demand_kwh has no per-field source metadata.
Warnings: Physical input hot_water_demand_kwh has no per-field source metadata.
Warnings: Physical input base_appliance_electricity_kwh has no per-field source metadata.
Warnings: Physical input annual_electricity_demand_kwh has no per-field source metadata.
Warnings: Physical input gas_space_heating_kwh has no per-field source metadata.
Warnings: Physical input gas_hot_water_kwh has no per-field source metadata.
Warnings: Physical input electric_space_heating_kwh has no per-field source metadata.
Warnings: Physical input electric_hot_water_kwh has no per-field source metadata.
Warnings: Physical input boiler_efficiency has no per-field source metadata.
Warnings: Physical input solar_generation_kwh has no per-field source metadata.
Warnings: Physical input solar_self_consumed_kwh has no per-field source metadata.
Sources: Enumerate all retrofit subsets against the same baseline; require known feasibility and documented per-measure costs within the budget; rank by the selected objective with cost and retrofit IDs as deterministic tie-breakers. No weighted score is used.
Negative fuel savings mean increased consumption. Property-value associations do not prove a causal retrofit premium.

### Structured evidence

```json
{
  "property_id": "P00001",
  "status": "partial",
  "score": {
    "status": "available",
    "unrounded_score": 22.17012251643461,
    "classification": "Very poor",
    "components": [
      {
        "name": "energy_efficiency",
        "subscore": 20.0,
        "weight": 0.25,
        "contribution": 5.0,
        "evidence": {
          "energy_rating": "F"
        }
      },
      {
        "name": "consumption_intensity",
        "subscore": 45.850612582173056,
        "weight": 0.2,
        "contribution": 9.170122516434612,
        "evidence": {
          "intensity_kwh_m2_year": 202.95925675675676,
          "benchmark_kwh_m2_year": 128.212778,
          "benchmark_source": "Synthetic fixed reference model v1; not an official NEED benchmark"
        }
      },
      {
        "name": "insulation",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "insulation": "poor"
        }
      },
      {
        "name": "heating_system",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "heating_system": "old_gas_boiler"
        }
      },
      {
        "name": "windows",
        "subscore": 20.0,
        "weight": 0.1,
        "contribution": 2.0,
        "evidence": {
          "glazing": "single"
        }
      },
      {
        "name": "renewable_energy",
        "subscore": 0.0,
        "weight": 0.1,
        "contribution": 0.0,
        "evidence": {
          "renewable_contribution": "none"
        }
      },
      {
        "name": "smart_management",
        "subscore": 0.0,
        "weight": 0.05,
        "contribution": 0.0,
        "evidence": {
          "smart_controls": "none"
        }
      }
    ],
    "missing_fields": [],
    "methodology_version": "greenprint-score-v1",
    "baseline": 22,
    "after": 22,
    "after_status": "available",
    "after_components": [
      {
        "name": "energy_efficiency",
        "subscore": 20.0,
        "weight": 0.25,
        "contribution": 5.0,
        "evidence": {
          "energy_rating": "F"
        }
      },
      {
        "name": "consumption_intensity",
        "subscore": 45.850612582173056,
        "weight": 0.2,
        "contribution": 9.170122516434612,
        "evidence": {
          "intensity_kwh_m2_year": 202.95925675675676,
          "benchmark_kwh_m2_year": 128.212778,
          "benchmark_source": "Synthetic fixed reference model v1; not an official NEED benchmark"
        }
      },
      {
        "name": "insulation",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "insulation": "poor"
        }
      },
      {
        "name": "heating_system",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "heating_system": "old_gas_boiler"
        }
      },
      {
        "name": "windows",
        "subscore": 20.0,
        "weight": 0.1,
        "contribution": 2.0,
        "evidence": {
          "glazing": "single"
        }
      },
      {
        "name": "renewable_energy",
        "subscore": 0.0,
        "weight": 0.1,
        "contribution": 0.0,
        "evidence": {
          "renewable_contribution": "none"
        }
      },
      {
        "name": "smart_management",
        "subscore": 0.0,
        "weight": 0.05,
        "contribution": 0.0,
        "evidence": {
          "smart_controls": "none"
        }
      }
    ]
  },
  "issues": [
    "Insulation is poor.",
    "An old gas boiler is recorded.",
    "Windows are single glazed.",
    "No renewable contribution is recorded.",
    "No smart energy controls are recorded.",
    "Purchased-energy intensity exceeds the supplied benchmark."
  ],
  "warnings": [
    "Score uses a synthetic reference benchmark, not an official consumption standard.",
    "Heating subtype is a disclosed synthetic modeling input, not survey evidence.",
    "Confirm alignment of the property snapshot and energy period; see source methodology.",
    "Energy data quality: synthetic.",
    "Score uses a synthetic reference benchmark, not an official consumption standard.",
    "Heating subtype is a disclosed synthetic modeling input, not survey evidence.",
    "Confirm alignment of the property snapshot and energy period; see source methodology.",
    "Physical input thermal_demand_kwh has no per-field source metadata.",
    "Physical input thermal_demand_scope has no per-field source metadata.",
    "Physical input space_heating_demand_kwh has no per-field source metadata.",
    "Physical input hot_water_demand_kwh has no per-field source metadata.",
    "Physical input base_appliance_electricity_kwh has no per-field source metadata.",
    "Physical input annual_electricity_demand_kwh has no per-field source metadata.",
    "Physical input gas_space_heating_kwh has no per-field source metadata.",
    "Physical input gas_hot_water_kwh has no per-field source metadata.",
    "Physical input electric_space_heating_kwh has no per-field source metadata.",
    "Physical input electric_hot_water_kwh has no per-field source metadata.",
    "Physical input boiler_efficiency has no per-field source metadata.",
    "Physical input solar_generation_kwh has no per-field source metadata.",
    "Physical input solar_self_consumed_kwh has no per-field source metadata."
  ],
  "scenario_id": "04103bd4-577c-4b60-904d-9b7d8323e2a8",
  "reason": null,
  "feasibility": {
    "status": "available",
    "all_feasible": true,
    "rejected_retrofits": [],
    "conditional_retrofits": [],
    "items": [],
    "reason": null
  },
  "carbon": {
    "status": "available",
    "reduction_kg_co2e": 0.0,
    "factors": [
      {
        "fuel": "electricity",
        "kg_co2e_per_kwh": 0.13096,
        "source": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026",
        "source_year": 2026,
        "accounting_boundary": "Scope 2 location-based UK generation; excludes transmission/distribution and well-to-tank emissions",
        "version": "DESNZ-2026-flat-revised-2026-07-31"
      },
      {
        "fuel": "gas",
        "kg_co2e_per_kwh": 0.18231,
        "source": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026",
        "source_year": 2026,
        "accounting_boundary": "Scope 1 natural gas combustion; gross calorific value; excludes well-to-tank emissions",
        "version": "DESNZ-2026-flat-revised-2026-07-31"
      }
    ],
    "reason": null
  },
  "valuation": {
    "status": "unavailable",
    "reason": "No supported projected EPC estimate; the existing valuation model uses recorded EPC as its energy feature.",
    "value_before": null,
    "value_after": null,
    "uplift_range": null,
    "baseline_value_gbp": null,
    "after_value_gbp": null,
    "baseline_range_gbp": null,
    "after_range_gbp": null,
    "value_change_gbp": null,
    "value_change_range_gbp": null,
    "confidence_level": null,
    "method": null,
    "warnings": []
  },
  "assumptions": [],
  "installation_cost_gbp": 0.0,
  "annual_bill_savings_gbp": null,
  "bill_savings_reason": "Both electricity and gas tariffs are required to calculate annual bill savings.",
  "simple_payback_years": null,
  "payback_reason": "Both electricity and gas tariffs are required to calculate annual bill savings.",
  "carbon_savings_by_fuel_kg_co2e": {
    "electricity": 0.0,
    "gas": 0.0
  },
  "applied_retrofits": [],
  "versions": {
    "score": "greenprint-score-v1",
    "retrofit": "p4-carbon-package-adapter-v1",
    "simulation": "p4-carbon-package-adapter-v1"
  },
  "energy": {
    "baseline_electricity_kwh": 2997.41,
    "baseline_gas_kwh": 27040.56,
    "after_electricity_kwh": 2997.41,
    "after_gas_kwh": 27040.56,
    "electricity_savings_kwh": 0.0,
    "gas_savings_kwh": 0.0,
    "net_savings_kwh": 0.0,
    "improvement_percentage": 0.0
  },
  "package_decisions": [
    {
      "retrofits": [],
      "status": "eligible",
      "cost_gbp": 0,
      "objective_value": 0.0,
      "reason": "Feasible, calculable, and within the supplied budget."
    },
    {
      "retrofits": [
        "loft_insulation"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: loft_insulation"
    },
    {
      "retrofits": [
        "heat_pump"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: heat_pump"
    },
    {
      "retrofits": [
        "solar_panels"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: solar_panels"
    },
    {
      "retrofits": [
        "double_glazing"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: double_glazing"
    },
    {
      "retrofits": [
        "smart_thermostat"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: smart_thermostat"
    },
    {
      "retrofits": [
        "loft_insulation",
        "heat_pump"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: loft_insulation, heat_pump"
    },
    {
      "retrofits": [
        "loft_insulation",
        "solar_panels"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: loft_insulation, solar_panels"
    },
    {
      "retrofits": [
        "loft_insulation",
        "double_glazing"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: loft_insulation, double_glazing"
    },
    {
      "retrofits": [
        "loft_insulation",
        "smart_thermostat"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: loft_insulation, smart_thermostat"
    },
    {
      "retrofits": [
        "heat_pump",
        "solar_panels"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: heat_pump, solar_panels"
    },
    {
      "retrofits": [
        "heat_pump",
        "double_glazing"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: heat_pump, double_glazing"
    },
    {
      "retrofits": [
        "heat_pump",
        "smart_thermostat"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: heat_pump, smart_thermostat"
    },
    {
      "retrofits": [
        "solar_panels",
        "double_glazing"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: solar_panels, double_glazing"
    },
    {
      "retrofits": [
        "solar_panels",
        "smart_thermostat"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: solar_panels, smart_thermostat"
    },
    {
      "retrofits": [
        "double_glazing",
        "smart_thermostat"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: double_glazing, smart_thermostat"
    },
    {
      "retrofits": [
        "loft_insulation",
        "heat_pump",
        "solar_panels"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: loft_insulation, heat_pump, solar_panels"
    },
    {
      "retrofits": [
        "loft_insulation",
        "heat_pump",
        "double_glazing"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: loft_insulation, heat_pump, double_glazing"
    },
    {
      "retrofits": [
        "loft_insulation",
        "heat_pump",
        "smart_thermostat"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: loft_insulation, heat_pump, smart_thermostat"
    },
    {
      "retrofits": [
        "loft_insulation",
        "solar_panels",
        "double_glazing"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: loft_insulation, solar_panels, double_glazing"
    },
    {
      "retrofits": [
        "loft_insulation",
        "solar_panels",
        "smart_thermostat"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: loft_insulation, solar_panels, smart_thermostat"
    },
    {
      "retrofits": [
        "loft_insulation",
        "double_glazing",
        "smart_thermostat"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: loft_insulation, double_glazing, smart_thermostat"
    },
    {
      "retrofits": [
        "heat_pump",
        "solar_panels",
        "double_glazing"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: heat_pump, solar_panels, double_glazing"
    },
    {
      "retrofits": [
        "heat_pump",
        "solar_panels",
        "smart_thermostat"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: heat_pump, solar_panels, smart_thermostat"
    },
    {
      "retrofits": [
        "heat_pump",
        "double_glazing",
        "smart_thermostat"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: heat_pump, double_glazing, smart_thermostat"
    },
    {
      "retrofits": [
        "solar_panels",
        "double_glazing",
        "smart_thermostat"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: solar_panels, double_glazing, smart_thermostat"
    },
    {
      "retrofits": [
        "loft_insulation",
        "heat_pump",
        "solar_panels",
        "double_glazing"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: loft_insulation, heat_pump, solar_panels, double_glazing"
    },
    {
      "retrofits": [
        "loft_insulation",
        "heat_pump",
        "solar_panels",
        "smart_thermostat"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: loft_insulation, heat_pump, solar_panels, smart_thermostat"
    },
    {
      "retrofits": [
        "loft_insulation",
        "heat_pump",
        "double_glazing",
        "smart_thermostat"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: loft_insulation, heat_pump, double_glazing, smart_thermostat"
    },
    {
      "retrofits": [
        "loft_insulation",
        "solar_panels",
        "double_glazing",
        "smart_thermostat"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: loft_insulation, solar_panels, double_glazing, smart_thermostat"
    },
    {
      "retrofits": [
        "heat_pump",
        "solar_panels",
        "double_glazing",
        "smart_thermostat"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: heat_pump, solar_panels, double_glazing, smart_thermostat"
    },
    {
      "retrofits": [
        "loft_insulation",
        "heat_pump",
        "solar_panels",
        "double_glazing",
        "smart_thermostat"
      ],
      "status": "unavailable",
      "reason": "Documented installation cost missing for: loft_insulation, heat_pump, solar_panels, double_glazing, smart_thermostat"
    }
  ],
  "sources": [
    "Enumerate all retrofit subsets against the same baseline; require known feasibility and documented per-measure costs within the budget; rank by the selected objective with cost and retrofit IDs as deterministic tie-breakers. No weighted score is used."
  ]
}
```

## LLM12: Which package saves most carbon?

Status: clarification_required; mode: deterministic; tools: none.

Please specify the complete retrofit package, or a budget and optimization objective. For comparisons, submit each package separately.

### Structured evidence

```json
null
```

## LLM13: Which package saves most purchased energy?

Status: clarification_required; mode: deterministic; tools: none.

Please specify the complete retrofit package, or a budget and optimization objective. For comparisons, submit each package separately.

### Structured evidence

```json
null
```

## LLM14: Why does electricity use increase with a heat pump?

Status: success; mode: grounded_llm; tools: assessment.

Valuation estimate is unavailable. Synthetic training data cannot support real-world value uplift
Issues: Insulation is poor.
Issues: An old gas boiler is recorded.
Issues: Windows are single glazed.
Issues: No renewable contribution is recorded.
Issues: No smart energy controls are recorded.
Issues: Purchased-energy intensity exceeds the supplied benchmark.
Warnings: Score uses a synthetic reference benchmark, not an official consumption standard.
Warnings: Heating subtype is a disclosed synthetic modeling input, not survey evidence.
Warnings: Confirm alignment of the property snapshot and energy period; see source methodology.
Warnings: Energy data quality: synthetic.
Sources: Property dataset: synthetic; Data/csv/properties.csv and Data/csv/energy_usage.csv
Sources: Annual energy: synthetic; Sum of 12 monthly purchased-energy readings for 2025; incomplete fuel totals remain null
Sources: Synthetic fixed reference model v1; not an official NEED benchmark
Energy efficiency: subscore 20.0; weighted contribution 5.0 points. Recorded evidence: energy rating: F.
Consumption intensity: subscore 45.850612582173056; weighted contribution 9.170122516434612 points. Recorded evidence: intensity kwh m2 year: 202.95925675675676; benchmark kwh m2 year: 128.212778; benchmark source: Synthetic fixed reference model v1; not an official NEED benchmark.
Insulation: subscore 20.0; weighted contribution 3.0 points. Recorded evidence: insulation: poor.
Heating system: subscore 20.0; weighted contribution 3.0 points. Recorded evidence: heating system: old_gas_boiler.
Windows: subscore 20.0; weighted contribution 2.0 points. Recorded evidence: glazing: single.
Renewable energy: subscore 0.0; weighted contribution 0.0 points. Recorded evidence: renewable contribution: none.
Smart management: subscore 0.0; weighted contribution 0.0 points. Recorded evidence: smart controls: none.
Negative fuel savings mean increased consumption. Property-value associations do not prove a causal retrofit premium.

### Structured evidence

```json
{
  "property_id": "P00001",
  "status": "success",
  "score": {
    "status": "available",
    "unrounded_score": 22.17012251643461,
    "classification": "Very poor",
    "components": [
      {
        "name": "energy_efficiency",
        "subscore": 20.0,
        "weight": 0.25,
        "contribution": 5.0,
        "evidence": {
          "energy_rating": "F"
        }
      },
      {
        "name": "consumption_intensity",
        "subscore": 45.850612582173056,
        "weight": 0.2,
        "contribution": 9.170122516434612,
        "evidence": {
          "intensity_kwh_m2_year": 202.95925675675676,
          "benchmark_kwh_m2_year": 128.212778,
          "benchmark_source": "Synthetic fixed reference model v1; not an official NEED benchmark"
        }
      },
      {
        "name": "insulation",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "insulation": "poor"
        }
      },
      {
        "name": "heating_system",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "heating_system": "old_gas_boiler"
        }
      },
      {
        "name": "windows",
        "subscore": 20.0,
        "weight": 0.1,
        "contribution": 2.0,
        "evidence": {
          "glazing": "single"
        }
      },
      {
        "name": "renewable_energy",
        "subscore": 0.0,
        "weight": 0.1,
        "contribution": 0.0,
        "evidence": {
          "renewable_contribution": "none"
        }
      },
      {
        "name": "smart_management",
        "subscore": 0.0,
        "weight": 0.05,
        "contribution": 0.0,
        "evidence": {
          "smart_controls": "none"
        }
      }
    ],
    "missing_fields": [],
    "methodology_version": "greenprint-score-v1",
    "baseline": 22
  },
  "issues": [
    "Insulation is poor.",
    "An old gas boiler is recorded.",
    "Windows are single glazed.",
    "No renewable contribution is recorded.",
    "No smart energy controls are recorded.",
    "Purchased-energy intensity exceeds the supplied benchmark."
  ],
  "warnings": [
    "Score uses a synthetic reference benchmark, not an official consumption standard.",
    "Heating subtype is a disclosed synthetic modeling input, not survey evidence.",
    "Confirm alignment of the property snapshot and energy period; see source methodology.",
    "Energy data quality: synthetic."
  ],
  "energy": {
    "baseline_electricity_kwh": 2997.41,
    "baseline_gas_kwh": 27040.56
  },
  "carbon": {
    "status": "available",
    "electricity_kg_co2e": 392.5408136,
    "gas_kg_co2e": 4929.764493600001,
    "total_kg_co2e": 5322.3053072,
    "reason": null,
    "factors": {
      "electricity": {
        "fuel": "electricity",
        "kg_co2e_per_kwh": 0.13096,
        "source": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026",
        "source_year": 2026,
        "accounting_boundary": "Scope 2 location-based UK generation; excludes transmission/distribution and well-to-tank emissions",
        "version": "DESNZ-2026-flat-revised-2026-07-31"
      },
      "gas": {
        "fuel": "gas",
        "kg_co2e_per_kwh": 0.18231,
        "source": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026",
        "source_year": 2026,
        "accounting_boundary": "Scope 1 natural gas combustion; gross calorific value; excludes well-to-tank emissions",
        "version": "DESNZ-2026-flat-revised-2026-07-31"
      }
    }
  },
  "valuation": {
    "status": "unavailable",
    "reason": "Synthetic training data cannot support real-world value uplift",
    "value_before": null,
    "value_after": null,
    "uplift_range": null,
    "baseline_value_gbp": null,
    "after_value_gbp": null,
    "baseline_range_gbp": null,
    "after_range_gbp": null,
    "value_change_gbp": null,
    "value_change_range_gbp": null,
    "confidence_level": null,
    "method": null,
    "warnings": []
  },
  "sources": [
    "Property dataset: synthetic; Data/csv/properties.csv and Data/csv/energy_usage.csv",
    "Annual energy: synthetic; Sum of 12 monthly purchased-energy readings for 2025; incomplete fuel totals remain null",
    "Synthetic fixed reference model v1; not an official NEED benchmark"
  ]
}
```

## LLM15: Why are electricity savings negative?

Status: success; mode: grounded_llm; tools: assessment.

Baseline purchased electricity: 2997.41 kWh/year (backend estimate).
Baseline gas: 27040.56 kWh/year (backend estimate).
Valuation estimate is unavailable. Synthetic training data cannot support real-world value uplift
Issues: Purchased-energy intensity exceeds the supplied benchmark.
Warnings: Score uses a synthetic reference benchmark, not an official consumption standard.
Warnings: Heating subtype is a disclosed synthetic modeling input, not survey evidence.
Warnings: Confirm alignment of the property snapshot and energy period; see source methodology.
Warnings: Energy data quality: synthetic.
Sources: Property dataset: synthetic; Data/csv/properties.csv and Data/csv/energy_usage.csv
Sources: Annual energy: synthetic; Sum of 12 monthly purchased-energy readings for 2025; incomplete fuel totals remain null
Sources: Synthetic fixed reference model v1; not an official NEED benchmark
Energy efficiency: subscore 20.0; weighted contribution 5.0 points. Recorded evidence: energy rating: F.
Consumption intensity: subscore 45.850612582173056; weighted contribution 9.170122516434612 points. Recorded evidence: intensity kwh m2 year: 202.95925675675676; benchmark kwh m2 year: 128.212778; benchmark source: Synthetic fixed reference model v1; not an official NEED benchmark.
Insulation: subscore 20.0; weighted contribution 3.0 points. Recorded evidence: insulation: poor.
Heating system: subscore 20.0; weighted contribution 3.0 points. Recorded evidence: heating system: old_gas_boiler.
Windows: subscore 20.0; weighted contribution 2.0 points. Recorded evidence: glazing: single.
Renewable energy: subscore 0.0; weighted contribution 0.0 points. Recorded evidence: renewable contribution: none.
Smart management: subscore 0.0; weighted contribution 0.0 points. Recorded evidence: smart controls: none.
Negative fuel savings mean increased consumption. Property-value associations do not prove a causal retrofit premium.

### Structured evidence

```json
{
  "property_id": "P00001",
  "status": "success",
  "score": {
    "status": "available",
    "unrounded_score": 22.17012251643461,
    "classification": "Very poor",
    "components": [
      {
        "name": "energy_efficiency",
        "subscore": 20.0,
        "weight": 0.25,
        "contribution": 5.0,
        "evidence": {
          "energy_rating": "F"
        }
      },
      {
        "name": "consumption_intensity",
        "subscore": 45.850612582173056,
        "weight": 0.2,
        "contribution": 9.170122516434612,
        "evidence": {
          "intensity_kwh_m2_year": 202.95925675675676,
          "benchmark_kwh_m2_year": 128.212778,
          "benchmark_source": "Synthetic fixed reference model v1; not an official NEED benchmark"
        }
      },
      {
        "name": "insulation",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "insulation": "poor"
        }
      },
      {
        "name": "heating_system",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "heating_system": "old_gas_boiler"
        }
      },
      {
        "name": "windows",
        "subscore": 20.0,
        "weight": 0.1,
        "contribution": 2.0,
        "evidence": {
          "glazing": "single"
        }
      },
      {
        "name": "renewable_energy",
        "subscore": 0.0,
        "weight": 0.1,
        "contribution": 0.0,
        "evidence": {
          "renewable_contribution": "none"
        }
      },
      {
        "name": "smart_management",
        "subscore": 0.0,
        "weight": 0.05,
        "contribution": 0.0,
        "evidence": {
          "smart_controls": "none"
        }
      }
    ],
    "missing_fields": [],
    "methodology_version": "greenprint-score-v1",
    "baseline": 22
  },
  "issues": [
    "Insulation is poor.",
    "An old gas boiler is recorded.",
    "Windows are single glazed.",
    "No renewable contribution is recorded.",
    "No smart energy controls are recorded.",
    "Purchased-energy intensity exceeds the supplied benchmark."
  ],
  "warnings": [
    "Score uses a synthetic reference benchmark, not an official consumption standard.",
    "Heating subtype is a disclosed synthetic modeling input, not survey evidence.",
    "Confirm alignment of the property snapshot and energy period; see source methodology.",
    "Energy data quality: synthetic."
  ],
  "energy": {
    "baseline_electricity_kwh": 2997.41,
    "baseline_gas_kwh": 27040.56
  },
  "carbon": {
    "status": "available",
    "electricity_kg_co2e": 392.5408136,
    "gas_kg_co2e": 4929.764493600001,
    "total_kg_co2e": 5322.3053072,
    "reason": null,
    "factors": {
      "electricity": {
        "fuel": "electricity",
        "kg_co2e_per_kwh": 0.13096,
        "source": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026",
        "source_year": 2026,
        "accounting_boundary": "Scope 2 location-based UK generation; excludes transmission/distribution and well-to-tank emissions",
        "version": "DESNZ-2026-flat-revised-2026-07-31"
      },
      "gas": {
        "fuel": "gas",
        "kg_co2e_per_kwh": 0.18231,
        "source": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026",
        "source_year": 2026,
        "accounting_boundary": "Scope 1 natural gas combustion; gross calorific value; excludes well-to-tank emissions",
        "version": "DESNZ-2026-flat-revised-2026-07-31"
      }
    }
  },
  "valuation": {
    "status": "unavailable",
    "reason": "Synthetic training data cannot support real-world value uplift",
    "value_before": null,
    "value_after": null,
    "uplift_range": null,
    "baseline_value_gbp": null,
    "after_value_gbp": null,
    "baseline_range_gbp": null,
    "after_range_gbp": null,
    "value_change_gbp": null,
    "value_change_range_gbp": null,
    "confidence_level": null,
    "method": null,
    "warnings": []
  },
  "sources": [
    "Property dataset: synthetic; Data/csv/properties.csv and Data/csv/energy_usage.csv",
    "Annual energy: synthetic; Sum of 12 monthly purchased-energy readings for 2025; incomplete fuel totals remain null",
    "Synthetic fixed reference model v1; not an official NEED benchmark"
  ]
}
```

## LLM16: Can I install solar on an unsuitable roof?

Status: success; mode: grounded_llm; tools: assessment.

Baseline Green Home Score: 22 points (backend estimate).
Baseline purchased electricity: 2997.41 kWh/year (backend estimate).
Baseline gas: 27040.56 kWh/year (backend estimate).
Valuation estimate is unavailable. Synthetic training data cannot support real-world value uplift
Issues: Insulation is poor.
Issues: An old gas boiler is recorded.
Issues: Windows are single glazed.
Issues: No renewable contribution is recorded.
Issues: No smart energy controls are recorded.
Issues: Purchased-energy intensity exceeds the supplied benchmark.
Warnings: Score uses a synthetic reference benchmark, not an official consumption standard.
Warnings: Heating subtype is a disclosed synthetic modeling input, not survey evidence.
Warnings: Confirm alignment of the property snapshot and energy period; see source methodology.
Warnings: Energy data quality: synthetic.
Sources: Property dataset: synthetic; Data/csv/properties.csv and Data/csv/energy_usage.csv
Sources: Annual energy: synthetic; Sum of 12 monthly purchased-energy readings for 2025; incomplete fuel totals remain null
Sources: Synthetic fixed reference model v1; not an official NEED benchmark
Energy efficiency: subscore 20.0; weighted contribution 5.0 points. Recorded evidence: energy rating: F.
Consumption intensity: subscore 45.850612582173056; weighted contribution 9.170122516434612 points. Recorded evidence: intensity kwh m2 year: 202.95925675675676; benchmark kwh m2 year: 128.212778; benchmark source: Synthetic fixed reference model v1; not an official NEED benchmark.
Insulation: subscore 20.0; weighted contribution 3.0 points. Recorded evidence: insulation: poor.
Heating system: subscore 20.0; weighted contribution 3.0 points. Recorded evidence: heating system: old_gas_boiler.
Windows: subscore 20.0; weighted contribution 2.0 points. Recorded evidence: glazing: single.
Renewable energy: subscore 0.0; weighted contribution 0.0 points. Recorded evidence: renewable contribution: none.
Smart management: subscore 0.0; weighted contribution 0.0 points. Recorded evidence: smart controls: none.
Negative fuel savings mean increased consumption. Property-value associations do not prove a causal retrofit premium.

### Structured evidence

```json
{
  "property_id": "P00001",
  "status": "success",
  "score": {
    "status": "available",
    "unrounded_score": 22.17012251643461,
    "classification": "Very poor",
    "components": [
      {
        "name": "energy_efficiency",
        "subscore": 20.0,
        "weight": 0.25,
        "contribution": 5.0,
        "evidence": {
          "energy_rating": "F"
        }
      },
      {
        "name": "consumption_intensity",
        "subscore": 45.850612582173056,
        "weight": 0.2,
        "contribution": 9.170122516434612,
        "evidence": {
          "intensity_kwh_m2_year": 202.95925675675676,
          "benchmark_kwh_m2_year": 128.212778,
          "benchmark_source": "Synthetic fixed reference model v1; not an official NEED benchmark"
        }
      },
      {
        "name": "insulation",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "insulation": "poor"
        }
      },
      {
        "name": "heating_system",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "heating_system": "old_gas_boiler"
        }
      },
      {
        "name": "windows",
        "subscore": 20.0,
        "weight": 0.1,
        "contribution": 2.0,
        "evidence": {
          "glazing": "single"
        }
      },
      {
        "name": "renewable_energy",
        "subscore": 0.0,
        "weight": 0.1,
        "contribution": 0.0,
        "evidence": {
          "renewable_contribution": "none"
        }
      },
      {
        "name": "smart_management",
        "subscore": 0.0,
        "weight": 0.05,
        "contribution": 0.0,
        "evidence": {
          "smart_controls": "none"
        }
      }
    ],
    "missing_fields": [],
    "methodology_version": "greenprint-score-v1",
    "baseline": 22
  },
  "issues": [
    "Insulation is poor.",
    "An old gas boiler is recorded.",
    "Windows are single glazed.",
    "No renewable contribution is recorded.",
    "No smart energy controls are recorded.",
    "Purchased-energy intensity exceeds the supplied benchmark."
  ],
  "warnings": [
    "Score uses a synthetic reference benchmark, not an official consumption standard.",
    "Heating subtype is a disclosed synthetic modeling input, not survey evidence.",
    "Confirm alignment of the property snapshot and energy period; see source methodology.",
    "Energy data quality: synthetic."
  ],
  "energy": {
    "baseline_electricity_kwh": 2997.41,
    "baseline_gas_kwh": 27040.56
  },
  "carbon": {
    "status": "available",
    "electricity_kg_co2e": 392.5408136,
    "gas_kg_co2e": 4929.764493600001,
    "total_kg_co2e": 5322.3053072,
    "reason": null,
    "factors": {
      "electricity": {
        "fuel": "electricity",
        "kg_co2e_per_kwh": 0.13096,
        "source": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026",
        "source_year": 2026,
        "accounting_boundary": "Scope 2 location-based UK generation; excludes transmission/distribution and well-to-tank emissions",
        "version": "DESNZ-2026-flat-revised-2026-07-31"
      },
      "gas": {
        "fuel": "gas",
        "kg_co2e_per_kwh": 0.18231,
        "source": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026",
        "source_year": 2026,
        "accounting_boundary": "Scope 1 natural gas combustion; gross calorific value; excludes well-to-tank emissions",
        "version": "DESNZ-2026-flat-revised-2026-07-31"
      }
    }
  },
  "valuation": {
    "status": "unavailable",
    "reason": "Synthetic training data cannot support real-world value uplift",
    "value_before": null,
    "value_after": null,
    "uplift_range": null,
    "baseline_value_gbp": null,
    "after_value_gbp": null,
    "baseline_range_gbp": null,
    "after_range_gbp": null,
    "value_change_gbp": null,
    "value_change_range_gbp": null,
    "confidence_level": null,
    "method": null,
    "warnings": []
  },
  "sources": [
    "Property dataset: synthetic; Data/csv/properties.csv and Data/csv/energy_usage.csv",
    "Annual energy: synthetic; Sum of 12 monthly purchased-energy readings for 2025; incomplete fuel totals remain null",
    "Synthetic fixed reference model v1; not an official NEED benchmark"
  ]
}
```

## LLM17: Can I replace already triple glazed windows?

Status: success; mode: grounded_llm; tools: assessment.

Valuation estimate is unavailable. Synthetic training data cannot support real-world value uplift
Issues: Windows are single glazed.
Warnings: Score uses a synthetic reference benchmark, not an official consumption standard.
Warnings: Heating subtype is a disclosed synthetic modeling input, not survey evidence.
Warnings: Confirm alignment of the property snapshot and energy period; see source methodology.
Warnings: Energy data quality: synthetic.
Sources: Property dataset: synthetic; Data/csv/properties.csv and Data/csv/energy_usage.csv
Sources: Annual energy: synthetic; Sum of 12 monthly purchased-energy readings for 2025; incomplete fuel totals remain null
Sources: Synthetic fixed reference model v1; not an official NEED benchmark
Negative fuel savings mean increased consumption. Property-value associations do not prove a causal retrofit premium.

### Structured evidence

```json
{
  "property_id": "P00001",
  "status": "success",
  "score": {
    "status": "available",
    "unrounded_score": 22.17012251643461,
    "classification": "Very poor",
    "components": [
      {
        "name": "energy_efficiency",
        "subscore": 20.0,
        "weight": 0.25,
        "contribution": 5.0,
        "evidence": {
          "energy_rating": "F"
        }
      },
      {
        "name": "consumption_intensity",
        "subscore": 45.850612582173056,
        "weight": 0.2,
        "contribution": 9.170122516434612,
        "evidence": {
          "intensity_kwh_m2_year": 202.95925675675676,
          "benchmark_kwh_m2_year": 128.212778,
          "benchmark_source": "Synthetic fixed reference model v1; not an official NEED benchmark"
        }
      },
      {
        "name": "insulation",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "insulation": "poor"
        }
      },
      {
        "name": "heating_system",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "heating_system": "old_gas_boiler"
        }
      },
      {
        "name": "windows",
        "subscore": 20.0,
        "weight": 0.1,
        "contribution": 2.0,
        "evidence": {
          "glazing": "single"
        }
      },
      {
        "name": "renewable_energy",
        "subscore": 0.0,
        "weight": 0.1,
        "contribution": 0.0,
        "evidence": {
          "renewable_contribution": "none"
        }
      },
      {
        "name": "smart_management",
        "subscore": 0.0,
        "weight": 0.05,
        "contribution": 0.0,
        "evidence": {
          "smart_controls": "none"
        }
      }
    ],
    "missing_fields": [],
    "methodology_version": "greenprint-score-v1",
    "baseline": 22
  },
  "issues": [
    "Insulation is poor.",
    "An old gas boiler is recorded.",
    "Windows are single glazed.",
    "No renewable contribution is recorded.",
    "No smart energy controls are recorded.",
    "Purchased-energy intensity exceeds the supplied benchmark."
  ],
  "warnings": [
    "Score uses a synthetic reference benchmark, not an official consumption standard.",
    "Heating subtype is a disclosed synthetic modeling input, not survey evidence.",
    "Confirm alignment of the property snapshot and energy period; see source methodology.",
    "Energy data quality: synthetic."
  ],
  "energy": {
    "baseline_electricity_kwh": 2997.41,
    "baseline_gas_kwh": 27040.56
  },
  "carbon": {
    "status": "available",
    "electricity_kg_co2e": 392.5408136,
    "gas_kg_co2e": 4929.764493600001,
    "total_kg_co2e": 5322.3053072,
    "reason": null,
    "factors": {
      "electricity": {
        "fuel": "electricity",
        "kg_co2e_per_kwh": 0.13096,
        "source": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026",
        "source_year": 2026,
        "accounting_boundary": "Scope 2 location-based UK generation; excludes transmission/distribution and well-to-tank emissions",
        "version": "DESNZ-2026-flat-revised-2026-07-31"
      },
      "gas": {
        "fuel": "gas",
        "kg_co2e_per_kwh": 0.18231,
        "source": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026",
        "source_year": 2026,
        "accounting_boundary": "Scope 1 natural gas combustion; gross calorific value; excludes well-to-tank emissions",
        "version": "DESNZ-2026-flat-revised-2026-07-31"
      }
    }
  },
  "valuation": {
    "status": "unavailable",
    "reason": "Synthetic training data cannot support real-world value uplift",
    "value_before": null,
    "value_after": null,
    "uplift_range": null,
    "baseline_value_gbp": null,
    "after_value_gbp": null,
    "baseline_range_gbp": null,
    "after_range_gbp": null,
    "value_change_gbp": null,
    "value_change_range_gbp": null,
    "confidence_level": null,
    "method": null,
    "warnings": []
  },
  "sources": [
    "Property dataset: synthetic; Data/csv/properties.csv and Data/csv/energy_usage.csv",
    "Annual energy: synthetic; Sum of 12 monthly purchased-energy readings for 2025; incomplete fuel totals remain null",
    "Synthetic fixed reference model v1; not an official NEED benchmark"
  ]
}
```

## LLM18: What if roof suitability is unknown?

Status: clarification_required; mode: deterministic; tools: none.

Please specify the complete retrofit package, or a budget and optimization objective. For comparisons, submit each package separately.

### Structured evidence

```json
null
```

## LLM19: What if annual consumption is missing?

Status: clarification_required; mode: deterministic; tools: none.

Please specify the complete retrofit package, or a budget and optimization objective. For comparisons, submit each package separately.

### Structured evidence

```json
null
```

## LLM20: What if baseline energy is zero?

Status: clarification_required; mode: deterministic; tools: none.

Please specify the complete retrofit package, or a budget and optimization objective. For comparisons, submit each package separately.

### Structured evidence

```json
null
```

## LLM21: How is carbon calculated?

Status: success; mode: grounded_llm; tools: assessment.

Valuation estimate is unavailable. Synthetic training data cannot support real-world value uplift
Warnings: Score uses a synthetic reference benchmark, not an official consumption standard.
Warnings: Heating subtype is a disclosed synthetic modeling input, not survey evidence.
Warnings: Confirm alignment of the property snapshot and energy period; see source methodology.
Warnings: Energy data quality: synthetic.
Sources: Property dataset: synthetic; Data/csv/properties.csv and Data/csv/energy_usage.csv
Sources: Annual energy: synthetic; Sum of 12 monthly purchased-energy readings for 2025; incomplete fuel totals remain null
Sources: Synthetic fixed reference model v1; not an official NEED benchmark
Negative fuel savings mean increased consumption. Property-value associations do not prove a causal retrofit premium.

### Structured evidence

```json
{
  "property_id": "P00001",
  "status": "success",
  "score": {
    "status": "available",
    "unrounded_score": 22.17012251643461,
    "classification": "Very poor",
    "components": [
      {
        "name": "energy_efficiency",
        "subscore": 20.0,
        "weight": 0.25,
        "contribution": 5.0,
        "evidence": {
          "energy_rating": "F"
        }
      },
      {
        "name": "consumption_intensity",
        "subscore": 45.850612582173056,
        "weight": 0.2,
        "contribution": 9.170122516434612,
        "evidence": {
          "intensity_kwh_m2_year": 202.95925675675676,
          "benchmark_kwh_m2_year": 128.212778,
          "benchmark_source": "Synthetic fixed reference model v1; not an official NEED benchmark"
        }
      },
      {
        "name": "insulation",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "insulation": "poor"
        }
      },
      {
        "name": "heating_system",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "heating_system": "old_gas_boiler"
        }
      },
      {
        "name": "windows",
        "subscore": 20.0,
        "weight": 0.1,
        "contribution": 2.0,
        "evidence": {
          "glazing": "single"
        }
      },
      {
        "name": "renewable_energy",
        "subscore": 0.0,
        "weight": 0.1,
        "contribution": 0.0,
        "evidence": {
          "renewable_contribution": "none"
        }
      },
      {
        "name": "smart_management",
        "subscore": 0.0,
        "weight": 0.05,
        "contribution": 0.0,
        "evidence": {
          "smart_controls": "none"
        }
      }
    ],
    "missing_fields": [],
    "methodology_version": "greenprint-score-v1",
    "baseline": 22
  },
  "issues": [
    "Insulation is poor.",
    "An old gas boiler is recorded.",
    "Windows are single glazed.",
    "No renewable contribution is recorded.",
    "No smart energy controls are recorded.",
    "Purchased-energy intensity exceeds the supplied benchmark."
  ],
  "warnings": [
    "Score uses a synthetic reference benchmark, not an official consumption standard.",
    "Heating subtype is a disclosed synthetic modeling input, not survey evidence.",
    "Confirm alignment of the property snapshot and energy period; see source methodology.",
    "Energy data quality: synthetic."
  ],
  "energy": {
    "baseline_electricity_kwh": 2997.41,
    "baseline_gas_kwh": 27040.56
  },
  "carbon": {
    "status": "available",
    "electricity_kg_co2e": 392.5408136,
    "gas_kg_co2e": 4929.764493600001,
    "total_kg_co2e": 5322.3053072,
    "reason": null,
    "factors": {
      "electricity": {
        "fuel": "electricity",
        "kg_co2e_per_kwh": 0.13096,
        "source": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026",
        "source_year": 2026,
        "accounting_boundary": "Scope 2 location-based UK generation; excludes transmission/distribution and well-to-tank emissions",
        "version": "DESNZ-2026-flat-revised-2026-07-31"
      },
      "gas": {
        "fuel": "gas",
        "kg_co2e_per_kwh": 0.18231,
        "source": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026",
        "source_year": 2026,
        "accounting_boundary": "Scope 1 natural gas combustion; gross calorific value; excludes well-to-tank emissions",
        "version": "DESNZ-2026-flat-revised-2026-07-31"
      }
    }
  },
  "valuation": {
    "status": "unavailable",
    "reason": "Synthetic training data cannot support real-world value uplift",
    "value_before": null,
    "value_after": null,
    "uplift_range": null,
    "baseline_value_gbp": null,
    "after_value_gbp": null,
    "baseline_range_gbp": null,
    "after_range_gbp": null,
    "value_change_gbp": null,
    "value_change_range_gbp": null,
    "confidence_level": null,
    "method": null,
    "warnings": []
  },
  "sources": [
    "Property dataset: synthetic; Data/csv/properties.csv and Data/csv/energy_usage.csv",
    "Annual energy: synthetic; Sum of 12 monthly purchased-energy readings for 2025; incomplete fuel totals remain null",
    "Synthetic fixed reference model v1; not an official NEED benchmark"
  ]
}
```

## LLM22: What if emissions factors are unavailable?

Status: clarification_required; mode: deterministic; tools: none.

Please specify the complete retrofit package, or a budget and optimization objective. For comparisons, submit each package separately.

### Structured evidence

```json
null
```

## LLM23: How much will my property value rise?

Status: success; mode: grounded_llm; tools: assessment.

Valuation estimate is unavailable. Synthetic training data cannot support real-world value uplift
Warnings: Score uses a synthetic reference benchmark, not an official consumption standard.
Warnings: Heating subtype is a disclosed synthetic modeling input, not survey evidence.
Warnings: Confirm alignment of the property snapshot and energy period; see source methodology.
Warnings: Energy data quality: synthetic.
Sources: Property dataset: synthetic; Data/csv/properties.csv and Data/csv/energy_usage.csv
Sources: Annual energy: synthetic; Sum of 12 monthly purchased-energy readings for 2025; incomplete fuel totals remain null
Sources: Synthetic fixed reference model v1; not an official NEED benchmark
Negative fuel savings mean increased consumption. Property-value associations do not prove a causal retrofit premium.

### Structured evidence

```json
{
  "property_id": "P00001",
  "status": "success",
  "score": {
    "status": "available",
    "unrounded_score": 22.17012251643461,
    "classification": "Very poor",
    "components": [
      {
        "name": "energy_efficiency",
        "subscore": 20.0,
        "weight": 0.25,
        "contribution": 5.0,
        "evidence": {
          "energy_rating": "F"
        }
      },
      {
        "name": "consumption_intensity",
        "subscore": 45.850612582173056,
        "weight": 0.2,
        "contribution": 9.170122516434612,
        "evidence": {
          "intensity_kwh_m2_year": 202.95925675675676,
          "benchmark_kwh_m2_year": 128.212778,
          "benchmark_source": "Synthetic fixed reference model v1; not an official NEED benchmark"
        }
      },
      {
        "name": "insulation",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "insulation": "poor"
        }
      },
      {
        "name": "heating_system",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "heating_system": "old_gas_boiler"
        }
      },
      {
        "name": "windows",
        "subscore": 20.0,
        "weight": 0.1,
        "contribution": 2.0,
        "evidence": {
          "glazing": "single"
        }
      },
      {
        "name": "renewable_energy",
        "subscore": 0.0,
        "weight": 0.1,
        "contribution": 0.0,
        "evidence": {
          "renewable_contribution": "none"
        }
      },
      {
        "name": "smart_management",
        "subscore": 0.0,
        "weight": 0.05,
        "contribution": 0.0,
        "evidence": {
          "smart_controls": "none"
        }
      }
    ],
    "missing_fields": [],
    "methodology_version": "greenprint-score-v1",
    "baseline": 22
  },
  "issues": [
    "Insulation is poor.",
    "An old gas boiler is recorded.",
    "Windows are single glazed.",
    "No renewable contribution is recorded.",
    "No smart energy controls are recorded.",
    "Purchased-energy intensity exceeds the supplied benchmark."
  ],
  "warnings": [
    "Score uses a synthetic reference benchmark, not an official consumption standard.",
    "Heating subtype is a disclosed synthetic modeling input, not survey evidence.",
    "Confirm alignment of the property snapshot and energy period; see source methodology.",
    "Energy data quality: synthetic."
  ],
  "energy": {
    "baseline_electricity_kwh": 2997.41,
    "baseline_gas_kwh": 27040.56
  },
  "carbon": {
    "status": "available",
    "electricity_kg_co2e": 392.5408136,
    "gas_kg_co2e": 4929.764493600001,
    "total_kg_co2e": 5322.3053072,
    "reason": null,
    "factors": {
      "electricity": {
        "fuel": "electricity",
        "kg_co2e_per_kwh": 0.13096,
        "source": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026",
        "source_year": 2026,
        "accounting_boundary": "Scope 2 location-based UK generation; excludes transmission/distribution and well-to-tank emissions",
        "version": "DESNZ-2026-flat-revised-2026-07-31"
      },
      "gas": {
        "fuel": "gas",
        "kg_co2e_per_kwh": 0.18231,
        "source": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026",
        "source_year": 2026,
        "accounting_boundary": "Scope 1 natural gas combustion; gross calorific value; excludes well-to-tank emissions",
        "version": "DESNZ-2026-flat-revised-2026-07-31"
      }
    }
  },
  "valuation": {
    "status": "unavailable",
    "reason": "Synthetic training data cannot support real-world value uplift",
    "value_before": null,
    "value_after": null,
    "uplift_range": null,
    "baseline_value_gbp": null,
    "after_value_gbp": null,
    "baseline_range_gbp": null,
    "after_range_gbp": null,
    "value_change_gbp": null,
    "value_change_range_gbp": null,
    "confidence_level": null,
    "method": null,
    "warnings": []
  },
  "sources": [
    "Property dataset: synthetic; Data/csv/properties.csv and Data/csv/energy_usage.csv",
    "Annual energy: synthetic; Sum of 12 monthly purchased-energy readings for 2025; incomplete fuel totals remain null",
    "Synthetic fixed reference model v1; not an official NEED benchmark"
  ]
}
```

## LLM24: Does the model prove a causal premium?

Status: success; mode: grounded_llm; tools: assessment.

Valuation estimate is unavailable. Synthetic training data cannot support real-world value uplift
Warnings: Score uses a synthetic reference benchmark, not an official consumption standard.
Warnings: Heating subtype is a disclosed synthetic modeling input, not survey evidence.
Warnings: Confirm alignment of the property snapshot and energy period; see source methodology.
Warnings: Energy data quality: synthetic.
Sources: Property dataset: synthetic; Data/csv/properties.csv and Data/csv/energy_usage.csv
Sources: Annual energy: synthetic; Sum of 12 monthly purchased-energy readings for 2025; incomplete fuel totals remain null
Sources: Synthetic fixed reference model v1; not an official NEED benchmark
Negative fuel savings mean increased consumption. Property-value associations do not prove a causal retrofit premium.

### Structured evidence

```json
{
  "property_id": "P00001",
  "status": "success",
  "score": {
    "status": "available",
    "unrounded_score": 22.17012251643461,
    "classification": "Very poor",
    "components": [
      {
        "name": "energy_efficiency",
        "subscore": 20.0,
        "weight": 0.25,
        "contribution": 5.0,
        "evidence": {
          "energy_rating": "F"
        }
      },
      {
        "name": "consumption_intensity",
        "subscore": 45.850612582173056,
        "weight": 0.2,
        "contribution": 9.170122516434612,
        "evidence": {
          "intensity_kwh_m2_year": 202.95925675675676,
          "benchmark_kwh_m2_year": 128.212778,
          "benchmark_source": "Synthetic fixed reference model v1; not an official NEED benchmark"
        }
      },
      {
        "name": "insulation",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "insulation": "poor"
        }
      },
      {
        "name": "heating_system",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "heating_system": "old_gas_boiler"
        }
      },
      {
        "name": "windows",
        "subscore": 20.0,
        "weight": 0.1,
        "contribution": 2.0,
        "evidence": {
          "glazing": "single"
        }
      },
      {
        "name": "renewable_energy",
        "subscore": 0.0,
        "weight": 0.1,
        "contribution": 0.0,
        "evidence": {
          "renewable_contribution": "none"
        }
      },
      {
        "name": "smart_management",
        "subscore": 0.0,
        "weight": 0.05,
        "contribution": 0.0,
        "evidence": {
          "smart_controls": "none"
        }
      }
    ],
    "missing_fields": [],
    "methodology_version": "greenprint-score-v1",
    "baseline": 22
  },
  "issues": [
    "Insulation is poor.",
    "An old gas boiler is recorded.",
    "Windows are single glazed.",
    "No renewable contribution is recorded.",
    "No smart energy controls are recorded.",
    "Purchased-energy intensity exceeds the supplied benchmark."
  ],
  "warnings": [
    "Score uses a synthetic reference benchmark, not an official consumption standard.",
    "Heating subtype is a disclosed synthetic modeling input, not survey evidence.",
    "Confirm alignment of the property snapshot and energy period; see source methodology.",
    "Energy data quality: synthetic."
  ],
  "energy": {
    "baseline_electricity_kwh": 2997.41,
    "baseline_gas_kwh": 27040.56
  },
  "carbon": {
    "status": "available",
    "electricity_kg_co2e": 392.5408136,
    "gas_kg_co2e": 4929.764493600001,
    "total_kg_co2e": 5322.3053072,
    "reason": null,
    "factors": {
      "electricity": {
        "fuel": "electricity",
        "kg_co2e_per_kwh": 0.13096,
        "source": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026",
        "source_year": 2026,
        "accounting_boundary": "Scope 2 location-based UK generation; excludes transmission/distribution and well-to-tank emissions",
        "version": "DESNZ-2026-flat-revised-2026-07-31"
      },
      "gas": {
        "fuel": "gas",
        "kg_co2e_per_kwh": 0.18231,
        "source": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026",
        "source_year": 2026,
        "accounting_boundary": "Scope 1 natural gas combustion; gross calorific value; excludes well-to-tank emissions",
        "version": "DESNZ-2026-flat-revised-2026-07-31"
      }
    }
  },
  "valuation": {
    "status": "unavailable",
    "reason": "Synthetic training data cannot support real-world value uplift",
    "value_before": null,
    "value_after": null,
    "uplift_range": null,
    "baseline_value_gbp": null,
    "after_value_gbp": null,
    "baseline_range_gbp": null,
    "after_range_gbp": null,
    "value_change_gbp": null,
    "value_change_range_gbp": null,
    "confidence_level": null,
    "method": null,
    "warnings": []
  },
  "sources": [
    "Property dataset: synthetic; Data/csv/properties.csv and Data/csv/energy_usage.csv",
    "Annual energy: synthetic; Sum of 12 monthly purchased-energy readings for 2025; incomplete fuel totals remain null",
    "Synthetic fixed reference model v1; not an official NEED benchmark"
  ]
}
```

## LLM25: Why is valuation unavailable?

Status: success; mode: grounded_llm; tools: assessment.

Valuation estimate is unavailable. Synthetic training data cannot support real-world value uplift
Warnings: Score uses a synthetic reference benchmark, not an official consumption standard.
Warnings: Heating subtype is a disclosed synthetic modeling input, not survey evidence.
Warnings: Confirm alignment of the property snapshot and energy period; see source methodology.
Warnings: Energy data quality: synthetic.
Sources: Property dataset: synthetic; Data/csv/properties.csv and Data/csv/energy_usage.csv
Sources: Annual energy: synthetic; Sum of 12 monthly purchased-energy readings for 2025; incomplete fuel totals remain null
Sources: Synthetic fixed reference model v1; not an official NEED benchmark
Negative fuel savings mean increased consumption. Property-value associations do not prove a causal retrofit premium.

### Structured evidence

```json
{
  "property_id": "P00001",
  "status": "success",
  "score": {
    "status": "available",
    "unrounded_score": 22.17012251643461,
    "classification": "Very poor",
    "components": [
      {
        "name": "energy_efficiency",
        "subscore": 20.0,
        "weight": 0.25,
        "contribution": 5.0,
        "evidence": {
          "energy_rating": "F"
        }
      },
      {
        "name": "consumption_intensity",
        "subscore": 45.850612582173056,
        "weight": 0.2,
        "contribution": 9.170122516434612,
        "evidence": {
          "intensity_kwh_m2_year": 202.95925675675676,
          "benchmark_kwh_m2_year": 128.212778,
          "benchmark_source": "Synthetic fixed reference model v1; not an official NEED benchmark"
        }
      },
      {
        "name": "insulation",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "insulation": "poor"
        }
      },
      {
        "name": "heating_system",
        "subscore": 20.0,
        "weight": 0.15,
        "contribution": 3.0,
        "evidence": {
          "heating_system": "old_gas_boiler"
        }
      },
      {
        "name": "windows",
        "subscore": 20.0,
        "weight": 0.1,
        "contribution": 2.0,
        "evidence": {
          "glazing": "single"
        }
      },
      {
        "name": "renewable_energy",
        "subscore": 0.0,
        "weight": 0.1,
        "contribution": 0.0,
        "evidence": {
          "renewable_contribution": "none"
        }
      },
      {
        "name": "smart_management",
        "subscore": 0.0,
        "weight": 0.05,
        "contribution": 0.0,
        "evidence": {
          "smart_controls": "none"
        }
      }
    ],
    "missing_fields": [],
    "methodology_version": "greenprint-score-v1",
    "baseline": 22
  },
  "issues": [
    "Insulation is poor.",
    "An old gas boiler is recorded.",
    "Windows are single glazed.",
    "No renewable contribution is recorded.",
    "No smart energy controls are recorded.",
    "Purchased-energy intensity exceeds the supplied benchmark."
  ],
  "warnings": [
    "Score uses a synthetic reference benchmark, not an official consumption standard.",
    "Heating subtype is a disclosed synthetic modeling input, not survey evidence.",
    "Confirm alignment of the property snapshot and energy period; see source methodology.",
    "Energy data quality: synthetic."
  ],
  "energy": {
    "baseline_electricity_kwh": 2997.41,
    "baseline_gas_kwh": 27040.56
  },
  "carbon": {
    "status": "available",
    "electricity_kg_co2e": 392.5408136,
    "gas_kg_co2e": 4929.764493600001,
    "total_kg_co2e": 5322.3053072,
    "reason": null,
    "factors": {
      "electricity": {
        "fuel": "electricity",
        "kg_co2e_per_kwh": 0.13096,
        "source": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026",
        "source_year": 2026,
        "accounting_boundary": "Scope 2 location-based UK generation; excludes transmission/distribution and well-to-tank emissions",
        "version": "DESNZ-2026-flat-revised-2026-07-31"
      },
      "gas": {
        "fuel": "gas",
        "kg_co2e_per_kwh": 0.18231,
        "source": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026",
        "source_year": 2026,
        "accounting_boundary": "Scope 1 natural gas combustion; gross calorific value; excludes well-to-tank emissions",
        "version": "DESNZ-2026-flat-revised-2026-07-31"
      }
    }
  },
  "valuation": {
    "status": "unavailable",
    "reason": "Synthetic training data cannot support real-world value uplift",
    "value_before": null,
    "value_after": null,
    "uplift_range": null,
    "baseline_value_gbp": null,
    "after_value_gbp": null,
    "baseline_range_gbp": null,
    "after_range_gbp": null,
    "value_change_gbp": null,
    "value_change_range_gbp": null,
    "confidence_level": null,
    "method": null,
    "warnings": []
  },
  "sources": [
    "Property dataset: synthetic; Data/csv/properties.csv and Data/csv/energy_usage.csv",
    "Annual energy: synthetic; Sum of 12 monthly purchased-energy readings for 2025; incomplete fuel totals remain null",
    "Synthetic fixed reference model v1; not an official NEED benchmark"
  ]
}
```
