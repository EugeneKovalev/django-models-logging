import json

from django.utils.encoding import force_text
from django.contrib.contenttypes.models import ContentType
from django.utils.module_loading import import_string

from . import _local
from .utils import get_changed_data, model_to_dict, ExtendedEncoder
from .settings import ADDED, CHANGED, DELETED, MERGE_CHANGES, MIDDLEWARES, LOGGING_WRITE_DATABASE
from .models import Change
from .settings import CUSTOM_JSON_ENCODER


JSON_ENCODER = ExtendedEncoder
if CUSTOM_JSON_ENCODER:
    JSON_ENCODER = import_string(CUSTOM_JSON_ENCODER)


def init_model_attrs(sender, instance, **kwargs):
    if not _local.ignore(sender, instance):
        model_dict = model_to_dict(instance)
        # for rest_framework
        if not instance.id:
            model_dict = {k: None for k, v in model_dict.items()}

        instance.__attrs = model_dict


def save_model(sender, instance, using, **kwargs):
    if not _local.ignore(sender, instance):
        ignore_on_create = getattr(getattr(instance, 'Logging', object), 'ignore_on_create', False)
        ignore_on_update = getattr(getattr(instance, 'Logging', object), 'ignore_on_update', False)

        action = ADDED if kwargs.get('created') else CHANGED
        if (action == ADDED and not ignore_on_create) or (action == CHANGED and not ignore_on_update):
            diffs = get_changed_data(instance)
            if diffs:
                _create_changes(instance, using, action, uuid=kwargs.get('uuid'))


def delete_model(sender, instance, using, **kwargs):
    if not _local.ignore(sender, instance):
        ignore_on_delete = getattr(getattr(instance, 'Logging', object), 'ignore_on_delete', False)
        if not ignore_on_delete:
            _create_changes(instance, using, DELETED, uuid=kwargs.get('uuid'))


def _create_changes(instance, using, action, uuid=None):
    """
    Creates a `Change` instance
    :param instance: an object which undergone the "action"
    :param using: a database associated with the object
    :param action: action performed to the object `created`/`changed`/`deleted`
    :param uuid: used to mark multiple actions of the same origin
    """
    changed_data = json.dumps(get_changed_data(instance, action), cls=JSON_ENCODER)
    user_id = _local.user.pk if _local.user and _local.user.is_authenticated else None
    content_type_id = ContentType.objects.get_for_model(instance._meta.model).pk

    data = {
        'db': using,
        'object_repr': force_text(instance),
        'action': action,
        'user_id': user_id,
        'changed_data': changed_data,
        'object_id': instance.pk,
        'content_type_id': content_type_id,
        'uuid': uuid
    }

    if MERGE_CHANGES and 'models_logging.middleware.LoggingStackMiddleware' in MIDDLEWARES:
        key = (instance.pk, content_type_id)
        old_action = _local.stack_changes.get(key, {}).get('action')
        if old_action == ADDED:
            data['action'] = ADDED
        _local.stack_changes[key] = data
    else:
        if data['action'] == CHANGED:
            divide_on_update = getattr(getattr(instance, 'ModelLogging', object), 'divide_on_update', False)
            if divide_on_update:
                Change.objects.using(LOGGING_WRITE_DATABASE or using).bulk_create([
                    Change(**{
                        **data,
                        **{'changed_data': json.dumps([_])}
                    }) for _ in json.loads(data['changed_data'])
                ])
                return

        Change.objects.using(LOGGING_WRITE_DATABASE or using).create(**data)
