__author__ = 'himanshu'
from decorator import decorator
from tests.fixtures.mock_httpretty_responses.common import Session
from tests.fixtures.mock_httpretty_responses.models import User, Node, File
session = Session()

def save(item=None):
    if item is not None:
        session.add(item)
    session.commit()



def create_new_folder(folder):
    new_folder = File(type=File.FOLDER, node=folder.node, user=folder.user, parent=folder)
    save(folder)
    save(new_folder)
    return new_folder

def create_new_file(folder):

    new_file = File(type=File.FILE, node=folder.node, user=folder.user, parent=folder)
    save(new_file)
    save(folder)
    return new_file


# helpers
@decorator
def must_be_logged_in(func, *args, **kwargs):
    try:

        id = user_id_from_request(args[0])
        session.query(User).filter(User.id==id).one()
        return func(*args, **kwargs)
    except:
        return (404, args[0].headers, 'something wrong with must_be_logged_in func')


def user_id_from_request(request):
    bearer_plus_id = request.headers.get('Authorization')
    id = bearer_plus_id.split(' ')[1]
    return id

