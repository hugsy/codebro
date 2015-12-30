import unipath

from django.core.exceptions import ValidationError


def validate_PathNotEmpty(value):
    """

    """
    path = unipath.Path(value).strip()
    if len(path) == 0:
        raise ValidationError(u'String must not be empty')


def validate_PathInScope(value):
    """

    """
    path = unipath.Path(value)
    path.absolute()
    if not abspath.startswith(settings.SRC_PATH) or not path.isdir(abspath):
        raise ValidationError(u'Invalid path for source code')


def validate_IsValidName(value):
    """

    """
    validate_PathNotEmpty(value)
    path = unipath.Path(value)

    if not path.isalnum():
        raise ValidationError(u'Project name must be alnum')
