from sqlalchemy import BigInteger, cast, func


def paid_minor(model):
    """What a top-up, refund or chargeback moved, in minor units, as a query expression on
    `Entry` or `Purchase`: the integer column, or the old text one for a row an older version
    wrote during a deploy (migration 0020). The fallback goes with the text column."""
    return func.coalesce(model.total_minor, cast(model.total, BigInteger))
