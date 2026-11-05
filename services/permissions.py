ADMIN = "admin"
RESEARCHER = "researcher"
ROLES = (ADMIN, RESEARCHER)

ARTICLES_READ = "articles:read"
ARTICLES_CREATE = "articles:create"
USERS_MANAGE = "users:manage"

ROLE_PERMISSIONS = {
    RESEARCHER: {ARTICLES_READ, ARTICLES_CREATE},
    ADMIN: {ARTICLES_READ, ARTICLES_CREATE, USERS_MANAGE},
}


def has_permission(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())


def permissions_for(role: str) -> list:
    return sorted(ROLE_PERMISSIONS.get(role, set()))
