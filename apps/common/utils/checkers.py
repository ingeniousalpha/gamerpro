from uuid import UUID


def is_valid_uuid(value, version=4):
    try:
        uuid_obj = UUID(value, version=version)
        return True
    except ValueError:
        return False
