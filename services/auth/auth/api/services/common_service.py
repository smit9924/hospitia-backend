import re
import secrets
import string


def generate_otp(length: int) -> str:
    """
    Generate a cryptographically secure numeric OTP of the given length.

    Parameters
    ----------
    length : int
        Number of digits in the OTP. Must be a positive integer.

    Returns
    -------
    str
        A zero-padded numeric OTP string of the requested length.
    """
    if length < 1:
        raise ValueError("OTP length must be a positive integer.")

    upper_bound = 10**length
    return str(secrets.randbelow(upper_bound)).zfill(length)


def is_password_strong(password: str | None) -> bool:
    r"""
    Validate the strength of a password based on defined criteria.

    criteria for a strong password:
    -------------------------------
    - Minimum length of 8 characters and maximum length of 50 characters.
    - Contains at least one uppercase letter.
    - Contains at least one lowercase letter.
    - Contains at least one digit.
    - Contains at least one special character (e.g., !@#$%^&*(),.?":{}|<>_-[];'\/+=~`).

    parameters
    ----------
        password : str | None

    returns
    -------
        bool : True if the password is strong, False otherwise.

    """
    if ( password is None
        or len(password) < 8
        or len(password) > 50
        or not re.search(r"[A-Z]", password)
        or not re.search(r"[a-z]", password)
        or not re.search(r"\d", password)
        or not re.search(r"[!@#$%^&*(),.?\":{}|<>\_\-\[\];'/+=~`]", password)
    ):
        return False

    return True


def generate_strong_password(length: int = 16) -> str:
    """
    Generate a cryptographically secure password that satisfies is_password_strong.

    Parameters
    ----------
    length : int
        Desired password length. Must be between 8 and 50 inclusive.

    Returns
    -------
    str
        A randomly generated strong password.
    """
    if length < 8 or length > 50:
        raise ValueError("Password length must be between 8 and 50 characters.")

    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special = "!@#$%^&*(),.?\":{}|<>_-[];'/+=~`"

    # Guarantee at least one character from each required class.
    required = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
        secrets.choice(special),
    ]
    alphabet = uppercase + lowercase + digits + special
    remaining = [secrets.choice(alphabet) for _ in range(length - len(required))]
    password_chars = required + remaining
    secrets.SystemRandom().shuffle(password_chars)
    password = "".join(password_chars)

    if not is_password_strong(password):
        return generate_strong_password(length)

    return password
