"""F7-013 — buyer / supplier ayrı rate scope."""

from rest_framework.throttling import UserRateThrottle


class BuyerRateThrottle(UserRateThrottle):
    scope = "buyer"


class SupplierRateThrottle(UserRateThrottle):
    scope = "supplier"


class OpsRateThrottle(UserRateThrottle):
    scope = "ops"
