"""Routes that read files from disk (guide articles, legal versions) are plain functions, so
FastAPI runs them in its thread pool rather than on the event loop every request shares."""

import inspect

from site_content.api.v1 import help as routes


def test_routes_that_read_files_run_off_the_event_loop():
    for route in (routes.list_guides, routes.get_guide_article, routes.get_legal):
        assert not inspect.iscoroutinefunction(route), route.__name__
