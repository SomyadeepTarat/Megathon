GREENPRINT AI
Megathon X: Singularity — Lloyds | Problem Statement 2
Product Requirements Document (PRD) + 24-Hour Execution Plan
Team: 5 developers
Development time: 24 hours
Resources: 2 Codex Plus accounts (GPT-6 Astra access), 3 ChatGPT Free accounts
Objective: Build a working, explainable AI platform that evaluates residential energy efficiency, recommends feasible retrofits, estimates savings and carbon reduction, and predicts indicative property-value changes.
1. Executive Summary
1.1 Product Vision
GreenPrint AI — Know your home's footprint. Build its greener future.
GreenPrint AI is an AI-powered home sustainability assessment platform designed for homeowners and financial institutions.
The platform analyzes property characteristics, energy consumption, and existing infrastructure to produce a Green Home Score from 0 to 100.
Beyond identifying inefficiencies, it recommends financially and technically suitable improvements and estimates their impact on:
- Annual electricity consumption
- Annual gas consumption
- Carbon emissions
- Energy expenditure
- Property value
- Overall energy efficiency
Users can interact with an AI assistant to understand recommendations and explore different retrofit scenarios.
Our differentiator
Rather than building another generic energy-efficiency calculator, we will develop a retrofit decision-support engine.
The system will let users answer questions such as:
"I have a £7,000 budget. Which improvements should I prioritize?"

"What happens if I install solar panels but keep my gas boiler?"

"Is insulation more beneficial than replacing my windows?"

"How will installing a heat pump affect my electricity bill?"

The system will calculate the actual estimates through a deterministic and model-based pipeline. The LLM will only explain the outputs.
This distinction is essential because the problem statement explicitly prohibits LLM-generated numerical estimates.
1.2 Product Scope
We will implement six essential modules.
Module	Purpose	Implementation
Green Home Score	Calculate efficiency score	Deterministic weighted scoring
Efficiency Detector	Identify poorly performing homes	Rules + intensity benchmarks
Retrofit Engine	Recommend and prioritize improvements	Feasibility rules + optimization
Energy & Carbon Engine	Estimate per-fuel savings and emissions	Documented simulation + emission factors
Property Valuation	Estimate indicative value changes	Regression with uncertainty range
AI Sustainability Advisor	Explain results and handle scenarios	LLM with structured tool outputs


A seventh component, the customer dashboard, integrates these modules into the application.
1.3 What We Should Actually Build in 24 Hours
We should not attempt to train a separate sophisticated neural network for every requirement.
That would introduce unnecessary complexity without necessarily improving evaluation results.
Instead:
Use deterministic, explainable calculations where the problem statement requires them, ML where historical relationships must be learned, and GenAI where natural-language interaction adds value.
Recommended implementation:
Requirement	Our approach
Green Home Score	Weighted, monotonic scoring algorithm
Poor-home detection	Score threshold + issue detection
Retrofit feasibility	Rule-based decision engine
Retrofit prioritization	Budget-aware scenario search
Energy savings	Sequential energy simulation
Carbon reduction	Government emissions factors
Property-value estimation	HistGradientBoosting / XGBoost regression
AI explanations	Grounded LLM with strict output validation
Frontend	Next.js dashboard
Backend	Python FastAPI
Database	SQLite
Visualizations	Recharts


This approach is achievable within 24 hours and aligns with the evaluation criteria.
2. Team Structure and Responsibility Distribution
The most important organizational decision is how to allocate the two Codex Plus accounts.
Codex access should be assigned according to integration complexity, not simply the amount of code required.
The architecture and backend work require extensive cross-file changes, while the data engineering and modeling work can be developed independently with normal Python tools.
2.1 Recommended Team Assignment
Member	Role	Primary responsibility	Tool allocation
Person 1	Technical Lead + Backend Engineer	Architecture, backend, scoring, API integration	Codex Plus #1
Person 2	Frontend Lead + AI Engineer	Dashboard, AI assistant, scenario interaction	Codex Plus #2
Person 3	Data Engineer	Dataset preparation, synthetic generation, data validation	ChatGPT Free
Person 4	Energy & Retrofit Engineer	Retrofit recommendations, energy savings, carbon, optimization	ChatGPT Free
Person 5	ML Engineer + Evaluation Lead	Property valuation, model training, evaluation, reports	ChatGPT Free


Each person should own a self-contained module.
The two Codex users should work in areas where AI-assisted codebase navigation, debugging, and integration offer the greatest advantage.
The other three should receive narrowly defined modules with explicit input/output contracts.
Important: People 3–5 do not need Codex subscriptions to work effectively. They can use VS Code, Python, local tests, GitHub, and ChatGPT Free for assistance.
2.2 Workload Distribution
Member	Estimated development time	Integration/testing
Person 1	14 hours	6 hours
Person 2	14 hours	6 hours
Person 3	12 hours	8 hours
Person 4	15 hours	5 hours
Person 5	14 hours	6 hours


The remaining four hours per person are reserved for breaks, reviews, presentation preparation, and contingency.
These are effort budgets, not separate sequential phases. Everyone works in parallel.
3. Proposed System Architecture
                  GREENPRINT AI
                       |
                 Next.js Frontend
                       |
                 FastAPI Backend
                       |
        +--------------+--------------+
        |              |              |
   Property Data   Energy Usage   Retrofit Data
        |              |              |
        +--------------+--------------+
                       |
                Data Validation
                       |
                Feature Engineering
                       |
          +------------+------------+
          |                         |
    GREEN HOME SCORE         EFFICIENCY DETECTOR
          |                         |
          +------------+------------+
                       |
                 RETROFIT ENGINE
                       |
             Feasibility Filtering
                       |
              Priority Optimization
                       |
               SCENARIO ENGINE
                       |
         +-------------+-------------+
         |             |             |
    Energy Model   Carbon Model   Value Model
         |             |             |
         +-------------+-------------+
                       |
                Structured Results
                       |
                LLM Explanation
                       |
              Customer Dashboard

Architectural principle
The numerical engines must function independently of the LLM.
Even if the AI assistant is unavailable, the platform must still calculate:
- Green Home Score
- Efficiency classification
- Retrofit recommendations
- Electricity and gas savings
- Carbon reduction
- Indicative property-value impact, when supported
This guarantees the core demo can work without a paid AI API.
4. Technology Stack
Layer	Technology	Reason
Frontend	Next.js + TypeScript	Responsive, modern UI
Styling	Tailwind CSS	Rapid development
Components	shadcn/ui	Accessible components
Charts	Recharts	Score and savings visualization
Backend	FastAPI	Fast Python integration
Validation	Pydantic	Strict schema enforcement
Database	SQLite	Zero infrastructure setup
Data processing	Pandas + NumPy	Data preparation
ML	Scikit-learn	Regression and evaluation
Optional ML	XGBoost	Strong tabular baseline challenger
Energy simulation	Python	Deterministic calculations
LLM	Configurable model API or local Ollama	Grounded explanations
Testing	Pytest	Automated validation
Version control	GitHub	Parallel development
Deployment	Vercel + compatible Python host, if available	Optional demo hosting


Recommendation: Run frontend and backend locally during development. Do not risk the final submission by making cloud deployment a prerequisite.
The entire platform must support a local demo.
5. Functional Requirements
FR-01: Property Input
Users must be able to select a sample property or enter their property's characteristics.
Required inputs:
Field	Type	Example
Property ID	String	P10001
Property type	Enum	Detached
Region	String	Greater London
Floor area	Number	120 m²
Property age	Number	35 years
Bedrooms	Integer	3
Energy rating	Enum	A–G
Annual electricity	Number	4,800 kWh
Annual gas	Number	12,000 kWh
Insulation	Enum	Poor / Average / Good
Heating system	Enum	Gas boiler / Heat pump / Electric
Glazing	Enum	Single / Double / Triple
Solar panels	Boolean	False
Smart thermostat	Boolean	False
Current property value	Number	£350,000


