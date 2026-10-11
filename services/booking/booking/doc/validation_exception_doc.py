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
}
