# Backend architecture

```mermaid
flowchart TD
    UI[Frontend] --> API[FastAPI routes]
    API --> Models[Pydantic validation]
    API --> Repo[Property repository]
    Models --> Score[Score and issue detection]
    Models --> Scenario[Scenario orchestrator]
    Scenario --> Feasible[P4 feasibility]
    Feasible --> Simulate[P4 interacting retrofit simulation]
    Simulate --> After[Updated property and fuel states]
    After --> Score
    After --> Carbon[P4 carbon adapter]
    After --> Value[P5 valuation adapter]
    Score --> Response[Typed response]
    Carbon --> Response
    Value --> Response
    Response --> UI
```

FastAPI routes depend on provider functions, enabling test-only adapters and explicit future integrations. Domain scoring remains independent of HTTP and LLM services. Scenario orchestration uses isolated input copies, preserves recorded EPC and fixed property characteristics, derives signed fuel savings, verifies carbon arithmetic, and returns unavailable subresults without manufacturing values.

Current runtime: synthetic JSON property repository, real scoring logic, pending retrofit/carbon adapters, existing P5 valuation adapter. Default scenario cannot run until feasibility/simulation is integrated. Tests inject fixture engines and validate orchestration, not predictive accuracy.

Backend-owned files contain no code comments or docstrings per the user's preference. Existing teammate modules are unchanged.
