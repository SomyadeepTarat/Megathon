from app.schemas.engines import CarbonResult, FeasibilityResult, ValuationResult


class PendingRetrofitEngine:
    version = 'not-integrated'
    def check_feasibility(self, request):
        return FeasibilityResult(status='unavailable', reason='P4 retrofit feasibility engine is not integrated.')
    def simulate_retrofits(self, request):
        raise RuntimeError('Simulation must not run without available feasibility')


class PendingCarbonEngine:
    def calculate_carbon(self, energy):
        return CarbonResult(status='unavailable', reason='P4 carbon engine and documented fuel factors are not integrated.')


class ExistingValuationAdapter:
    def predict_scenario_impact(self, request, scenario, energy):
        if request.annual_energy.quality == 'synthetic' and request.property.provenance.get('record') == 'synthetic':
            try:
                from ml.synthetic_impact import predict_impact
                result = predict_impact(request.property, scenario, energy)
            except ImportError:
                return ValuationResult(status='unavailable', reason='Synthetic valuation dependencies unavailable.')
            return ValuationResult.model_validate(result)
        if request.property.model_dump() != scenario.model_dump() and request.property.energy_rating == scenario.energy_rating:
            return ValuationResult(status='unavailable', reason='No supported projected EPC estimate for observed/estimated inputs.')
        return self.predict_value_impact(request.property, scenario)

    @staticmethod
    def to_features(prop):
        row = prop.model_dump(mode='json')
        row.update(floor_area=prop.floor_area_m2, age=prop.property_age_years)
        return row

    def predict_value_impact(self, baseline, scenario):
        try:
            from app.services.valuation_service import predict_value_impact
        except ImportError:
            return ValuationResult(status='unavailable', reason='Valuation dependencies unavailable; install ml/requirements.txt.')
        result = predict_value_impact(self.to_features(baseline), self.to_features(scenario),
                                      allow_illustrative=False)
        return ValuationResult.model_validate(result)
