from auth.schemas.common_schemas import ApiErrorResponse
from auth.types.error_codes import ErrorCodes

SECURITY_EXCEPTION_DOC = {
    "UserUnauthorizedException": {
        401: {
            "description": "Authentication failed or user is not authorized to access this resource.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": "None",
                        "message": "You are not authorized to perform this action. Please authenticate and try again.",
                        "errorCode": ErrorCodes.UNAUTHORIZED
                    }
                }
            },
        }
    },
    "ExpiredSignatureError": {
        401: {
            "description": "JWT access token has expired.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": "None",
                        "message": "Access token has expired. Please authenticate again.",
                        "errorCode": ErrorCodes.INVALIDTOKEN
                    }
                }
            },
        }
    },
    "InvalidTokenError": {
        401: {
            "description": "JWT token is invalid, malformed, or tampered with.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": "None",
                        "message": "Invalid access token.",
                        "errorCode": ErrorCodes.INVALIDTOKEN
                    }
                }
            },
        }
    },
    "InvalidSignatureError": {
        401: {
            "description": "JWT signature verification failed.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": "None",
                        "message": "Invalid access token signature.",
                        "errorCode": ErrorCodes.INVALIDTOKEN
                    }
                }
            },
        }
    },
    "InvalidKeyError": {
        401: {
            "description": "JWT signing or verification key is invalid.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": "None",
                        "message": "Invalid token verification key.",
                        "errorCode": ErrorCodes.INVALIDTOKEN
                    }
                }
            },
        }
    },
    "InvalidAlgorithmError": {
        401: {
            "description": "JWT uses an unsupported algorithm.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": "None",
                        "message": "Unsupported token algorithm.",
                        "errorCode": ErrorCodes.INVALIDTOKEN
                    }
                }
            },
        }
    },
    "InvalidAudienceError": {
        401: {
            "description": "JWT audience claim is invalid.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": "None",
                        "message": "Invalid token audience.",
                        "errorCode": ErrorCodes.INVALIDTOKEN
                    }
                }
            },
        }
    },
    "InvalidIssuerError": {
        401: {
            "description": "JWT issuer claim is invalid.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": "None",
                        "message": "Invalid token issuer.",
                        "errorCode": ErrorCodes.INVALIDTOKEN
                    }
                }
            },
        }
    },
    "InvalidIssuedAtError": {
        401: {
            "description": "JWT issued-at claim is invalid.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": "None",
                        "message": "Invalid token issued time.",
                        "errorCode": ErrorCodes.INVALIDTOKEN
                    }
                }
            },
        }
    },
    "ImmatureSignatureError": {
        401: {
            "description": "JWT token is not yet valid (nbf claim).",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": "None",
                        "message": "Access token is not yet valid.",
                        "errorCode": ErrorCodes.INVALIDTOKEN
                    }
                }
            },
        }
    },
    "MissingRequiredClaimError": {
        401: {
            "description": "JWT is missing required claims.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": "None",
                        "message": "Token is missing required claims.",
                        "errorCode": ErrorCodes.INVALIDTOKEN
                    }
                }
            },
        }
    },
    "DecodeError": {
        401: {
            "description": "JWT cannot be decoded or is malformed.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": "None",
                        "message": "Malformed access token.",
                        "errorCode": ErrorCodes.INVALIDTOKEN
                    }
                }
            },
        }
    },
    "InvalidCredentialsException": {
        401: {
            "description": "Incorrect username/email or password.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": "None",
                        "message": "Incorrect username or password.",
                        "errorCode": ErrorCodes.INVALID_CREDENTIALS
                    }
                }
            },
        }
    },
    "UserInactiveException": {
        403: {
            "description": "User account is inactive.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": "None",
                        "message": "Your account is inactive. Please contact support or activate your account.",
                        "errorCode": ErrorCodes.USER_INACTIVE
                    }
                }
            },
        }
    },
    "InvalidTokenException": {
        401: {
            "description": "Provided token is invalid, expired, or malformed.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": "None",
                        "message": "Invalid token. Please provide a valid token and try again.",
                        "errorCode": ErrorCodes.INVALIDTOKEN
                    }
                }
            }
        }
    },
}
