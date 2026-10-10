import json
from pathlib import Path
from app.schemas.engines import PropertyRecord


class JsonPropertyRepository:
    def __init__(self, path: Path):
        records = [PropertyRecord.model_validate(row) for row in json.loads(path.read_text())]
        self._records = {row.property.property_id: row for row in records}
        if len(self._records) != len(records):
            raise ValueError('Duplicate property IDs in repository')

    def list_properties(self):
        return [row.model_copy(deep=True) for row in self._records.values()]

    def load_property(self, property_id):
        if property_id not in self._records:
            raise KeyError(property_id)
        return self._records[property_id].model_copy(deep=True)