The interface should clearly distinguish:
1. User-provided values
2. Imported values
3. Estimated or imputed values
Missing energy consumption must not automatically become zero.
If only monthly readings are available, the backend should annualize them using a documented method and indicate whether the result is based on a complete year or partial coverage.
Acceptance criteria
A user can select a demo property, view its characteristics, modify them, and request an assessment.
Invalid inputs must produce clear error messages.
6. Green Home Score Engine
Owner: Person 1
This is one of the most important modules because the scoring methodology has strict requirements.
6.1 Scoring Formula
\[
S=0.25E+0.20C+0.15I+0.15H+0.10W+0.10R+0.05M
\]
Where:
- \(E\): Energy efficiency rating score
- \(C\): Consumption intensity score
- \(I\): Insulation score
- \(H\): Heating system score
- \(W\): Windows score
- \(R\): Renewable energy score
- \(M\): Smart energy management score
Every component ranges from 0 to 100.
Proposed mappings
These mappings are team-defined modeling assumptions, not UK government standards. They must be included in the methodology documentation.
Energy efficiency (25%)
EPC Rating	Score
A	100
B	85
C	70
D	55
E	40
F	20
G	0


If the actual EPC numerical efficiency rating is available, a documented mapping based on that measure may be more informative.
Energy consumption intensity (20%)
Calculate:
\[
ECI=\frac{E_{\text{electricity}}+E_{\text{gas}}}{\text{Floor Area}}
\]
Units: kWh/m²/year.
Use a benchmark specific to property type and, where supported by reference data, relevant regional characteristics.
Define:
\[
r=\frac{ECI}{ECI_{\text{benchmark}}}
\]
A proposed continuous score is:
\[
C=\operatorname{clip}(100-50(r-0.5),0,100)
\]
This is monotonic: increasing consumption intensity can never increase the score.
The benchmark must come from a documented dataset or methodology rather than a fabricated national average.
Energy efficiency and consumption intensity are deliberately separated: the former uses the recorded EPC rating, while the latter uses metered purchased energy relative to area.
Insulation (15%)
State	Score
Poor	20
Average	60
Good	100


Heating system (15%)
Example team-defined mapping:
System	Score
Old gas boiler	20
Modern gas boiler	50
Direct electric resistance heating	60
Air-source heat pump	90
Ground-source heat pump	100


These values should be treated as a simplified sustainability proxy rather than universal rankings. Heating efficiency depends on system performance, climate, and energy source; a refined mapping should consider those factors.
Windows and glazing (10%)
State	Score
Single	20
Double	75
Triple	100


Renewable energy (10%)
State	Score
No renewable system	0
Solar installed, limited contribution	50
Solar installed, substantial contribution	100


When solar generation data is available, the score should be based on a documented bounded generation or self-consumption measure.
Smart energy management (5%)
State	Score
No smart controls	0
Basic programmable controls	50
Smart thermostat / advanced controls	100


Score reporting
Calculate the weighted contributions without premature rounding.
Round only the final score.
Classification:
Score	Category
80–100	Highly efficient
65–79	Good
50–64	Moderate
30–49	Poor
0–29	Very poor


Explainability requirement
The backend must return each component's:
- Raw sub-score
- Weight
- Weighted contribution
- Evidence/input used
Example:
{
  "score": 38,
  "classification": "Poor",
  "components": [
    {
      "name": "insulation",
      "subscore": 20,
      "weight": 0.15,
      "contribution": 3.0
    }
  ]
}

The full response must contain all seven components.
Important edge case
If required data is unavailable, do not silently assume the worst condition.
Return a missing-data indicator, supported fallback, or an unavailable assessment when the available information is insufficient.
7. Poor-Home Detection
Owner: Person 1, with outputs from Person 4
A property is flagged when:
\[
S<50
\]
The system must also identify its main deficiencies.
Examples:
- Very high metered energy intensity
- Insufficient insulation
- Inefficient heating
- Single-pane glazing
- No renewable generation
- Lack of energy management controls
The system should rank homes by estimated improvement potential, not merely by their current score.
\[
IP=100\frac{E_{\text{baseline}}-E_{\text{after}}}
{E_{\text{baseline}}}
\]
Here, \(E\) represents annual purchased electricity plus annual gas consumption.
Improvement potential should be calculated using the complete feasible retrofit package for each property.
If baseline purchased energy is zero or unknown, improvement potential must be marked unavailable.
Acceptance criteria
The user can compare multiple demo homes, see which are inefficient, and understand which offer the largest potential reduction in purchased energy.
8. Retrofit Recommendation Engine
Owner: Person 4
This is the core decision-making component.
The engine should recommend improvements based on:
1. Technical feasibility
2. Current property conditions
3. Estimated energy reduction
4. Estimated carbon reduction
5. Indicative installation cost
6. User budget
7. Interactions with other retrofits
8.1 Supported Retrofit Types
For the MVP, support five options.
Retrofit	Basic eligibility	Modeling approach
Loft insulation	Insulation below good; suitable roof	Reduces space-heating demand
Heat pump	Compatible property and heating configuration	Replaces gas heating with electric heat
Solar panels	Suitable roof and installation conditions	Reduces purchased grid electricity
Double glazing	Single-glazed windows	Reduces space-heating demand
Smart thermostat	No advanced controls; compatible heating	Reduces heating energy demand


The input schema should contain or derive the relevant eligibility fields.
If roof suitability, heat-pump feasibility, or control compatibility is unknown, mark the recommendation conditional rather than definitively feasible.
8.2 Retrofit Suitability
Each recommendation should include:
{
  "retrofit": "loft_insulation",
  "feasible": true,
  "suitability": "High",
  "estimated_cost_gbp": 1800,
  "reason": "The property has poor loft insulation.",
  "priority": 1
}

The example cost is illustrative only. The implemented catalogue needs documented sources, dates, assumptions, and relevant property-size adjustments.
Do not use arbitrary numeric thresholds to imply that a retrofit is universally suitable.
8.3 Retrofit Interaction Logic
This is critical.
Do not simply add percentage savings together.
Example:
Assume baseline space-heating demand is:
\[
Q_0=12,000\text{ kWh}
\]
Loft insulation reduces demand by an assumed 15%:
\[
Q_1=12,000(0.85)=10,200
\]
Double glazing then reduces the remaining demand by an assumed 10%:
\[
Q_2=10,200(0.90)=9,180
\]
Combined reduction:
\[
12,000-9,180=2,820\text{ kWh}
\]
This example assumes that the heating-demand percentages apply sequentially to the same underlying demand.
It is not an estimate of purchased fuel savings until heating-system efficiency is considered.
Heat pump modeling
A heat pump must be modeled as a fuel substitution.
For example, replacing gas heating may:
- Significantly reduce gas consumption
- Increase electricity consumption
- Reduce total purchased energy
- Reduce carbon emissions
Use an explicit thermal-demand and heating-efficiency model.
\[
E_{\text{heat pump}}=\frac{Q_{\text{thermal}}}{SCOP}
\]
Where SCOP is the seasonal coefficient of performance.
For an existing boiler:
\[
E_{\text{gas,heating}}
=\frac{Q_{\text{thermal}}}{\eta_{\text{boiler}}}
\]
A retrofit package must preserve non-heating electricity and gas loads.
Solar modeling
Solar panels reduce purchased grid imports.
They must not reduce the modeled underlying electricity demand.
\[
E_{\text{grid,after}}
=
\max(0,E_{\text{demand,after}}-E_{\text{solar,self-consumed}})
\]
Solar self-consumption must be bounded by demand and plausible generation. Exported electricity should be tracked separately where modeled.
8.4 Budget-Aware Recommendation
The user can enter a budget, such as £5,000.
The engine should evaluate feasible retrofit combinations within that budget.
For five retrofit options, exhaustive subset enumeration is entirely practical.
For each package, calculate:
- Installation cost
- Purchased electricity after retrofits
- Gas consumption after retrofits
- Total energy savings
- Carbon reduction
- Estimated annual bill savings
- Simple payback, if cost and tariff assumptions are available
Then rank packages using a documented objective.
For example:
Maximize estimated annual carbon reduction subject to budget and feasibility constraints.
The user should also be able to choose an alternative objective such as maximum energy reduction or shortest simple payback.
This makes the platform substantially more useful than a static recommendation list.
9. Energy Savings and Carbon Engine
Owner: Person 4
9.1 Required Outputs
Every scenario must report:
Metric	Required
Baseline electricity	Yes
Baseline gas	Yes
Post-retrofit electricity	Yes
Post-retrofit gas	Yes
Electricity savings	Yes
Gas savings	Yes
Net purchased-energy savings	Yes
Percentage reduction	Yes
Annual carbon reduction	Yes


