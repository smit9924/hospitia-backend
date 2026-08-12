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
    "WeakPasswordException": {
        409: {
            "description": "Provided password does not meet strength requirements.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": "None",
                        "message": "The provided password is too weak. Password must be at least 8 characters long and include uppercase letters, lowercase letters, numbers, and special characters.",
                        "errorCode": ErrorCodes.WEAK_PASSWORD
                    }
                }
            },
        }
    },
    "InvalidUsernameException": {
        409: {
            "description": "Provided username is invalid.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": "None",
                        "message": "The provided username is invalid. Please choose a different username.",
                        "errorCode": ErrorCodes.INVALID_USERNAME
                    }
                }
            },
        }
    },
    "EmailAlreadyVerifiedException": {
        409: {
            "description": "User email is already verified.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": "None",
                        "message": "Your email address has already been verified.",
                        "errorCode": ErrorCodes.EMAIL_ALREADY_VERIFIED
                    }
                }
            },
        }
    },
    "InvalidOtpException": {
        400: {
            "description": "Provided OTP is invalid or expired.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": "None",
                        "message": "The provided OTP is invalid or has expired.",
                        "errorCode": ErrorCodes.INVALID_OTP
                    }
                }
            },
        }
    },
}
