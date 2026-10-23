import os

def load_config():
    return dict(SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL','sqlite:///tasks.db'),
                SQLALCHEMY_TRACK_MODIFICATIONS=False, SECRET_KEY=os.getenv('SECRET_KEY'),
                TOKEN_MAX_AGE=int(os.getenv('TOKEN_MAX_AGE','3600')),
                LEGACY_MD5_CUTOFF=os.getenv('LEGACY_MD5_CUTOFF','2027-01-01T00:00:00+00:00'))
