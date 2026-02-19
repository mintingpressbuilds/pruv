"""Scope definition, validation, and in-scope checking."""


def check_scope(action_scope: str, declared_scope: list[str]) -> bool:
    """Check if an action_scope falls within the declared scope.

    Args:
        action_scope: The scope item the action claims to be under.
        declared_scope: The list of scope items declared at registration.

    Returns:
        True if action_scope is in declared_scope, False otherwise.
    """
    return action_scope in declared_scope
