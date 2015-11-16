from furl import furl

from osfoffline.settings import API_BASE, FILE_BASE


# todo: can make a api_url_for function that makes things potentially simpler...?
USERS = 'users'
NODES = 'nodes'
FILES = 'files'
APPLICATIONS = 'applications'
CHILDREN = 'children'
RESOURCES = 'resources'


def _ensure_trailing_slash(url):
    url.rstrip('/')
    return url + '/'


def api_url_for(endpoint_type, related_type=None, **kwargs):
    base = furl(API_BASE)
    files_base = furl(FILE_BASE)
    assert endpoint_type in [USERS, NODES, FILES, APPLICATIONS, RESOURCES]

    if endpoint_type == USERS:
        base.path.segments.extend(['v2', USERS])
        if 'user_id' in kwargs and kwargs['user_id'] is not None:
            base.path.segments.append(str(kwargs['user_id']))
        if related_type:
            assert related_type in [NODES]
            base.path.segments.append(related_type)
            user_nodes = _ensure_trailing_slash(base.url)
            user_nodes += '?filter[registration]=false'
            return user_nodes
    elif endpoint_type == NODES:

        base.path.segments.extend(['v2', NODES])
        if 'node_id' in kwargs and kwargs['node_id'] is not None:
            base.path.segments.append(str(kwargs['node_id']))
        if related_type:
            assert related_type in [FILES, CHILDREN]
            base.path.segments.append(related_type)
            if kwargs.get('provider') is not None and kwargs.get('file_id') is not None:
                base.path.segments.extend([kwargs['provider'], str(kwargs['file_id'])])
    elif endpoint_type == FILES:
        base.path.segments.extend(['v2', FILES])
        if 'file_id' in kwargs and kwargs['file_id'] is not None:
            base.path.segments.append(str(kwargs['file_id']))
    elif endpoint_type == RESOURCES:
        # /v1/resources/6/providers/osfstorage/21/?kind=folder&name=FUN_FOLDER HTTP/1.1" 200 -
        files_base.path.segments.extend(['v1', RESOURCES,
                                         str(kwargs['node_id']),
                                         'providers',
                                         kwargs['provider']
                                         ])
        if 'file_id' in kwargs and kwargs['file_id'] is not None:
            files_base.path.segments.append(str(kwargs['file_id']))
        return _ensure_trailing_slash(files_base.url)
    return _ensure_trailing_slash(base.url)
