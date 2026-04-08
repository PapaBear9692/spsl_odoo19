# Copyright 2026 SPSL - Smart Printing Service Limited
# License OPL-1 (https://www.odoo.com/documentation/16.0/applications/general/modules.html#module-structure)

# Test modules will be imported here
# Example: from . import test_approval
from odoo.tests.common import TransactionCase


class TestSPSLCoreBase(TransactionCase):
    """Base test class for SPSL Core module tests."""

    def setUp(self):
        super().setUp()
