"""Package initializer for route blueprints.

This module provides a helper that automatically discovers all Python
modules in the `routes` package, imports them, and registers any
`flask.Blueprint` objects found on the Flask application.

Usage ::

    from routes import register_routes
    register_routes(app)
"""

import os
import pkgutil
import importlib
from flask import Blueprint


def register_routes(app):
    """Register all blueprints defined in this package on *app*.

    Scans the filesystem for modules in the same directory as this
    file, imports each one, and inspects its attributes for ``Blueprint``
    instances.  Any that are found are registered automatically.
    """

    package_dir = os.path.dirname(__file__)
    package_name = __name__

    for finder, module_name, is_pkg in pkgutil.iter_modules([package_dir]):
        # skip subpackages for now (shouldn't be any)
        if is_pkg:
            continue

        full_name = f"{package_name}.{module_name}"
        try:
            module = importlib.import_module(full_name)
        except ImportError:
            # log or re-raise depending on needs; we'll just continue
            continue

        # scan module for Blueprint instances
        for obj_name in dir(module):
            obj = getattr(module, obj_name)
            if isinstance(obj, Blueprint):
                app.register_blueprint(obj)
