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
    "RoomTypeAlreadyExistsException": {
        409: {
            "description": "A room type with this name already exists in this organization.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "A room type with this name already exists in this organization.",
                        "errorCode": ErrorCodes.ROOM_TYPE_ALREADY_EXISTS,
                    }
                }
            },
        }
    },
    "RoomTypeAmenityNotAvailableException": {
        400: {
            "description": "One or more selected amenities are not available for this organization.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "One or more selected amenities are not available for this organization.",
                        "errorCode": ErrorCodes.ROOM_TYPE_AMENITY_NOT_AVAILABLE,
                    }
                }
            },
        }
    },
    "RoomTypeOrganizationRequiredException": {
        400: {
            "description": "Select the organization the room type belongs to.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "Select the organization the room type belongs to.",
                        "errorCode": ErrorCodes.ROOM_TYPE_ORGANIZATION_REQUIRED,
                    }
                }
            },
        }
    },
    "RoomAlreadyExistsException": {
        409: {
            "description": "A room with this number already exists in this organization.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "A room with this number already exists in this organization.",
                        "errorCode": ErrorCodes.ROOM_ALREADY_EXISTS,
                    }
                }
            },
        }
    },
    "RoomOrganizationRequiredException": {
        400: {
            "description": "Select the organization the room belongs to.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "Select the organization the room belongs to.",
                        "errorCode": ErrorCodes.ROOM_ORGANIZATION_REQUIRED,
                    }
                }
            },
        }
    },
    "RoomTypeNotAvailableForRoomException": {
        400: {
            "description": "The selected room type is not available for this organization.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "The selected room type is not available for this organization.",
                        "errorCode": ErrorCodes.ROOM_TYPE_NOT_AVAILABLE_FOR_ROOM,
                    }
                }
            },
        }
    },
    "RoomTypeInUseException": {
        409: {
            "description": "This room type has rooms and cannot be deleted.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "This room type has rooms and cannot be deleted.",
                        "errorCode": ErrorCodes.ROOM_TYPE_IN_USE,
                    }
                }
            },
        }
    },
    "BookingOrganizationRequiredException": {
        400: {
            "description": "Select the organization the booking belongs to.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "Select the organization the booking belongs to.",
                        "errorCode": ErrorCodes.BOOKING_ORGANIZATION_REQUIRED,
                    }
                }
            },
        }
    },
    "BookingRoomUnavailableException": {
        409: {
            "description": "This room is not available for the selected dates.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "This room is not available for the selected dates.",
                        "errorCode": ErrorCodes.BOOKING_ROOM_UNAVAILABLE,
                    }
                }
            },
        }
    },
    "BookingGuestCapacityExceededException": {
        400: {
            "description": "This room does not fit that many guests.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "This room does not fit that many guests.",
                        "errorCode": ErrorCodes.BOOKING_GUEST_CAPACITY_EXCEEDED,
                    }
                }
            },
        }
    },
    "BookingPrimaryGuestRequiredException": {
        400: {
            "description": "Add the primary guest with a phone number and an ID proof.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "Add the primary guest with a phone number and an ID proof.",
                        "errorCode": ErrorCodes.BOOKING_PRIMARY_GUEST_REQUIRED,
                    }
                }
            },
        }
    },
    "BookingInvalidDatesException": {
        400: {
            "description": "The check-in and check-out dates are not valid.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "The check-in and check-out dates are not valid.",
                        "errorCode": ErrorCodes.BOOKING_INVALID_DATES,
                    }
                }
            },
        }
    },
    "BookingInvalidStatusTransitionException": {
        409: {
            "description": "This action is not possible for the booking's current status.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "This action is not possible for the booking's current status.",
                        "errorCode": ErrorCodes.BOOKING_INVALID_STATUS_TRANSITION,
                    }
                }
            },
        }
    },
    "BookingNotEditableException": {
        409: {
            "description": "This booking can no longer be changed.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "This booking can no longer be changed.",
                        "errorCode": ErrorCodes.BOOKING_NOT_EDITABLE,
                    }
                }
            },
        }
    },
    "RoomHasActiveBookingsException": {
        409: {
            "description": "This room has active bookings and can't be deleted.",
            "model": ApiErrorResponse[None],
            "content": {
                "application/json": {
                    "example": {
                        "metadata": None,
                        "message": "This room has active bookings and can't be deleted.",
                        "errorCode": ErrorCodes.ROOM_HAS_ACTIVE_BOOKINGS,
                    }
                }
            },
        }
    },
}
