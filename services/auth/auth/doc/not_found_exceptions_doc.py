from auth.schemas.common_schemas import ApiErrorResponse
from auth.types.error_codes import ErrorCodes

NOT_FOUND_EXCEPTIONS_DOC = {
    "UserNotFoundException": {
        404: {
            "description": "The requested user was not found.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": "None",
                        "message": "The requested user was not found.",
                        "errorCode": ErrorCodes.USER_NOT_FOUND
                    }
                }
            },
        }
    },
}