Savings must follow the convention:
\[
\Delta E_f=E_{f,\text{baseline}}-E_{f,\text{after}}
\]
An increase in electricity consumption must appear as a negative electricity saving.
9.2 Carbon Formula
\[
\Delta C=
\Delta E_{\text{electricity}}EF_{\text{electricity}}
+
\Delta E_{\text{gas}}EF_{\text{gas}}
\]
Carbon calculations must use documented fuel-specific conversion factors.
The UK's Department for Energy Security and Net Zero publishes 2026 greenhouse gas conversion factors, including methodology and updated machine-readable data. The official 2026 flat file was corrected in July 2026. GOV.UK
Implementation requirement: Extract the appropriate 2026 UK grid-electricity and natural-gas factors, record their exact units and accounting boundary, and include them in a versioned CSV.
Do not hardcode unverified emission factors.
9.3 Output Structure
{
  "baseline": {
    "electricity_kwh": 4800,
    "gas_kwh": 12000
  },
  "after": {
    "electricity_kwh": 6000,
    "gas_kwh": 3000
  },
  "savings": {
    "electricity_kwh": -1200,
    "gas_kwh": 9000,
    "net_kwh": 7800,
    "percentage": 46.43
  },
  "carbon": {
    "reduction_kg_co2e": null,
    "factor_source": "UK Government 2026"
  }
}

These figures are an illustrative API example, not a prediction for a real property. The actual engine must calculate every field, including carbon once the documented emissions factors are loaded.
Critical acceptance test
Installing a heat pump must be capable of producing:
Electricity savings: Negative
Gas savings: Positive
Net energy savings: Positive
Carbon savings: Calculated independently

This is specifically relevant to the problem statement's scenario-based evaluation.
10. Property Valuation Model
Owner: Person 5
The challenge expects a potential property-value impact expressed as a range.
This is an appropriate place to apply machine learning.
10.1 Recommended ML Approach
Use a regression model to estimate property value based on:
- Region
- Property type
- Floor area
- Bedrooms
- Property age
- Sale-period or market-condition features
- EPC rating
- Relevant property characteristics
Recommended models
Start with:
1. Baseline: Ridge regression or median-by-region/property-type predictor.
2. Main model: HistGradientBoostingRegressor.
3. Optional challenger: XGBoost.
Train and validate using available property-sale data.
The simplest validated model should be preferred if the more complex model does not materially outperform it.
10.2 Data Sources
Recommended:
HM Land Registry Price Paid Data
The dataset includes property transactions in England and Wales and can be downloaded in yearly files. The published data has licensing and attribution requirements. GOV.UK
EPC Data
The official EPC service provides building-energy records for England and Wales, including bulk CSV access and a developer API. Access to downloads requires GOV.UK sign-in. Energy Performance Data
Important data limitation
Standard Land Registry transactions and EPC records are not guaranteed to be directly joinable using the fields available in the downloaded files.
Do not waste half the hackathon trying to construct a perfect national dataset.
For this MVP, use a defensible combination of:
- A manageable public property-sales dataset
- Available energy-rating information
- Documented synthetic examples where necessary
Maintain provenance for each record and feature.
Never present fabricated property-price relationships as real observations.
10.3 Value-Uplift Estimation
The ideal method is counterfactual prediction.
\[
V_{\text{before}}=f(X_{\text{before}})
\]
\[
V_{\text{after}}=f(X_{\text{after}})
\]
Hold location, area, type, age and market conditions constant.
Only change supported energy-efficiency features.
\[
\Delta V=V_{\text{after}}-V_{\text{before}}
\]
Then estimate a range.
Important: The range should come from a documented uncertainty method, such as held-out residual calibration or conformal prediction. It must not be an arbitrary ±5% added to the prediction.
If the property-value model has no credible energy-efficiency signal, it must not manufacture one.
A perfectly acceptable output is:
"Insufficient evidence to estimate a reliable property-value uplift."

If the dataset is primarily synthetic or contains insufficient comparable transactions, label the prediction as illustrative or indicative, not a proven market premium.
10.4 Evaluation
Track:
- MAE
- RMSE
- R²
- Baseline comparison
- Interval coverage on held-out data
- Interval width
- Sample counts
When possible, use an earlier-period training set and a later-period test set to evaluate generalization across changing market conditions.
Do not use the latest sale price as a predictor of that same sale.
11. AI Sustainability Advisor
Owner: Person 2
The AI assistant is a major UX and GenAI scoring opportunity.
However, it must obey one foundational rule:
The LLM explains calculations. It never creates calculations.
11.1 User Questions
The assistant should answer:
- Why is my Green Home Score low?
- Which improvement should I prioritize?
- What if I install solar panels?
- What if I have only £5,000?
- What if I replace my gas boiler with a heat pump?
- What combination reduces carbon emissions the most?
- How much could my property value change?
11.2 What-if Execution Flow
User question
     |
LLM extracts requested scenario
     |
Structured scenario validation
     |
Feasibility verification
     |
Backend recalculates energy
     |
Backend recalculates carbon
     |
Backend recomputes score where supported
     |
Property-value model reruns
     |
Verified numerical results
     |
LLM generates explanation

Example
User:
What happens if I install solar panels and a heat pump?

LLM extracts:
{
  "intent": "simulate_retrofit",
  "retrofits": [
    "solar_panels",
    "heat_pump"
  ]
}

Backend:
1. Checks technical feasibility.
2. Simulates the fuel changes.
3. Recalculates energy and carbon.
4. Updates the applicable scoring inputs.
5. Reruns property-value estimation where supported.
6. Returns structured numerical outputs.
Only then does the LLM construct the response.
11.3 Prompt Requirements
The system prompt must enforce:
You are GreenPrint AI, a residential energy
efficiency explanation assistant.

You may explain only numerical estimates returned
by the provided calculation and modeling tools.

You must never calculate, invent, interpolate,
or modify Green Home Scores, energy savings,
carbon reductions, costs, or property values.

For what-if questions, request a new simulation
before explaining any proposed scenario.

If required data or a calculation is unavailable,
state that the estimate is unavailable.

Do not recommend a retrofit marked infeasible.

Distinguish between estimates, observed data,
and verified facts.

Never describe indicative property-value
relationships as proven causal effects.

11.4 Grounding and Validation
The application should preferably render the numerical figures directly from backend responses.
The LLM should generate only explanatory text.
Implement a basic verification layer that rejects unsupported numerical claims or replaces the explanation with a deterministic template.
This ensures the application is still usable if:
- The LLM produces an incorrect response.
- API access fails.
- Free-tier limits are reached.
- An explanation times out.
11.5 LLM Selection
You do not need to use GPT-6 Astra as the production LLM.
Use Codex Plus for implementation assistance.
For runtime inference, choose an accessible API or local model with sufficient reliability for short structured explanations.
Provide an environment variable:
LLM_PROVIDER=
LLM_MODEL=
LLM_API_KEY=

