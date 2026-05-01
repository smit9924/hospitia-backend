from auth.schemas.common_schemas import ApiErrorResponse
from auth.schemas.exception_data_schemas import PublicEmailNotAllowedExceptionMetadata
from auth.types.error_codes import ErrorCodes

VALIDATION_EXCEPTION_DOC = {
    "PublicEmailNotAllowedException": {
        409: {
            "description": "Public email domains are not allowed.",
            "model": ApiErrorResponse[PublicEmailNotAllowedExceptionMetadata],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": {
                            "field": "email",
                            "input": "test@gmail.com",
                            "data": "gmail.com"
                        },
                        "message": "Public email domains are not allowed. Please use a business email address.",
                        "errorCode": ErrorCodes.PUBLIC_EMAIL_NOW_ALLOWED
                    }
                }
            },
        }
    },
    "UserWithEmailAlreadyExistsException": {
        409: {
            "description": "User with given email already exists.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": "None",
                        "message": "A user with the provided email address already exists.",
                        "errorCode": ErrorCodes.USER_WITH_EMAIL_ALREADY_EXIST
                    }
                }
            },
        }
    },
    "UserWithUsernameAlreadyExistsException": {
        409: {
            "description": "User with given username already exists.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": "None",
                        "message": "A user with the provided username already exists.",
                        "errorCode": ErrorCodes.USER_WITH_USENAME_ALREADY_EXIST
                    }
                }
            },
        }
    },
}
