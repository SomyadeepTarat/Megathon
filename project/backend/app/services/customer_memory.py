"""Explicit, bounded customer memory. Never supplies physical inputs or estimates."""
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field
from app.services.llm_service import AdvisorService, ChatResponse, Intent, PropertyNotFound, Retrofit, Objective, EngineUnavailable, Fact

class Preferences(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)
    budget_gbp: float | int | None = Field(default=None, ge=0, le=1_000_000_000)
    objective: Objective = 'carbon_reduction'
    excluded_retrofits: list[Retrofit] = Field(default_factory=list, max_length=5)

class MemoryUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)
    revision: int = Field(ge=0)
    preferences: Preferences | None = None
    completed_retrofits: list[Retrofit] | None = Field(default=None, max_length=5)
    feedback: 'Feedback | None' = None
    reset: bool = False

class Feedback(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)
    retrofits: list[Retrofit] = Field(min_length=1, max_length=5)
    response: str = Field(pattern=r'^(accepted|rejected|deferred)$')

MemoryUpdate.model_rebuild()

class MemoryConflict(Exception):
    pass

class MemoryStore:
    def __init__(self, path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as c:
            c.execute('CREATE TABLE IF NOT EXISTS customer_memory (customer_id TEXT PRIMARY KEY, payload TEXT NOT NULL)')

    @staticmethod
    def empty():
        return {'revision': 0, 'preferences': Preferences().model_dump(), 'properties': {}}

    def load(self, customer):
        with sqlite3.connect(self.path) as c:
            row = c.execute('SELECT payload FROM customer_memory WHERE customer_id=?', (customer,)).fetchone()
        return json.loads(row[0]) if row else self.empty()

    def mutate(self, customer, action, revision=None):
        # An atomic read/modify/write prevents concurrent chats losing preferences.
        with sqlite3.connect(self.path, timeout=10) as c:
            c.execute('BEGIN IMMEDIATE')
            row = c.execute('SELECT payload FROM customer_memory WHERE customer_id=?', (customer,)).fetchone()
            value = json.loads(row[0]) if row else self.empty()
            if revision is not None and revision != value['revision']:
                raise MemoryConflict()
            action(value)
            value['revision'] += 1
            value['updated_at'] = datetime.now(timezone.utc).isoformat()
            c.execute('INSERT INTO customer_memory VALUES (?,?) ON CONFLICT(customer_id) DO UPDATE SET payload=excluded.payload', (customer, json.dumps(value)))
            return value

    def update(self, customer, property_id, change):
        def action(value):
            if change.reset:
                # Reset this home's context; retain another home's completed work.
                value['preferences'] = Preferences().model_dump()
                value['properties'].pop(property_id, None)
                return
            if change.preferences is not None:
                value['preferences'] = change.preferences.model_dump()
            prop = value['properties'].setdefault(property_id, {})
            if change.completed_retrofits is not None:
                prop['completed_retrofits'] = sorted(set(change.completed_retrofits))
            if change.feedback is not None:
                key = ','.join(sorted(set(change.feedback.retrofits)))
                prop.setdefault('feedback', {})[key] = {'response': change.feedback.response, 'updated_at': datetime.now(timezone.utc).isoformat()}
        return self.mutate(customer, action, change.revision)


def identity(repository, property_id):
    try:
        record = repository.load_property(property_id)
    except KeyError:
        raise PropertyNotFound() from None
    # Source identity is authoritative; edited provenance cannot move source owners.
    try:
        canonical = repository.source.load_property(property_id)
    except (AttributeError, KeyError):
        canonical = None
    customer = (canonical.property.provenance.get('customer_id') if canonical else None)
    return ('customer:' + customer if customer else 'property:' + property_id), record


def view(value, property_id):
    prop = value['properties'].get(property_id, {})
    return {'revision': value['revision'], 'preferences': value['preferences'],
            'completed_retrofits': prop.get('completed_retrofits', []),
            'feedback': prop.get('feedback', {}), 'history': prop.get('history', [])[-20:],
            'last_action': prop.get('last_action'), 'updated_at': value.get('updated_at'),
            'scope': 'Customer preferences; completed work, feedback and follow-up context scoped to this home. Memory does not change assessment inputs.'}


def restrictions(memory):
    excluded = set(memory['preferences']['excluded_retrofits']) | set(memory['completed_retrofits'])
    packages = [key.split(',') for key, feedback in memory['feedback'].items() if feedback['response'] in ('rejected', 'deferred')]
    return excluded, packages

def stale_completed(memory, property):
    fields = {'loft_insulation': 'loft_insulation_installed', 'heat_pump': 'heat_pump_installed',
              'solar_panels': 'solar_installed'}
    def installed(retrofit):
        if retrofit == 'double_glazing':
            return property.glazing in ('double', 'triple')
        if retrofit == 'smart_thermostat':
            return property.smart_controls == 'advanced' or property.smart_thermostat_installed is True
        return getattr(property, fields[retrofit], None) is True
    return [r for r in memory['completed_retrofits'] if not installed(r)]


def planner_memory(service, repository, request):
    """Resolve the same authoritative identity; inspect the submitted current baseline."""
    if not isinstance(service, MemoryAdvisorService):
        return None
    try:
        customer, _ = identity(repository, request.property.property_id)
    except PropertyNotFound:
        customer = 'property:' + request.property.property_id
    memory = view(service.store.load(customer), request.property.property_id)
    return memory

class MemoryEngines:
    def __init__(self, base, memory, stale=()):
        self.base, self.memory, self.stale = base, memory, stale
        self.excluded, self.packages = restrictions(memory)
    def apply_intent(self, intent):
        prefs = self.memory['preferences']
        if intent.intent == 'recommend' and prefs['budget_gbp'] is not None:
            return Intent(intent='optimize_budget', budget_gbp=prefs['budget_gbp'], objective=prefs['objective'])
        if intent.intent == 'simulate_retrofit' and intent.budget_gbp is None and prefs['budget_gbp'] is not None:
            return intent.model_copy(update={'budget_gbp': prefs['budget_gbp']})
        return intent
    async def assessment(self, property_id):
        return await self.base.assessment(property_id)
    async def feasibility(self, property_id, retrofits):
        if self.excluded.intersection(retrofits) or any(set(retrofits) == set(p) for p in self.packages):
            return {'all_feasible': False, 'conditional_retrofits': list(retrofits), 'items': [{'retrofit': r, 'status': 'conditional', 'reason': 'Conflicts with saved exclusions, completed work or package feedback. Review memory to change this choice.'} for r in retrofits]}
        return await self.base.feasibility(property_id, retrofits)
    async def simulate(self, *args):
        if self.stale:
            raise EngineUnavailable('Completed work requires an updated baseline')
        return await self.base.simulate(*args)
    async def recommendations(self, property_id):
        if self.stale:
            raise EngineUnavailable('Completed work requires an updated baseline')
        return await self.base.recommendations(property_id, excluded_retrofits=self.excluded, excluded_packages=self.packages, objective=self.memory['preferences']['objective'])
    async def optimize(self, property_id, budget, objective):
        if self.stale:
            raise EngineUnavailable('Completed work requires an updated baseline')
        return await self.base.optimize(property_id, budget, objective, excluded_retrofits=self.excluded, excluded_packages=self.packages)

class MemoryAdvisorService(AdvisorService):
    def __init__(self, engines, provider, repository, store):
        super().__init__(engines, provider)
        self.repository, self.store = repository, store

    async def chat(self, request, progress=None):
        customer, record = identity(self.repository(), request.property_id)
        memory = view(self.store.load(customer), request.property_id)
        message = request.message.lower().strip().rstrip('?.!')
        # Save explicit preferences locally, without any model extraction call.
        budget = re.fullmatch(r'remember (?:that )?my budget is £?([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)', message)
        if budget and float(budget[1].replace(',', '')) > 1_000_000_000:
            return ChatResponse(status='clarification_required', intent=Intent(intent='clarify'), explanation='Please provide a budget between £0 and £1,000,000,000.', memory=memory)
        if budget:
            prefs = Preferences.model_validate({**memory['preferences'], 'budget_gbp': float(budget[1].replace(',', ''))})
            updated = self.store.mutate(customer, lambda value: value['preferences'].update(budget_gbp=prefs.budget_gbp))
            return ChatResponse(status='success', intent=Intent(intent='explain'), memory=view(updated, request.property_id), explanation=f'I’ll remember your £{prefs.budget_gbp:,.2f} budget. Ask “Use my saved preferences” to compare feasible packages. This preference does not change your home’s recorded condition.')
        prefs = memory['preferences']
        use_saved = not request.scenario and bool(re.fullmatch(r'use (?:my )?saved preferences|recommend(?:ations)?(?: for me)?|suggest improvements|how (?:can|do) i improve my score', message))
        if use_saved and prefs['budget_gbp'] is not None:
            request = request.model_copy(update={'scenario': Intent(intent='optimize_budget', budget_gbp=prefs['budget_gbp'], objective=prefs['objective'])})
        elif use_saved:
            request = request.model_copy(update={'scenario': Intent(intent='recommend')})
        if request.context is None and memory['last_action']:
            request = request.model_copy(update={'context': Intent.model_validate(memory['last_action'])})
        # A claim of completed work is not a measured new baseline. Never silently
        # mutate flags, energy readings or physical parameters from remembered text.
        stale = stale_completed(memory, record.property)
        if stale and ((request.context and request.context.intent in ('simulate_retrofit', 'optimize_budget') and re.fullmatch(r'why|why not|what do you mean|explain(?: that| this| it)?|tell me more', message)) or use_saved or (request.scenario and request.scenario.intent in ('recommend', 'simulate_retrofit', 'optimize_budget')) or re.search(r'\b(?:install|what if|recommend|budget|improve|payback|savings)\b', message)):
            return ChatResponse(status='unavailable', intent=request.scenario or Intent(intent='explain'), memory=memory,
                explanation='You recorded completed work that the assessment does not yet reflect: ' + ', '.join(r.replace('_', ' ') for r in stale) + '. Update the installed features and current energy/physical inputs in Assessment before calculating further improvements. Memory alone cannot provide a new baseline.')
        excluded, packages = restrictions(memory)
        if request.scenario and request.scenario.intent == 'simulate_retrofit' and (excluded.intersection(request.scenario.retrofits) or sorted(request.scenario.retrofits) in [sorted(p) for p in packages]):
            return ChatResponse(status='clarification_required', intent=Intent(intent='clarify'), memory=memory,
                                explanation='This package conflicts with your saved exclusions, completed work or deferred/rejected package. Review your saved preferences or feedback before simulating it.')
        service = AdvisorService(MemoryEngines(self.engines, memory, stale), self.provider)
        response = await service.chat(request, progress)
        def remember(value):
            prop = value['properties'].setdefault(request.property_id, {})
            if response.intent.intent != 'clarify':
                prop['last_action'] = response.intent.model_dump(mode='json')
            event = {'at': datetime.now(timezone.utc).isoformat(), 'action': response.intent.model_dump(mode='json'), 'status': response.status,
                     'recommended_package': (response.result or {}).get('applied_retrofits', []), 'scenario_id': (response.result or {}).get('scenario_id')}
            prop['history'] = (prop.get('history', []) + [event])[-20:]
        if stale and set(response.tool_calls).intersection({'recommendations', 'optimize', 'simulate'}):
            response.explanation = 'Update Assessment to reflect the completed work and current energy/physical inputs before estimating further improvements. Memory alone cannot provide a new baseline.'
        updated = self.store.mutate(customer, remember)
        response.memory = view(updated, request.property_id)
        response.memory['used_revision'] = memory['revision']
        if updated['preferences'] != prefs or response.memory['completed_retrofits'] != memory['completed_retrofits'] or response.memory['feedback'] != memory['feedback']:
            response.explanation += ' Your saved choices changed while this request ran. These results use the earlier settings; use your saved preferences again for a fresh calculation.'
        if prefs['budget_gbp'] is not None:
            response.facts.append(Fact(id='memory-budget', source='customer_memory.budget_gbp', text=f'User-confirmed remembered maximum budget: £{prefs["budget_gbp"]:,.2f}. This is a constraint, not an estimate.'))
        if response.status == 'unavailable' and (response.result or {}).get('reason'):
            response.explanation += ' ' + response.result['reason']
        if not use_saved and response.intent.intent == 'simulate_retrofit' and prefs['budget_gbp'] is not None and response.intent.budget_gbp == prefs['budget_gbp']:
            response.explanation = f'Your remembered maximum budget is £{prefs["budget_gbp"]:,.2f}. ' + response.explanation
        if use_saved:
            summary = (f'Using your remembered £{prefs["budget_gbp"]:,.2f} budget and {prefs["objective"].replace("_", " ")} priority. ' if prefs['budget_gbp'] is not None else 'Using your saved exclusions and feedback. ')
            response.explanation = summary + response.explanation
        return response
