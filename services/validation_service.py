import re

DISPOSABLE_EMAIL_DOMAINS = {
    "tempmail.com", "mailinator.com", "10minutemail.com", "guerrillamail.com",
    "yopmail.com", "trashmail.com", "fake.com",
    "dispostable.com", "sharklasers.com", "getairmail.com", "throwawaymail.com",
    "temp-mail.org", "maildrop.cc", "mohmal.com", "inboxkitten.com"
}

class AccountValidationService:
    @staticmethod
    def validate_username(username: str) -> str:
        clean_username = username.strip()
        if len(clean_username) < 2:
            raise ValueError("Username must be at least 2 characters in length")
        if len(clean_username) > 50:
            raise ValueError("Username cannot exceed 50 characters in length")
        return clean_username

    @staticmethod
    def validate_email(email_address: str) -> str:
        clean_email = email_address.strip().lower()
        if "@" not in clean_email or "." not in clean_email.split("@")[-1]:
            raise ValueError("Invalid email format")
        domain_part = clean_email.split("@")[-1]
        if domain_part in DISPOSABLE_EMAIL_DOMAINS:
            raise ValueError("Disposable temporary emails are not permitted")
        return clean_email

    @staticmethod
    def validate_password(password: str) -> str:
        clean_password = password.strip()
        if len(clean_password) < 4:
            raise ValueError("Password must be at least 4 characters long")
        return password
