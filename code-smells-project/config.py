import os
from datetime import datetime


class Config:
    DATABASE = os.environ.get("DATABASE", "loja.db")
    SECRET_KEY = os.environ.get("SECRET_KEY")
    APP_ENV = os.environ.get("APP_ENV", "production")
    DEBUG = False
    TOKEN_MAX_AGE = 3600
    SEED_DATA = False
    AUTO_INIT_DB = False
    LEGACY_PASSWORD_CUTOFF = os.environ.get(
        'LEGACY_PASSWORD_CUTOFF', '2027-01-01T00:00:00+00:00'
    )

    @classmethod
    def validate(cls, values):
        if not values.get("SECRET_KEY"):
            raise RuntimeError("SECRET_KEY is required")
        cutoff = datetime.fromisoformat(values['LEGACY_PASSWORD_CUTOFF'])
        if cutoff.tzinfo is None:
            raise RuntimeError('LEGACY_PASSWORD_CUTOFF requires a timezone')

