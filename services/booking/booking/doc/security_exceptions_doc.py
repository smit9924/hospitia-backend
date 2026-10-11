from booking.schemas.common_schemas import ApiErrorResponse
from booking.types.error_codes import ErrorCodes

SECURITY_EXCEPTION_DOC = {
    "UserUnauthorizedException": {
        401: {
            "description": "Authentication or role authorization failed.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "You are not authorized to perform this action. Please authenticate and try again.",
                        "errorCode": ErrorCodes.UNAUTHORIZED,
                    }
                }
            },
        }
    },
    "OrganizationAccessForbiddenException": {
        403: {
            "description": "The authenticated user cannot access this organization.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "You do not have access to this organization.",
                        "errorCode": ErrorCodes.ORGANIZATION_ACCESS_FORBIDDEN,
                    }
                }
            },
        }
    },
    "InvalidTokenException": {
        401: {
            "description": "The access token is invalid, expired, or malformed.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "Invalid access token. Please provide a valid token.",
                        "errorCode": ErrorCodes.UNAUTHORIZED,
                    }
                }
            },
        }
    },
}
