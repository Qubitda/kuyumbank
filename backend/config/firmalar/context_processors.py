"""Act-as banner context — ADR-0021."""


def act_as(request):
    active = getattr(request, "act_as_active", False)
    actor = getattr(request, "act_as_actor", None)
    user = getattr(request, "user", None)
    return {
        "act_as_active": active,
        "act_as_actor": actor,
        "act_as_target": user if active else None,
    }
