# Our models' prices are set in Langfuse when a service starts (trace_prices.py), within this
# long, so a slow Langfuse never holds up a start.
PRICE_SYNC_SECONDS = 5
# Langfuse's model definitions, read this many a page.
MODELS_PAGE = 100
