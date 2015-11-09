import json
from osfoffline.polling_osf_manager.api_url_builder import api_user_nodes
from furl import furl
from tests.fixtures.mock_httpretty_responses.utils import (
    must_be_logged_in,
    session,
    create_new_file,
    create_new_folder,
    save,
    user_id_from_request
)
from tests.fixtures.mock_httpretty_responses.models import User, Node, File

#api_create_user_url
def create_user(request, uri, headers):
    try:
        fullname = request.parsed_body['fullname'][0]
        user = User(fullname=fullname)
        save(user)
        session.refresh(user)
        resp = json.dumps(
            {
                'data': user.as_dict()
            }
        )

        return 200, headers, resp
    except:
        return 400, headers, 'ERROR in create_user.'

@must_be_logged_in
def get_user(request, uri, headers):
    try:
        id = furl(uri).path.segments[2]
        user = session.query(User).filter(User.id ==id).one()
        resp = json.dumps(
            {
                'data': user.as_dict()
            }
        )
        return 200, headers, resp
    except:
        return 400, headers, 'ERROR in get_user.'

@must_be_logged_in
def create_node(request, uri, headers):
    try:
        user_id = user_id_from_request(request)
        user = session.query(User).filter(User.id ==user_id).one()
        title = request.parsed_body['title'][0]
        node = Node(user=user, title=title)
        save(node)
        session.refresh(node)
        provider = File(type=File.FOLDER, user=user, node=node)
        node.files.append(provider)
        save(node)
        session.refresh(node)
        resp = json.dumps({
            'data':node.as_dict()
        })
        return (200, headers, resp)
    except:
        return (400, headers, 'cant get user nodes')


@must_be_logged_in
def get_user_nodes(request, uri, headers):
    try:
        user_id = furl(uri).path.segments[2]

        user = session.query(User).filter(User.id ==user_id).one()

        nodes = user.nodes
        # return 200, headers, json.dumps({'data':'asd'})
        resp = [node.as_dict() for node in nodes]
        resp = json.dumps({
            'data':resp
        })
        return (200, headers, resp)
    except:
        return (400, headers, 'cant get user nodes')

def get_all_nodes(request, uri, headers):
    try:

        nodes = session.query(Node).all()
        resp = [node.as_dict() for node in nodes]
        resp = json.dumps({
            'data':resp
        })
        return (200, headers, resp)
    except:
        return (400, headers, 'ERROR in getting all nodes')

# @must_be_logged_in
# def get_providers_for_node(request, uri, headers):
#     try:
#
#         nid = furl(uri).path.segments[2]
#
#         node = session.query(Node).filter(Node.id == nid).one()
#         print('hifahsidfadsf')
#         resp = [provider.as_dict() for provider in node.providers]
#
#         resp = json.dumps({
#             'data':resp
#         })
#         return (200, headers, resp)
#     except:
#         return (400, headers, 'cant get providers for node')

@must_be_logged_in
def get_node_children(request, uri, headers):
    try:

        nid = furl(uri).path.segments[2]
        node = session.query(Node).filter(Node.id == nid).one()

        resp = [child.as_dict() for child in node.child_nodes]
        resp = json.dumps({
            'data':resp
        })
        return (200, headers, resp)
    except:
        return (400, headers, 'cant get children for node')



@must_be_logged_in
def get_children_for_folder(request, uri, headers):
    try:

        folder_path = furl(uri).args['path']

        nid = furl(uri).path.segments[2]

        for file_folder in session.query(File):
            if not file_folder.is_file:
                if file_folder.node.id == int(nid) and file_folder.path == folder_path:
                    resp = [child.as_dict() for child in file_folder.files]
                    resp = json.dumps({
                        'data':resp
                    })
                    return (200, headers, resp)
    except:
        return (400, headers, 'cant get providers for node')

@must_be_logged_in
def create_folder(request, uri, headers):

    data = furl(uri).args['path']

    parts = data.split('/')
    parent_path = parts[1] if len(parts)==3 else '/'
    new_folder_name = parts[2] if len(parts)==3 else parts[1]

    provider = furl(uri).args['provider']
    nid = furl(uri).args['nid']
    return 200, headers, json.dumps({
        'data':'ahahah'
    })
    parent = session.query(File).filter(File.is_folder and File.node_id==nid and File.path==parent_path).one()
    assert parent.node.id == nid

    new_folder = File(type=File.FOLDER, node=parent.node, user=parent.user,
                      parent=parent, name=new_folder_name, provider=provider)
    save(parent)
    save(new_folder)
    resp = json.dumps({
        'data':new_folder.as_dict()
    })
    return (200, headers, resp)



@must_be_logged_in
def create_file(request, uri, headers):
    folder_path = furl(uri).args['path']
    # folder_name = folder_path.split('/')[1]
    # provider_name = furl(uri).args['path']
    nid = furl(uri).args['nid']
    provider = session.query(File).filter(File.parent == None and File.node_id==nid).one()
    new_file = create_new_file(provider)
    resp = json.dumps({
        'data':new_file.as_dict()
    })
    return (200, headers, resp)

# @must_be_logged_in
# def download_file(request, uri, headers):


