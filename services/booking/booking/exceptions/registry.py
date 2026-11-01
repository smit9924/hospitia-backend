from typing import Any

from jwt import (
    DecodeError,
    ExpiredSignatureError,
    ImmatureSignatureError,
    InvalidAlgorithmError,
    InvalidAudienceError,
    InvalidIssuedAtError,
    InvalidIssuerError,
    InvalidKeyError,
    InvalidSignatureError,
    InvalidTokenError,
    MissingRequiredClaimError,
)

from booking.exceptions.definitions.messaging_queue_exceptions import (
    MQMessagePublishException,
    MQNotFoundException,
)
from booking.exceptions.definitions.not_found_exceptions import (
    AddressNotFoundException,
    CurrencyUnitNotFoundException,
    OrganizationNotFoundException,
    OrganizationTypeNotFoundException,
    OrganizationUserMappingNotFoundException,
    RoomAmenityNotFoundException,
    RoomTypeNotFoundException,
    UserNotFoundException,
)
from booking.exceptions.definitions.security_exceptions import (
    ActiveOrganizationInvalidException,
    OrganizationAccessForbiddenException,
    RoomAmenityModificationForbiddenException,
    UserUnauthorizedException,
)
from booking.exceptions.definitions.validation_exceptions import (
    ActiveOrganizationRequiredException,
    CurrencyUnitAlreadyExistsException,
    CurrencyUnitInUseException,
    OrganizationHasActiveDependenciesException,
    OrganizationMustHaveActiveOwnerException,
    OrganizationTypeAlreadyExistsException,
    OrganizationTypeHasActiveOrganizationsException,
    RoomAmenityAlreadyExistsException,
    RoomAmenityInUseException,
    RoomTypeAlreadyExistsException,
    RoomTypeAmenityNotAvailableException,
    RoomTypeOrganizationRequiredException,
    UserRoleMismatchForOrganizationException,
)
from booking.exceptions.handlers.messaging_queue_exceptions_handlers import (
    mq_message_publish_exception_handler,
    mq_not_found_exception_handler,
)
from booking.exceptions.handlers.not_found_exceptions_handlers import (
    address_not_found_exception_handler,
    currency_unit_not_found_exception_handler,
    organization_not_found_exception_handler,
    organization_type_not_found_exception_handler,
    organization_user_mapping_not_found_exception_handler,
    room_amenity_not_found_exception_handler,
    room_type_not_found_exception_handler,
    user_not_found_exception_handler,
)
from booking.exceptions.handlers.security_exceptions_handlers import (
    active_organization_invalid_exception_handler,
    decode_error_exception_handler,
    expired_signature_error_exception_handler,
    immature_signature_error_exception_handler,
    invalid_algorithm_error_exception_handler,
    invalid_audience_error_exception_handler,
    invalid_issued_at_error_exception_handler,
    invalid_issuer_error_exception_handler,
    invalid_key_error_exception_handler,
    invalid_signature_error_exception_handler,
    invalid_token_error_exception_handler,
    missing_required_claim_error_exception_handler,
    organization_access_forbidden_exception_handler,
    room_amenity_modification_forbidden_exception_handler,
    user_unauthorized_exception_handler,
)
from booking.exceptions.handlers.validation_exception_handlers import (
    active_organization_required_exception_handler,
    currency_unit_already_exists_exception_handler,
    currency_unit_in_use_exception_handler,
    organization_has_active_dependencies_exception_handler,
    organization_must_have_active_owner_exception_handler,
    organization_type_already_exists_exception_handler,
    organization_type_has_active_organizations_exception_handler,
    room_amenity_already_exists_exception_handler,
    room_amenity_in_use_exception_handler,
    room_type_already_exists_exception_handler,
    room_type_amenity_not_available_exception_handler,
    room_type_organization_required_exception_handler,
    user_role_mismatch_for_organization_exception_handler,
)


def get_exception_handlers() -> dict[Any, Any]:
    """
    Returns a mapping of custom exception types to their corresponding
    FastAPI exception handler callables.
    """
    return {
        # Register CUSTOM SECURITY EXCEPTION handlers
        UserUnauthorizedException: user_unauthorized_exception_handler,
        OrganizationAccessForbiddenException: organization_access_forbidden_exception_handler,
        ActiveOrganizationInvalidException: active_organization_invalid_exception_handler,
        RoomAmenityModificationForbiddenException: room_amenity_modification_forbidden_exception_handler,

        # Register PYJWT SECURITY EXCEPTION handlers
        ExpiredSignatureError: expired_signature_error_exception_handler,
        InvalidTokenError: invalid_token_error_exception_handler,
        InvalidSignatureError: invalid_signature_error_exception_handler,
        InvalidKeyError: invalid_key_error_exception_handler,
        InvalidAlgorithmError: invalid_algorithm_error_exception_handler,
        InvalidAudienceError: invalid_audience_error_exception_handler,
        InvalidIssuerError: invalid_issuer_error_exception_handler,
        InvalidIssuedAtError: invalid_issued_at_error_exception_handler,
        ImmatureSignatureError: immature_signature_error_exception_handler,
        MissingRequiredClaimError: missing_required_claim_error_exception_handler,
        DecodeError: decode_error_exception_handler,

        # Register NOT FOUND EXCEPTION handlers
        UserNotFoundException: user_not_found_exception_handler,
        OrganizationTypeNotFoundException: organization_type_not_found_exception_handler,
        AddressNotFoundException: address_not_found_exception_handler,
        OrganizationNotFoundException: organization_not_found_exception_handler,
        OrganizationUserMappingNotFoundException: organization_user_mapping_not_found_exception_handler,
        CurrencyUnitNotFoundException: currency_unit_not_found_exception_handler,
        RoomAmenityNotFoundException: room_amenity_not_found_exception_handler,
        RoomTypeNotFoundException: room_type_not_found_exception_handler,

        # Register VALIDATION EXCEPTION handlers
        OrganizationTypeAlreadyExistsException: organization_type_already_exists_exception_handler,
        OrganizationTypeHasActiveOrganizationsException: organization_type_has_active_organizations_exception_handler,
        OrganizationHasActiveDependenciesException: organization_has_active_dependencies_exception_handler,
        OrganizationMustHaveActiveOwnerException: organization_must_have_active_owner_exception_handler,
        UserRoleMismatchForOrganizationException: user_role_mismatch_for_organization_exception_handler,
        ActiveOrganizationRequiredException: active_organization_required_exception_handler,
        CurrencyUnitAlreadyExistsException: currency_unit_already_exists_exception_handler,
        CurrencyUnitInUseException: currency_unit_in_use_exception_handler,
        RoomAmenityAlreadyExistsException: room_amenity_already_exists_exception_handler,
        RoomAmenityInUseException: room_amenity_in_use_exception_handler,
        RoomTypeAlreadyExistsException: room_type_already_exists_exception_handler,
        RoomTypeAmenityNotAvailableException: room_type_amenity_not_available_exception_handler,
        RoomTypeOrganizationRequiredException: room_type_organization_required_exception_handler,

        # Register MESSAGING QUEUE EXCEPTION handlers
        MQNotFoundException: mq_not_found_exception_handler,
        MQMessagePublishException: mq_message_publish_exception_handler,
    }