Do not couple the product to an account-specific Codex model entitlement.
The fallback should always be deterministic explanations.
12. Data Engineering Strategy
Owner: Person 3
Data quality is a significant part of the judging criteria, so this workstream cannot be treated as simply generating random CSV files.
12.1 Data Strategy for 24 Hours
Use a hybrid dataset.
Dataset	Source	Purpose
EPC properties	UK government	Building characteristics and ratings
NEED consumption tables	UK government	Energy-consumption benchmarks
Property sales	HM Land Registry	Property-value regression
Synthetic energy records	Generated	Complete property-level scenarios
Retrofit catalogue	Documented assumptions and sources	Feasibility and impacts
Emissions factors	UK government 2026	Carbon calculations


The NEED tables provide household energy-consumption statistics across property characteristics, which can support consumption benchmarks. They do not constitute individual-property meter readings. GOV.UK
Recommended dataset size
For a 24-hour prototype:
- 1,000–3,000 synthetic properties
- 12 monthly electricity and gas records per property
- 50–100 carefully constructed scenario test cases
- A manageable public-property dataset for valuation training
- 5–10 curated demonstration properties
Avoid downloading huge datasets simply to claim a large training set.
A clean, properly documented dataset is much more valuable.
12.2 Synthetic Data Generation
Synthetic data must reflect plausible physical relationships.
For example:
A poorly insulated property should generally have higher space-heating demand than an otherwise comparable well-insulated property.
A heat pump should reduce gas consumption while potentially increasing electricity consumption.
Solar panels should reduce grid imports rather than underlying household demand.
A larger home may consume more energy overall without necessarily having worse energy intensity.
Data generation structure
Property characteristics
          |
    Floor area / age
          |
   Thermal demand estimate
          |
 Insulation and glazing effects
          |
 Heating-system efficiency
          |
 Electricity + gas consumption
          |
 Solar generation / self-consumption
          |
 Monthly variation
          |
 Synthetic energy readings

Document all generation equations, assumptions, parameter ranges, and random seeds.
Do not generate arbitrary random labels for savings, feasibility, or value uplift.
12.3 Dataset Schema
Create the following tables:
properties
---------
property_id
customer_id
property_type
region
age
floor_area
bedrooms
energy_rating
heating
insulation
glazing
solar
smart_controls
current_value_estimate

energy_usage
------------
property_id
month
electricity_kwh
gas_kwh
reading_status

retrofit_catalogue
------------------
retrofit_id
name
minimum_cost_gbp
maximum_cost_gbp
applicability
impact_type
minimum_impact
maximum_impact
source
assumptions

emission_factors
----------------
fuel
kg_co2e_per_kwh
source
source_year
accounting_boundary

sales_history
-------------
property_id
sale_date
sale_price
energy_rating_at_sale

retrofit_history
----------------
property_id
retrofit_id
completion_date

For the MVP, customer IDs can be fictional and property information can be synthetic or lawfully obtained public information.
12.4 Train / Validation / Test Splits
Use:
- 70% training
- 15% validation
- 15% test
Split by property ID or customer ID before constructing multiple property-related examples.
No record for the same property should appear in multiple splits.
For synthetic data, avoid leakage through shared generation seeds, reused records, or labels derived from unavailable future information.
If the valuation data supports chronological validation, report a time-based evaluation as well.
13. UX and Dashboard Requirements
Owner: Person 2
The dashboard needs to communicate complex calculations in a visually simple format.
Use a minimal interface with an off-white background, charcoal text, muted green accents, and a limited number of charts.
Avoid spending too much time on visual effects.
13.1 Page 1 — Property Selection
Features:
- Search or select a demo property.
- Enter property details.
- Edit energy usage.
- Show data-completeness warnings.
- Run assessment.
13.2 Page 2 — Green Home Dashboard
Main components:
Green Home Score
A prominent score displayed as:
38 / 100 — Poor
Score breakdown
A chart displaying the seven weighted contributions.
Current performance
- Annual grid electricity
- Annual gas consumption
- Energy intensity
- Estimated annual emissions
- Current EPC rating
Efficiency issues
Display the strongest reasons for poor performance.
13.3 Page 3 — Retrofit Planner
A prioritized list of feasible retrofits.
Each recommendation displays:
- Suitability
- Reason
- Estimated implementation cost
- Electricity change
- Gas change
- Carbon reduction
- Important assumptions
Users can select or deselect retrofits.
A budget input controls the recommendation engine.
Important: The selection must trigger a backend simulation, not update the numbers using frontend arithmetic.
13.4 Page 4 — Scenario Comparison
Side-by-side comparison:
Metric	Current home	Proposed home
Green Home Score	Calculated	Recalculated
Electricity	Baseline	Simulated
Gas	Baseline	Simulated
Carbon	Baseline	Simulated
Estimated value	Baseline estimate	Indicative scenario range


Recommended charts:
- Stacked electricity and gas bars
- Carbon emissions comparison
- Score contribution comparison
- Retrofit cost versus estimated savings
13.5 Page 5 — AI Advisor
A simple conversational interface.
The assistant should use the currently selected property and scenario as context.
For example:
Why do you recommend insulation before installing a heat pump?

It should explain the model's reasoning and cite the assumptions or data sources used.
For what-if questions, the response should be accompanied by a fresh scenario result.
13.6 Page 6 — Portfolio Analysis
This can be a secondary dashboard.
Show all demo properties and allow sorting by:
- Green Home Score
- Energy intensity
- Improvement potential
- Potential carbon reduction
This is particularly relevant to Lloyds because a financial institution may want to identify sustainability opportunities across a portfolio of properties.
Priority: Finish the individual-property experience first. Portfolio analysis is a later addition.
14. API Contracts and Integration
These contracts must be agreed upon before development begins.
Person 1 owns the API interface. Other team members should implement logic behind it.
14.1 API Endpoints
Endpoint	Method	Purpose
/health	GET	Backend health
/properties	GET	List demo properties
/properties/{id}	GET	Property details
/properties/{id}/assessment	GET	Score and efficiency issues
/retrofits/recommend	POST	Feasible recommendations
/scenarios/simulate	POST	Recalculate a retrofit package
/properties/{id}/valuation	POST	Value impact estimate
/advisor/chat	POST	Grounded AI explanation
/portfolio/rank	GET	Rank properties by improvement potential


For the dashboard, Person 1 should also expose a unified endpoint that combines the core outputs into one response.
14.2 Scenario Request Contract
{
  "property_id": "P10001",
  "retrofits": [
    "loft_insulation",
    "heat_pump",
    "solar_panels"
  ],
  "budget_gbp": 15000,
  "objective": "carbon_reduction"
}

14.3 Scenario Response Contract
{
  "property_id": "P10001",
  "scenario_id": "scenario_001",
  "status": "success",
  "feasibility": {
    "all_feasible": true,
    "rejected_retrofits": []
  },
  "score": {
    "baseline": 38,
    "after": 72,
    "classification_after": "Good"
  },
  "energy": {
    "baseline_electricity_kwh": 4800,
    "baseline_gas_kwh": 12000,
    "after_electricity_kwh": 6000,
    "after_gas_kwh": 3000,
    "electricity_savings_kwh": -1200,
    "gas_savings_kwh": 9000,
    "net_savings_kwh": 7800,
    "improvement_percentage": 46.43
  },
  "carbon": {
    "reduction_kg_co2e": null,
    "status": "awaiting_factors"
  },
  "valuation": {
    "status": "unavailable",
    "reason": "No calibrated valuation model available"
  },
  "assumptions": [],
  "warnings": []
}

