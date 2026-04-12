from django.conf import settings
from rest_framework.response import Response


def set_token_cookies(
    response: Response,
    access_token: str | None = None,
    refresh_token: str | None = None,
) -> None:
    cookie_settings = {
        'secure': settings.SIMPLE_JWT.get("AUTH_COOKIE_SECURE", False),
        'httponly': settings.SIMPLE_JWT.get("AUTH_COOKIE_HTTP_ONLY", True),
        'samesite': settings.SIMPLE_JWT.get("AUTH_COOKIE_SAMESITE", "Lax"),
        'domain': settings.SIMPLE_JWT.get("AUTH_COOKIE_DOMAIN", None),
        'path': '/',
    }
    
    if access_token:
        max_age_access = int(settings.SIMPLE_JWT.get("ACCESS_TOKEN_LIFETIME").total_seconds())
        response.set_cookie(
            key=settings.SIMPLE_JWT.get("AUTH_COOKIE_ACCESS", "access_token"),
            value=access_token,
            max_age=max_age_access,
            **cookie_settings
        )
    
    if refresh_token:
        max_age_refresh = int(settings.SIMPLE_JWT.get("REFRESH_TOKEN_LIFETIME").total_seconds())
        response.set_cookie(
            key=settings.SIMPLE_JWT.get("AUTH_COOKIE_REFRESH", "refresh_token"),
            value=refresh_token,
            max_age=max_age_refresh,
            **cookie_settings
        )


def delete_token_cookies(response: Response) -> None:

    delete_settings = {
        'domain': settings.SIMPLE_JWT.get("AUTH_COOKIE_DOMAIN", None),
        'samesite': settings.SIMPLE_JWT.get("AUTH_COOKIE_SAMESITE", "Lax"),
        'path': '/',
    }
    
    response.delete_cookie(
        settings.SIMPLE_JWT.get("AUTH_COOKIE_ACCESS", "access_token"),
        **delete_settings
    )
    
    response.delete_cookie(
        settings.SIMPLE_JWT.get("AUTH_COOKIE_REFRESH", "refresh_token"),
        **delete_settings
    )
    
