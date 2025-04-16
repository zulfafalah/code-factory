import uuid


def generate_nameming_series(prefix: str):
    """
    Generates a name series string with a given prefix and a unique ID.

    For example: ABD250300001
    """
    unique_id = str(uuid.uuid4().int)[:9]
    padded_id = unique_id.zfill(9)
    return f"{prefix}{padded_id}"