This is an illustrative integration contract. The numbers are not linked to any actual simulation and must never be shipped as hardcoded production results.
A completed scenario should replace the null fields only when the relevant calculations succeed.
The frontend must gracefully display unavailable results.
14.4 Standard Internal Function Contracts
These function interfaces are more important than the choice of ML library.
Owner	Function	Input	Output
P1	calculate_score()	Property + annual energy	Score breakdown
P1	detect_efficiency_issues()	Property + score	Classification + issues
P3	load_property()	Property ID	Validated property
P3	annualize_energy()	Monthly records	Annual fuel consumption + quality
P4	check_feasibility()	Property + retrofits	Feasibility result
P4	simulate_retrofits()	Property + package	Per-fuel scenario
P4	calculate_carbon()	Per-fuel changes + factors	Carbon impact
P4	optimize_package()	Property + budget	Ranked packages
P5	predict_value_impact()	Baseline + scenario	Indicative range
P2	generate_explanation()	Verified result	Grounded explanation


Critical integration rule
Person 4 should provide both the updated fuel values and the updated physical-property state.
For example, after installing a heat pump, the property should indicate that the heating system has changed.
Otherwise, the post-retrofit score and valuation model will use inconsistent information.
15. GitHub Repository Structure
Create one repository with clearly separated ownership.
greenprint-ai/
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx
│   │   ├── property/
│   │   ├── dashboard/
│   │   ├── planner/
│   │   ├── compare/
│   │   └── advisor/
│   │
│   ├── components/
│   ├── lib/
│   │   ├── api.ts
│   │   └── types.ts
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── properties.py
│   │   │   ├── scoring.py
│   │   │   ├── retrofits.py
│   │   │   ├── scenarios.py
│   │   │   ├── valuation.py
│   │   │   └── advisor.py
│   │   │
│   │   ├── core/
│   │   │   ├── scoring.py
│   │   │   ├── efficiency.py
│   │   │   └── config.py
│   │   │
│   │   ├── services/
│   │   │   ├── retrofit_engine.py
│   │   │   ├── energy_engine.py
│   │   │   ├── carbon_engine.py
│   │   │   ├── valuation_service.py
│   │   │   └── llm_service.py
│   │   │
│   │   ├── schemas/
│   │   └── db/
│   │
│   ├── tests/
│   └── requirements.txt
│
├── ml/
│   ├── train_valuation.py
│   ├── evaluate_valuation.py
│   ├── models/
│   └── reports/
│
├── data/
│   ├── raw/
│   ├── processed/
│   ├── synthetic/
│   ├── retrofit_catalogue.csv
│   └── emission_factors.csv
│
├── scripts/
│   ├── prepare_data.py
│   ├── generate_synthetic.py
│   └── validate_data.py
│
├── evaluation/
│   ├── test_scenarios.py
│   ├── evaluate_recommendations.py
│   ├── evaluate_explanations.py
│   └── results/
│
├── docs/
│   ├── architecture.md
│   ├── scoring_methodology.md
│   ├── data_methodology.md
│   ├── retrofit_assumptions.md
│   ├── evaluation_report.md
│   └── responsible_ai.md
│
├── .env.example
├── .gitignore
└── README.md

File ownership
Person	Primary ownership
P1	backend/app/api/, backend/app/core/, backend/app/schemas/
P2	frontend/, backend/app/services/llm_service.py
P3	data/, scripts/, backend/app/db/
P4	backend/app/services/retrofit_engine.py, energy_engine.py, carbon_engine.py
P5	ml/, backend/app/services/valuation_service.py, evaluation/


Documentation should be contributed by the person responsible for the corresponding subsystem.
Avoid two people editing the same files simultaneously.
16. Division of Work — Detailed Assignments
Person 1 — Technical Lead and Backend Engineer
Codex Plus Account #1
Primary mission
Build the application backbone and ensure every subsystem connects correctly.
Responsibilities
Architecture
- Initialize repository structure.
- Create FastAPI application.
- Define shared Pydantic models.
- Establish API contracts.
- Configure CORS and environment variables.
Scoring
- Implement the exact weighted formula.
- Implement seven monotonic mappings.
- Return contribution-level explanations.
- Classify homes.
- Detect low-efficiency properties.
Backend integration
- Integrate Person 3's datasets.
- Integrate Person 4's simulation engine.
- Integrate Person 5's valuation model.
- Expose APIs to Person 2.
Quality
- Add API tests.
- Handle missing inputs.
- Validate response schemas.
- Eliminate hardcoded demo results.
- Manage final integration.
Deliverables
backend/app/main.py
backend/app/core/scoring.py
backend/app/core/efficiency.py
backend/app/schemas/
backend/app/api/
backend/tests/test_scoring.py
backend/tests/test_api.py
docs/scoring_methodology.md

Definition of done
The backend can accept a property, calculate its Green Home Score, classify it, and return the exact seven-component breakdown.
After integration, it can execute a complete scenario through one API call.
Priority: Critical
Person 2 — Frontend Lead and AI Engineer
Codex Plus Account #2
Primary mission
Build the complete user experience and make the AI assistant genuinely useful.
Responsibilities
Frontend
- Build the property-selection page.
- Build the Green Home Score dashboard.
- Build retrofit recommendation cards.
- Build the scenario planner.
- Add before-and-after charts.
- Build portfolio comparison if time permits.
AI
- Implement LLM-provider abstraction.
- Implement intent extraction.
- Connect what-if intents to backend simulation.
- Generate grounded explanations.
- Add deterministic fallback.
- Handle infeasible and unavailable scenarios.
Integration
- Connect frontend to FastAPI.
- Ensure numerical displays always use backend values.
- Add loading/error states.
Deliverables
frontend/app/
frontend/components/
frontend/lib/api.ts
frontend/lib/types.ts
backend/app/services/llm_service.py
backend/app/api/advisor.py
docs/llm_methodology.md

Definition of done
A user can select a property, view its assessment, explore retrofits, compare scenarios, and ask the AI assistant questions.
The application remains functional when the LLM is unavailable.
Priority: Critical
Person 3 — Data Engineer
ChatGPT Free
Primary mission
Provide realistic, reproducible datasets that all other modules can use.
Responsibilities
- Research and download manageable public datasets.
- Inspect licensing restrictions.
- Define a consistent data schema.
- Generate synthetic property records.
- Generate realistic monthly electricity/gas consumption.
- Create demo properties.
- Create or validate the retrofit catalogue.
- Obtain official emissions factors.
- Validate missing and inconsistent data.
- Prepare train/validation/test splits.
- Document synthetic-data generation rules.
Deliverables
data/processed/properties.csv
data/processed/energy_usage.csv
data/synthetic/
data/retrofit_catalogue.csv
data/emission_factors.csv
scripts/generate_synthetic.py
scripts/prepare_data.py
scripts/validate_data.py
docs/data_methodology.md

Definition of done
The backend and ML modules can load the datasets without manual edits.
The dataset generation is reproducible from a documented random seed.
The schema distinguishes observed, derived, imputed, and synthetic information.
Priority: Critical
Important instruction
Person 3 must provide an initial dataset schema and a few valid test properties within the first two hours.
The full data-processing pipeline can continue afterward.
Person 4 — Energy, Retrofit and Optimization Engineer
ChatGPT Free
Primary mission
Build the mathematical and physical engine responsible for recommendations, savings, and carbon calculations.
Responsibilities
- Define feasibility checks.
- Identify relevant retrofit candidates.
- Model baseline heating demand.
- Model insulation and glazing effects.
- Model heat-pump fuel substitution.
- Model solar grid-import reduction.
- Model smart thermostat effects.
- Calculate per-fuel savings.
- Calculate carbon reduction using official factors.
- Handle retrofit interactions.
- Rank individual retrofits.
- Optimize packages for user budgets.
- Create scenario-based tests.
Deliverables
backend/app/services/retrofit_engine.py
backend/app/services/energy_engine.py
backend/app/services/carbon_engine.py
backend/tests/test_energy_engine.py
backend/tests/test_retrofits.py
backend/tests/test_carbon.py
docs/retrofit_assumptions.md

