from app.db.repository import load_property_energy_data

record = load_property_energy_data("P00001")
print(record)
# Use record["property"], record["annual_energy"], and record["monthly_energy"]