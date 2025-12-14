from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Validates a plaintext password against a bcrypt-hashed password.

    Parameters
    ----------
    plain_password : str
        The plaintext password to validate.

    hashed_password : str
        The bcrypt-hashed password to validate against.

    Returns
    -------
    bool
        True if the plaintext password matches the hashed password, otherwise False.
    """
    return checkpw(
        bytes(plain_password, encoding="utf-8"),
        bytes(hashed_password, encoding="utf-8"),
    )


def get_password_hash(password: str) -> str:
    """
    Create a bcrypt hash from the given plaintext password.

    Parameters
    ----------
    password : str
        The plaintext password to hash.

    Returns
    -------
    str
        The bcrypt-hashed password as a UTF-8 decoded string (includes salt).
    """
    password_hash_byte = hashpw(
        bytes(password, encoding="utf-8"),
        gensalt(),
    )

    password_hash_string = password_hash_byte.decode("utf-8")

    return password_hash_string
