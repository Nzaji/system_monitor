import json
from decimal import Decimal

def strict_serialize(obj):
    """Convertit tous les types numériques en float Python natif"""
    if isinstance(obj, (int, float, Decimal)):
        return float(obj)
    raise TypeError(f"Type non sérialisable: {type(obj)}")

class StrictEncoder(json.JSONEncoder):
    def default(self, obj):
        return strict_serialize(obj)
