from booking.schemas.common_schemas import ApiErrorResponse
from booking.types.error_codes import ErrorCodes

VALIDATION_EXCEPTION_DOC = {
    "OrganizationTypeAlreadyExistsException": {
        409: {
            "description": "An organization type with the requested name already exists.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "An organization type with this name already exists.",
                        "errorCode": ErrorCodes.ORGANIZATION_TYPE_ALREADY_EXISTS,
                    }
                }
            },
        }
    },
    "OrganizationTypeHasActiveOrganizationsException": {
        409: {
            "description": "The organization type is still used by an active organization.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "Cannot delete an organization type that is still in use.",
                        "errorCode": ErrorCodes.ORGANIZATION_TYPE_HAS_ACTIVE_ORGANIZATIONS,
                    }
                }
            },
        }
    },
    "OrganizationHasActiveDependenciesException": {
        409: {
            "description": "The organization has active dependencies and cannot be deleted.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "Cannot delete an organization with active dependencies.",
                        "errorCode": ErrorCodes.ORGANIZATION_HAS_ACTIVE_DEPENDENCIES,
                    }
                }
            },
        }
    },
    "OrganizationMustHaveActiveOwnerException": {
        409: {
            "description": "The operation would leave the organization without an active owner.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "An organization must always have at least one active owner.",
                        "errorCode": ErrorCodes.ORGANIZATION_MUST_HAVE_ACTIVE_OWNER,
                    }
                }
            },
        }
    },
    "UserRoleMismatchForOrganizationException": {
        400: {
            "description": "The selected user does not have the required organization role.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "The selected user does not have the required role for this assignment.",
                        "errorCode": ErrorCodes.USER_ROLE_MISMATCH_FOR_ORGANIZATION,
                    }
                }
            },
        }
    },
    "ActiveOrganizationRequiredException": {
        400: {
            "description": "The X-Active-Organization-Guid header is missing or is not a valid UUID.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "An active organization is required for this request.",
                        "errorCode": ErrorCodes.ACTIVE_ORGANIZATION_REQUIRED,
                    }
                }
            },
        }
    },
    "CurrencyUnitAlreadyExistsException": {
        409: {
            "description": "A currency unit with this code already exists.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "A currency unit with this code already exists.",
                        "errorCode": ErrorCodes.CURRENCY_UNIT_ALREADY_EXISTS,
                    }
                }
            },
        }
    },
    "CurrencyUnitInUseException": {
        409: {
            "description": "Cannot delete a currency unit that is still in use.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "Cannot delete a currency unit that is still in use.",
                        "errorCode": ErrorCodes.CURRENCY_UNIT_IN_USE,
                    }
                }
            },
        }
    },
    "RoomAmenityAlreadyExistsException": {
        409: {
            "description": "A room amenity with this name already exists.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "A room amenity with this name already exists.",
                        "errorCode": ErrorCodes.ROOM_AMENITY_ALREADY_EXISTS,
                    }
                }
            },
        }
    },
    "RoomAmenityInUseException": {
        409: {
            "description": "Cannot delete a room amenity that is still in use.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "Cannot delete a room amenity that is still in use.",
                        "errorCode": ErrorCodes.ROOM_AMENITY_IN_USE,
                    }
                }
            },
        }
    },
}