Definition of done
Given a property and retrofit package, the engine returns a valid post-retrofit property state, separate electricity and gas estimates, net energy savings, and carbon reduction.
The same input must always produce the same result.
Priority: Critical
Important instruction
Person 4 should avoid spending time training a recommendation classifier.
A deterministic feasibility and prioritization engine is more practical and easier to evaluate in this timeframe.
Person 5 — ML Engineer and Evaluation Lead
ChatGPT Free
Primary mission
Develop the property-value model and establish evidence that the overall system works.
Responsibilities
Machine learning
- Prepare valuation features.
- Train a simple baseline.
- Train a nonlinear regression model.
- Compare held-out performance.
- Save the fitted model and preprocessing.
- Implement scenario-based value predictions.
- Generate uncertainty ranges.
- Document limitations.
Evaluation
- Validate property-level splitting.
- Evaluate retrofit feasibility.
- Compare the energy simulator with reference cases.
- Check score monotonicity.
- Measure numerical reproducibility.
- Evaluate LLM groundedness using prepared cases.
- Consolidate the final evaluation report.
Documentation
- Draft responsible AI notes.
- Document model limitations.
- Maintain evaluation results.
Deliverables
ml/train_valuation.py
ml/evaluate_valuation.py
ml/models/
ml/reports/
backend/app/services/valuation_service.py
evaluation/
docs/evaluation_report.md
docs/responsible_ai.md

Definition of done
The valuation model can load from disk and return a baseline-consistent, indicative value range when supported.
A reproducible evaluation report includes baseline comparisons and held-out metrics.
Priority: High
Important instruction
If reliable valuation training data or energy-rating features cannot be obtained, do not fabricate market evidence.
Use an explicitly illustrative model, disclose its limitations, and return unavailable for real-world value-uplift claims.
17. The 24-Hour Development Schedule
The key is to work in parallel from the beginning, with integration happening continuously rather than at the end.
Phase 1 — Architecture and Foundation
Hour 0–2
Person	Tasks	Checkpoint
P1	Initialize FastAPI, repository, schemas and scoring engine	API starts
P2	Initialize Next.js and dashboard layout	Frontend starts
P3	Define data schemas and create 10 demo properties	Valid sample data
P4	Define retrofit model inputs, outputs and assumptions	Simulation interface
P5	Identify valuation dataset and implement baseline model	Baseline training script


Mandatory team meeting at Hour 2.
Verify that everybody agrees on property fields, retrofit identifiers, fuel units and API response formats.
Do not allow independent implementations to diverge.
Phase 2 — Core Module Development
Hour 2–7
Person	Tasks	Checkpoint
P1	Finish score, classification, issue detection, API endpoints	Scoring API functional
P2	Finish property entry, score dashboard, retrofit UI	Frontend demo using mocks
P3	Implement synthetic generation, clean public data, emissions factors	Reproducible data
P4	Implement retrofit feasibility and sequential energy simulator	Scenario engine functional
P5	Train valuation models, test splits and baselines	Initial held-out metrics


Mandatory integration at Hour 7.
At this checkpoint, the team should be able to calculate a score and simulate a retrofit from Python, even if the complete interface is not connected.
Phase 3 — First End-to-End Prototype
Hour 7–12
Person	Tasks
P1	Integrate data, scoring and retrofit services
P2	Connect frontend to the actual backend; build scenario comparison
P3	Finalize data loader, missing-data cases and provenance
P4	Implement carbon calculations, package optimization and tests
P5	Implement valuation service and uncertainty ranges


Required milestone at Hour 12
The application must support:
Select property → Calculate score → Recommend improvements → Select package → Calculate energy/carbon impact → Display results.
If this flow is not working, stop developing optional features.
Do not continue building the AI assistant, animations or portfolio analytics until the core flow works.
Phase 4 — AI and Advanced Functionality
Hour 12–17
Person	Tasks
P1	Finish API integrations, improve error handling
P2	Implement grounded AI assistant and what-if orchestration
P3	Create realistic edge-case properties and data-quality tests
P4	Complete package optimization and interaction tests
P5	Integrate value estimates and build evaluation harness


Required milestone at Hour 17
A user should be able to ask:
"What if I replace my gas boiler with a heat pump?"

The platform should rerun the appropriate simulation and explain the updated results.
Phase 5 — Evaluation and Reliability
Hour 17–21
Stop adding major features.
Focus entirely on:
- Functional tests
- Numerical accuracy
- Infeasible retrofit handling
- Missing data
- Integration issues
- LLM grounding
- Evaluation reports
- Responsiveness
- Reproducibility
Everyone tests somebody else's module.
Suggested cross-review:
Reviewer	Reviews
P1	P4 simulation and integration
P2	P1 backend response behavior
P3	P5 data splitting and model inputs
P4	P2 scenario behavior
P5	P3 data methodology and quality


Phase 6 — Submission
Hour 21–24
Time	Work
21–22	Freeze code, final smoke tests
22–23	README, architecture, evaluation and Responsible AI report
23–24	Record demo, prepare presentation and verify submission


Do not make major architectural changes after Hour 21.
Reserve the final hour for packaging and final demonstration checks.
18. Evaluation Plan
The challenge gives significant weight to data quality, ML methodology, calculations and LLM behavior.
You need evidence beyond a working interface.
18.1 Score Evaluation
Owner: P1
Required tests:
1. All seven weights sum to 1.
2. Every sub-score remains between 0 and 100.
3. Better insulation never decreases the insulation score.
4. Better glazing never decreases the glazing score.
5. Lower consumption intensity never decreases its score.
6. Final classification uses the rounded score.
7. Scores and contributions are reproducible.
Use parameterized tests for every monotonic mapping.
18.2 Retrofit Evaluation
Owner: P4
Test the feasibility engine against labeled property-retrofit pairs.
For example:
Property condition	Retrofit	Expected behavior
Already triple-glazed	Double glazing	Reject
Existing solar installation at supported capacity	Duplicate solar installation	Reject
Poor insulation, suitable loft	Loft insulation	Eligible
Roof suitability unknown	Solar	Conditional / insufficient information
Heat pump physically unsuitable	Heat pump	Reject
Heat pump installation	Heating-system update	Required


Report feasibility precision, recall and F1 against a documented reference set, if sufficient independently reviewed reference labels are available.
Do not call tests against the same rules that generated the labels independent validation.
18.3 Energy Evaluation
Owner: P4 + P5
Create reference cases covering:
- Insulation only
- Solar only
- Heat pump only
- Smart thermostat only
- Double glazing only
- Multiple interacting retrofits
- Zero baseline energy
- Missing annual consumption
- Heat pump increasing electricity use
- Infeasible retrofit packages
Compare predictions to independently prepared reference estimates where possible.
Use MAE and percentage error when appropriate.
If reference outputs come from the same simulator, report agreement as implementation verification rather than proof of predictive accuracy.
18.4 Property Valuation Evaluation
Owner: P5
Minimum evaluation:
Metric	Requirement
MAE	Report
RMSE	Report
R²	Report
Baseline comparison	Required
Prediction interval coverage	Required where range model exists
Dataset sizes	Required
Data leakage checks	Required


