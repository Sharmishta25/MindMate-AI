"""Strict bounded transport parser: reject duplicate keys and non-JSON constants."""
import json


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


def _constant(_value):
    raise ValueError("Nonfinite JSON value")


def loads(value):
    return json.loads(value, object_pairs_hook=_pairs, parse_constant=_constant)
