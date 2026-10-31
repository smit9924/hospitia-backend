from booking.schemas.common_schemas import ApiErrorResponse
from booking.types.error_codes import ErrorCodes


NOT_FOUND_EXCEPTIONS_DOC = {
    "UserNotFoundException": {
        404: {
            "description": "The authenticated user was not found.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "The requested user was not found.",
                        "errorCode": ErrorCodes.USER_NOT_FOUND,
                    }
                }
            },
        }
    },
    "OrganizationTypeNotFoundException": {
        404: {
            "description": "The requested organization type was not found.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "The requested organization type was not found.",
                        "errorCode": ErrorCodes.ORGANIZATION_TYPE_NOT_FOUND,
                    }
                }
            },
        }
    },
    "OrganizationNotFoundException": {
        404: {
            "description": "The requested organization was not found.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "The requested organization was not found.",
                        "errorCode": ErrorCodes.ORGANIZATION_NOT_FOUND,
                    }
                }
            },
        }
    },
    "OrganizationUserMappingNotFoundException": {
        404: {
            "description": "The requested organization membership was not found.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "The requested organization membership was not found.",
                        "errorCode": ErrorCodes.ORGANIZATION_USER_MAPPING_NOT_FOUND,
                    }
                }
            },
        }
    },
    "CurrencyUnitNotFoundException": {
        404: {
            "description": "The requested currency unit was not found.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "The requested currency unit was not found.",
                        "errorCode": ErrorCodes.CURRENCY_UNIT_NOT_FOUND,
                    }
                }
            },
        }
    },
    "RoomAmenityNotFoundException": {
        404: {
            "description": "The requested room amenity was not found.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "The requested room amenity was not found.",
                        "errorCode": ErrorCodes.ROOM_AMENITY_NOT_FOUND,
                    }
                }
            },
        }
    },
    "RoomTypeNotFoundException": {
        404: {
            "description": "The requested room type was not found.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "The requested room type was not found.",
                        "errorCode": ErrorCodes.ROOM_TYPE_NOT_FOUND,
                    }
                }
            },
        }
    },
}