Include separate commentary about why the estimated value change is not necessarily causal.
18.5 LLM Evaluation
Owner: P2 + P5
Prepare 20–30 test questions covering factual explanations, missing data, infeasible scenarios and what-if requests.
Evaluate:
- Groundedness
- Factual accuracy
- Unsupported numerical claims
- Completeness
- Correct tool invocation
- Correct handling of unavailable values
The challenge specifies targets of:
- Groundedness ≥90%
- Factual accuracy ≥90%
- Unsupported claims <5%
Create a simple evaluation harness that compares generated responses against structured model outputs and human-reviewed expected behavior.
Do not claim these targets have been met until evaluation is actually run.
18.6 System Evaluation
Owner: P1
Measure:
- Score calculation latency
- Scenario simulation latency
- Full assessment API latency
- LLM response latency
- Error rate on test cases
- Local startup reproducibility
The core calculations should execute without remote LLM dependencies.
19. Innovation Strategy
Innovation accounts for 10% of the final score.
Don't sacrifice core functionality to chase too many extras.
I recommend prioritizing two innovations.
Innovation 1 — Budget-Constrained Retrofit Optimizer
Highest priority
Rather than recommending every possible retrofit, optimize a retrofit package based on a customer's budget.
Example:
A homeowner has £8,000.
The engine identifies feasible combinations and compares them by expected carbon reduction or energy savings.
This provides a direct, practical benefit to homeowners and financial institutions.
It also demonstrates that recommendations account for interactions between improvements.
Innovation 2 — Green Mortgage Readiness
High value for Lloyds
Create an informational panel answering:
"How might the proposed improvements affect my home's energy efficiency and potential suitability for green housing finance?"

Show:
- Current EPC rating
- Estimated post-retrofit efficiency
- Potential property-value impact
- Estimated retrofit investment
- Annual running-cost savings
- Indicative payback
Do not invent Lloyds mortgage eligibility criteria or promise a mortgage benefit.
Position this as a decision-support feature that could help customers prepare for conversations about green-home financing.
Optional Innovation 3 — Customer Memory
If the core system is stable, implement simple persistent preferences:
- Maximum budget
- Preferred retrofit types
- Previously completed improvements
- Declined recommendations
- Previous scenario selections
SQLite is sufficient.
For example, if a customer previously rejected solar panels, future recommendations could deprioritize solar unless conditions or preferences change.
The underlying numerical calculations must remain unchanged.
My recommendation: Build Innovations 1 and 2. Add customer memory only if the core platform is fully complete.
20. GitHub Workflow
Set up the repository immediately.
Use five branches:
main
feature/backend-scoring
feature/frontend-llm
feature/data-engineering
feature/retrofit-engine
feature/valuation-evaluation

Assign each branch to its corresponding team member.
Merge process
At the start:
1. Person 1 creates the repository.
2. Person 1 adds the directory structure and shared schemas.
3. Everybody creates their branches from the same commit.
4. Each member works only inside owned files.
5. Feature branches are integrated at predefined checkpoints.
6. Person 1 maintains the working main branch.
Avoid waiting until the final hour to merge everything.
Integration checkpoints
- Hour 2
- Hour 7
- Hour 12
- Hour 17
- Hour 21
For long-running changes, use smaller pull requests so integration problems are discovered early.
21. Ready-to-Use Codex Prompts
Use these as development instructions. The PRD above remains the source of truth.
Person 1 — Codex Plus #1
You are the principal backend architect for GreenPrint AI,
a 24-hour hackathon project for Lloyds.

Read the project PRD before implementing anything.

You own:
- FastAPI backend architecture
- Pydantic schemas
- Green Home Score
- Efficiency detection
- API integration
- Backend tests
- Final subsystem integration

Important constraints:

1. Green Home Score must use the seven exact weights:
   25%, 20%, 15%, 15%, 10%, 10%, 5%.

2. Every component mapping must be documented
   and monotonic.

3. Energy efficiency must use EPC rating information.
   Consumption intensity must use annualized metered
   purchased energy per square metre.

4. Scores, savings, carbon and value figures must
   never be generated by an LLM.

5. Other team members own data engineering,
   retrofit simulation, valuation and frontend.
   Do not duplicate their implementations.

6. Define and preserve shared interfaces before
   implementing the API routes.

7. Use mock adapters only during initial development.
   Remove hardcoded numerical demo results from
   production routes before submission.

8. Every endpoint must use validated Pydantic schemas.

9. Missing data, unavailable models and infeasible
   retrofits must produce explicit responses.

10. Include automated tests and clear run commands.

Development process:

First:
- Inspect the repository.
- Define architecture and module boundaries.
- Establish request/response contracts.
- Create the application skeleton.

Then:
- Implement scoring and classification.
- Write tests.
- Implement APIs.
- Integrate external team modules as they arrive.

Do not unnecessarily refactor files owned by
other contributors.

Prioritize a working end-to-end backend over
advanced architecture.

Explain major design decisions briefly.

Person 2 — Codex Plus #2
You are the frontend and GenAI engineer for
GreenPrint AI, a home sustainability assessment
platform for the Lloyds hackathon.

Read the complete PRD.

Your responsibilities:
- Next.js dashboard
- Property selection and input
- Green Home Score visualization
- Retrofit recommendation interface
- Before/after scenario comparison
- Budget-constrained retrofit planner
- Grounded LLM assistant
- What-if orchestration

Build a polished but minimal user interface.

Use:
- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui
- Recharts

Architecture requirements:

1. All numerical outputs must come from FastAPI.

2. Never calculate energy savings, score,
   carbon reductions or value uplift inside
   frontend components.

3. The LLM must not invent calculations.

4. What-if questions must trigger backend
   scenario simulation before explanation.

5. The application must handle unavailable
   estimates and infeasible recommendations.

6. Implement deterministic explanation fallback
   if the LLM is unavailable.

7. Avoid expensive UI animations.

8. Ensure responsive desktop and mobile layouts.

9. Use the shared API contracts from the PRD.

10. Work primarily inside frontend/ and the
    explicitly owned LLM service files.

Begin by building the dashboard with typed mock data,
then connect to the real backend.

Prioritize:
Property selection ->
Green Home Score ->
Retrofit planner ->
Scenario comparison ->
AI assistant.

Do not build secondary features until this
flow works.

22. Prompts for the Three Free-Tier Members
These prompts should be usable with ChatGPT Free or another available coding assistant. They intentionally keep each task self-contained.
Person 3 — Data Engineering
Act as a senior data engineer.

I am working on GreenPrint AI, a UK home-energy
efficiency hackathon project.

I need a reproducible property and energy dataset.

Your task is limited to data engineering.

Build:
1. Property schema
2. Energy usage schema
3. Realistic synthetic property generator
4. Monthly electricity and gas generator
5. Data quality validator
6. Property-level train/validation/test splitting
7. Public data ingestion where practical
8. Data methodology documentation

Use Python, pandas and numpy.

Important:
- Do not generate arbitrary target labels.
- Model plausible relationships between building
  characteristics and energy demand.
- Ensure large houses are not automatically inefficient.
- Preserve provenance and missing-value information.
- Do not treat missing energy readings as zero.
- Use deterministic random seeds.
- Generate 1000–3000 properties.
- Include 10 hand-reviewed demo properties.
- Obtain documented UK emissions factors.
- Output clean CSV files.

Use the repository structure and data contracts
provided in the PRD.

Provide complete working scripts with tests
and usage instructions.

Person 4 — Retrofit and Energy Engine
Act as a building-energy modeling engineer
and Python developer.

You are building the core numerical retrofit
engine for GreenPrint AI.

Implement:
1. Retrofit feasibility checks
2. Retrofit relevance and prioritization
3. Heating-demand model
4. Insulation and glazing effects
5. Heat pump fuel substitution
6. Solar grid-import reduction
7. Smart thermostat energy effects
8. Sequential retrofit interaction modeling
9. Electricity and gas savings
10. Carbon calculation using documented factors
11. Budget-constrained package optimization
12. Automated tests

Constraints:

The engine must be deterministic and explainable.

Do not simply add individual retrofit percentages.

Heating-system changes may increase electricity
while reducing gas consumption.

Report negative savings for increased consumption.

Solar reduces grid electricity purchases,
not household electricity demand.

Use documented assumptions and units.

Return updated property characteristics together
with the calculated fuel changes.

