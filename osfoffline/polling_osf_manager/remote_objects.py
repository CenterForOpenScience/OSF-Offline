"""
Things to validate:
    1) actually turn modified string to timestamp
        handle when this doesnt exist and whatever else this needs to do.
    2) check type is correct
    3) check file versus folder
    4) check if each remote thing exist. IF NOT, then raise error (done automatically so i guess thats good)

"""
import iso8601


class RemoteObject(object):
    def __init__(self, remote_dict):
        assert isinstance(remote_dict, dict)
        assert 'type' in remote_dict
        self.id = None
        self.name = None

    def validate(self):
        assert self.id
        assert self.name


class RemoteUser(RemoteObject):
    def __init__(self, remote_dict):
        super().__init__(remote_dict)
        assert remote_dict['type'] == 'users'
        self.id = remote_dict['id']
        self.name = remote_dict['attributes']['full_name']
        self.given_name = remote_dict['attributes']['given_name']
        self.child_nodes_url = remote_dict['relationships']['nodes']['links']['related']

        self.validate()


class RemoteNode(RemoteObject):
    def __init__(self, remote_dict):
        super().__init__(remote_dict)
        assert remote_dict['type'] == 'nodes'
        self.id = remote_dict['id']
        self.name = remote_dict['attributes']['title']
        self.category = remote_dict['attributes']['category']
        self.child_files_url = remote_dict['relationships']['files']['links']['related']['href']
        self.is_top_level = remote_dict['relationships']['parent']['links']['related']['href'] is None
        self.child_nodes_url = remote_dict['relationships']['children']['links']['related']['href']
        # self.num_child_nodes = remote_dict['relationships']['children']['links']['related']['meta']['count']
        self.last_modified = remote_to_local_datetime(remote_dict['attributes']['date_modified'])

        self.validate()

    def validate(self):
        super().validate()
        assert self.child_files_url
        assert self.is_top_level is not None
        assert self.child_nodes_url
        assert self.last_modified
        # assert self.num_child_nodes >= 0


class RemoteFileFolder(RemoteObject):
    def __init__(self, remote_dict):
        super().__init__(remote_dict)
        assert remote_dict['type'] == 'files'
        self.id = remote_dict['id']
        if '/' in self.id:
            self.id = self.id.split('/')[1]
        self.name = remote_dict['attributes']['name']
        self.provider = remote_dict['attributes']['provider']
        self.move_url = remote_dict['links']['move'] if 'move' in remote_dict['links'] else None
        self.delete_url = remote_dict['links']['delete'] if 'delete' in remote_dict['links'] else None

    def validate(self):
        super().validate()
        assert self.provider
        assert self.move_url if not self.id else True
        assert self.delete_url if not self.id else True


class RemoteFolder(RemoteFileFolder):
    def __init__(self, remote_dict):
        super().__init__(remote_dict)
        assert remote_dict['attributes']['kind'] == 'folder'

        self.child_files_url = remote_dict['relationships']['files']['links']['related']['href']
        self.upload_file_url = remote_dict['links']['upload']
        self.upload_folder_url = remote_dict['links']['new_folder']

        self.validate()

    def validate(self):
        super().validate()
        assert self.child_files_url
        assert self.upload_file_url
        assert self.upload_folder_url


class RemoteFile(RemoteFileFolder):
    def __init__(self, remote_dict):
        super().__init__(remote_dict)
        assert remote_dict['attributes']['kind'] == 'file'

        self.download_url = remote_dict['links']['download']
        self.overwrite_url = remote_dict['links']['upload']
        self.size = remote_dict['attributes']['size']
        self.last_modified_string = remote_dict['attributes'].get('date_modified')

        self.validate()

    @property
    def last_modified(self):
        """
        We store the last modified string above. We turn it into a datetime on demand so that
        it will raise an error if the last modified string is wrong.
        """
        return remote_to_local_datetime(self.last_modified_string)

    def validate(self):
        super().validate()
        assert self.download_url
        assert self.delete_url
        assert self.size >= 0
        assert self.overwrite_url


def dict_to_remote_object(remote_dict):
    assert isinstance(remote_dict, dict)
    if remote_dict['type'] == 'files':
        if remote_dict['attributes']['kind'] == 'file':
            return RemoteFile(remote_dict)
        else:
            return RemoteFolder(remote_dict)
    elif remote_dict['type'] == 'nodes':
        return RemoteNode(remote_dict)
    elif remote_dict['type'] == 'users':
        return RemoteUser(remote_dict)
    else:
        raise TypeError('unable to convert dict {} to RemoteObject'.format(remote_dict))


def remote_to_local_datetime(remote_utc_time_string):
    """convert osf utc time string to a proper datetime (with utc timezone).
        throws iso8601.ParseError. Handle as needed.
    """
    return iso8601.parse_date(remote_utc_time_string)