Do not use an LLM to calculate numerical estimates.

Prioritize physically consistent outputs over
unnecessary machine learning.

Implement complete Python functions using the
shared interfaces from the PRD.

Include tests for missing inputs, infeasible
retrofits and interacting measures.

Person 5 — Valuation ML and Evaluation
Act as a senior ML engineer and evaluation specialist.

I am building GreenPrint AI for the Lloyds
hackathon.

My responsibilities are:
1. Property-value regression
2. Model training and inference
3. Baseline comparisons
4. Prediction uncertainty
5. Model evaluation
6. System evaluation documentation
7. Responsible AI documentation

Use scikit-learn and pandas.

Build a simple regression baseline before
training a stronger nonlinear model.

Features should include:
- Region
- Property type
- Floor area
- Bedrooms
- Property age
- Market conditions
- EPC rating where supported

Prevent data leakage.

Use property-level or customer-level splits.

Estimate value before and after retrofits while
holding unrelated property characteristics constant.

Do not claim that observational associations prove
a causal retrofit premium.

Prediction ranges must come from a documented
calibration method, not arbitrary percentages.

If the dataset cannot support a credible
retrofit-value relationship, return unavailable
rather than fabricate estimates.

Report MAE, RMSE, R2, interval coverage,
and baseline comparison.

Also create an evaluation harness for:
- Score monotonicity
- Retrofit feasibility
- Per-fuel calculation consistency
- LLM groundedness
- Unsupported numerical claims

Provide reproducible scripts, tests and
clear methodological limitations.

23. Risks and Contingency Plan
A 24-hour deadline means you need predefined fallback decisions.
Risk	Impact	Contingency
Public datasets take too long to prepare	High	Use documented synthetic dataset + public benchmarks
Valuation training fails	High	Ship calibrated baseline where possible; otherwise mark uplift unavailable
LLM API unavailable	Medium	Deterministic explanations
Frontend integration delayed	High	Prioritize score and scenario pages
Retrofit models produce inconsistent results	Critical	Reduce supported retrofit combinations until physically valid
Git merge conflicts	Medium	Strict file ownership
Deployment fails	Medium	Local demo with startup script
Insufficient time for customer memory	Low	Drop optional extension
Insufficient time for portfolio dashboard	Low	Keep individual-property flow
Missing carbon factors	High	Source official factors early; never invent values


Features to cut first
If the project falls behind schedule, cut features in this order:
1. Customer memory
2. Advanced portfolio analytics
3. Green mortgage informational panel
4. Multiple optimization objectives
5. Complex AI conversation history
Do not cut:
- Correct weighted scoring
- Separate electricity/gas modeling
- Retrofit feasibility
- Retrofit interactions
- Carbon calculations
- Valuation methodology and honest limitations
- Grounded what-if behavior
- Evaluation and reproducibility
24. Submission Checklist
Your submission should satisfy all nine required deliverables.
Submission requirement	Responsible member
A. Working web prototype	P1 + P2
B. Source code and data scripts	P3 + P1
C. Trained models and inference code	P5
D. Documented scoring methodology	P1
E. LLM prompts, provider and evaluation	P2 + P5
F. Architecture diagram	P1
G. Evaluation report	P5, with team contributions
H. Responsible AI note	P5
I. Held-out predictions and schema documentation	P3 + P4 + P5


Also include:
- README.md with complete setup instructions
- .env.example without secrets
- Required dependencies
- Model artifact or reproducible training instructions
- Data-source links and licenses
- Dataset-generation scripts
- Example scenario inputs
- Recorded numerical test outputs
- Screenshots or a short demo video
For reproducibility, the README should provide a straightforward sequence to prepare data, train any required models, start the backend, start the frontend, and run the tests.
25. Suggested Demo Flow
Aim for a three- to four-minute demonstration.
Step 1 — Assess a home (30 seconds)
Open GreenPrint AI.
Select a poorly performing demonstration property.
Display its Green Home Score and the seven contributions.
Explain why the home is inefficient.
Step 2 — View recommendations (45 seconds)
Open the retrofit planner.
Display feasible upgrades with suitability, cost and expected impact.
Show how the system prioritizes insulation before heating-system replacement when appropriate.
Step 3 — Optimize for a budget (45 seconds)
Enter a budget.
Show the best feasible combination for a selected objective.
Demonstrate that the system evaluates packages rather than adding independent savings percentages.
Step 4 — Compare scenarios (45 seconds)
Apply the selected package.
Show:
- Updated score
- Electricity change
- Gas change
- Net energy savings
- Carbon reduction
- Indicative property-value range, if supported
Emphasize the fuel substitution from a heat pump.
Step 5 — Ask a what-if question (45 seconds)
Ask:
"What if I skip insulation and install only a heat pump?"

Demonstrate that the backend recalculates everything before the LLM explains the new scenario.
This is likely to be one of the strongest parts of your demonstration.
Step 6 — Prove reliability (30 seconds)
Briefly show:
- Test results
- Evaluation metrics
- Documented emission factors
- Transparent assumptions
- Missing-data handling
The message to the judges should be:
GreenPrint AI does not simply produce sustainability recommendations. It provides a transparent, testable decision-support system for homeowners.
26. My Recommended Priorities for Winning
Based on the scoring criteria, here's how I would prioritize the team's limited time.
Area	Judging weight	Our implementation priority
ML and recommendation quality	20%	Very high
Business relevance	15%	Very high
Energy, carbon and valuation estimates	15%	Very high
GenAI and what-if explanations	15%	Very high
Technical architecture	10%	High
Innovation	10%	High
Green Home Score quality	5%	Essential
Explainability and responsible AI	5%	Essential
UX and dashboard	5%	High
Total	100%	


The temptation will be to spend too much time building a visually impressive dashboard or training an overly complicated model.
Avoid that.
The judges explicitly care about:
- Defensible calculations
- Meaningful model evaluation
- Reproducibility
- Realistic assumptions
- Useful recommendations
- Correct handling of edge cases
A powerful model with fabricated synthetic labels is much less convincing than a transparent simulator backed by a well-designed evaluation process.
27. Final Work Allocation
This is the assignment table I would send to the team immediately.
Member	Role	Must finish by Hour 7	Must finish by Hour 17	Final responsibility
P1 — Codex Plus	Backend / Architecture	Scoring engine + initial APIs	Fully integrated backend	Stability and final integration
P2 — Codex Plus	Frontend / GenAI	Dashboard and retrofit UI	Working AI what-if experience	Demo and frontend QA
P3 — Free	Data Engineering	Dataset generation and clean sample data	Final datasets, emissions factors and documentation	Data reproducibility
P4 — Free	Retrofit / Energy	Feasibility and energy simulation	Complete interaction-aware engine and optimization	Numerical correctness
P5 — Free	ML / Evaluation	Baseline valuation model	Valuation model + evaluation scripts	Final metrics and reports


Three non-negotiable checkpoints
Hour 2: Contracts and sample data frozen.
Hour 12: Complete numerical pipeline working end to end.
Hour 21: Code freeze. Only documentation, testing and demo preparation afterward.
Final recommendation
For this 24-hour hackathon, I would build GreenPrint AI around three standout capabilities:
1. Explainable Green Home Score: Every point has a traceable calculation, with no arbitrary LLM estimates.
2. Budget-Aware Retrofit Optimization: The platform finds feasible combinations that deliver the best estimated sustainability outcome for the customer's constraints.
3. Grounded Conversational What-If Engine: Users can change retrofit scenarios through natural language, and every numerical answer is regenerated by the actual models.
Together, these deliver a coherent product with genuine relevance to Lloyds, while keeping the implementation feasible for five developers using only two Codex Plus accounts.
The main objective is not to implement the largest number of features. It is to deliver one complete, numerically consistent, evaluated system that survives the judges' hidden scenario tests.