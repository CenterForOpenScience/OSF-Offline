from tests.fixtures.mock_osf_api_server.models import User, Node, File
from flask import Flask, jsonify, request, make_response
from tests.fixtures.mock_osf_api_server.utils import (
    session,
    must_be_logged_in,
    save,
    get_user
)


app = Flask(__name__)


def paginate_response(data):
    """
    obviously this is only a start. Will handle pagination properly when time comes.
    :param data:
    :return:
    """
    return jsonify({
        "data":data,
        "links": {
            "first": None,
            "last": None,
            "prev": None,
            "next": None,
            "meta": {
                "total": len(data) if isinstance(data, list) else 1,
                "per_page": 10
            }
        }
    })


@app.route("/v2/users/", methods=['POST']) # create user
@app.route("/v2/users/<user_id>/", methods=['GET']) # get user
def user(user_id=None):
    if request.method == 'POST':
        fullname = request.form['fullname']
        user = User(fullname=fullname)
        save(user)
        session.refresh(user)
    elif request.method =='GET':
        must_be_logged_in(lambda a:a) # check if user is logged in or not
        user = session.query(User).filter(User.id == user_id).one()
    return paginate_response(user.as_dict())


@app.route("/v2/nodes/<node_id>/children/", methods=['GET']) # get a node's child nodes
@must_be_logged_in
def node_children(node_id):
    cur_node = session.query(Node).filter(Node.id==node_id).one()
    return paginate_response([node.as_dict() for node in cur_node.child_nodes])


@app.route("/v2/nodes/", methods=['POST']) # create node
@app.route("/v2/nodes/<node_id>/", methods=['GET']) # get a node
@must_be_logged_in
def node(node_id=None):
    if request.method == 'POST':

        user = get_user()
        title = request.get_json()['data']['attributes']['title']
        node = Node(title=title, user=user)
        session.refresh(user)
        save(node)
        provider = File(name=File.DEFAULT_PROVIDER, type=File.FOLDER, user=user, node=node)
        node.files.append(provider)
        save(node)
        save(provider)
        session.refresh(node)
    elif request.method =='GET':
        node = session.query(Node).filter(Node.user==get_user() and Node.id==node_id).one()
    return paginate_response(node.as_dict())



@app.route("/v2/users/<user_id>/nodes/", methods=['GET'])  # user's nodes
@must_be_logged_in
def user_nodes(user_id):
    if request.method=='GET':

        user = get_user()
        assert str(user_id) == str(user.id)
        users_nodes = session.query(Node).filter(Node.user == user).all()
        return paginate_response([node.as_dict() for node in users_nodes])

@app.route("/v2/nodes/<node_id>/files/", methods=['GET'])  # node's files
@app.route("/v2/nodes/<node_id>/files/<provider>/", methods=['GET'])  # node's files
@app.route("/v2/nodes/<node_id>/files/<provider>/<file_id>/", methods=['GET','DELETE'])  # files' children
@must_be_logged_in
def node_files(node_id, provider=None, file_id=None):
    if request.method=='GET':
        if provider is None:
            user = get_user()
            all_files = session.query(File).filter(File.user==user and File.node_id==node_id).all()
            for file in all_files:
                if file.is_provider:
                    provider_model = file
                    return paginate_response([provider_model.as_dict()])
            assert False # failed because provider model is null
        elif file_id is None:
            assert provider
            user=get_user()
            all_files = session.query(File).filter(File.user==user and File.node_id==node_id).all()
            for file in all_files:
                if file.is_provider:
                    provider_model = file
                    return paginate_response([file_folder.as_dict() for file_folder in provider_model.files])
            assert False # failed because provider model is null

        else:
            assert provider
            assert file_id is not None
            file_folder = session.query(File).filter(File.id == file_id).one()
            assert file_folder.is_folder
            ret = [child.as_dict() for child in file_folder.files]
            return paginate_response(ret)
    elif request.method=='DELETE':
        # deletes everything with given file id and given user.
        file = session.query(File).filter(File.id==file_id and File.user==get_user()).delete()
        #todo: unclear what to return in this case right now.
        return jsonify({'success':'true'})


@app.route("/v2/files/<file_id>/", methods=['GET', 'PUT','PATCH'])  # files
@must_be_logged_in
def files(file_id):
    file_folder = session.query(Node).filter(File.user==get_user() and File.id==file_id).one()
    if request.method=='GET':
        assert file_folder.is_folder
        children = [child.as_dict() for child in file_folder.files]
        return paginate_response(children)
    #todo: this code for put and patch files deals with file checkout. it does NOT match with what api does. understand and fix.
    elif request.method == 'PUT':
        file_folder.checked_out = True
        save(file_folder)
    elif request.method == 'PATCH':
        file_folder.checked_out = True
        save(file_folder)
    return paginate_response(file_folder.as_dict())

@app.route("/v1/resources/<node_id>/providers/<provider>/", methods=['GET','PUT']) # get list of things in provider folder, upload to provider folder
@app.route("/v1/resources/<node_id>/providers/<provider>/<file_id>/", methods=['PUT','POST', 'GET', 'DELETE'])  # download file, update existing file, move/rename file/folder
@must_be_logged_in
def resources(node_id, provider, file_id=None):
    if file_id is None:
        file_folder = session.query(Node).filter(Node.user==get_user() and Node.id == node_id).one().files[0] # provider folder
    else:
        file_folder = session.query(File).filter(File.id==file_id and File.user==get_user() and File.node_id == node_id).one()
    if request.method=='GET': # download
        assert file_folder.is_file
        #make it so that the returned content is actually downloadable.
        content = file_folder.contents
        response = make_response(content)
        # Set the right header for the response
        response.headers["Content-Disposition"] = "attachment; filename={}".format(file_folder.name)
        return response
    elif request.method == 'PUT': # upload new file, upload new folder, update existing file
        if file_folder.is_folder: # upload new file, upload new folder
            parent = file_folder
            kind = request.args.get('kind','file')
            new_file_folder = File(
                type=File.FOLDER if kind == 'folder' else File.FILE,
                node=parent.node,
                user=parent.user,
                parent=parent,
                name=request.args.get('name'),
                provider=provider,
                contents=request.get_data() if kind == 'file' else None
            )
            save(new_file_folder)
            session.refresh(new_file_folder)
            return paginate_response(new_file_folder.as_dict())
        else: # update existing file
            assert request.args.get('kind') == 'file'
            assert request.args.get('name') is not None
            assert file_folder.has_parent # if no parent, then provider thus error.
            # this creates new version of the file
            file_folder.content = request.get_data()
            file_folder.name = request.args.get('name')
            session.refresh(file_folder)
            return paginate_response(file_folder.as_dict())
    elif request.method=='POST': # rename, move
        assert file_folder.has_parent
        if request.json['action'] == 'rename':
            file_folder.name = request.json['rename']
            save(file_folder)
            session.refresh(file_folder)
            return paginate_response(file_folder.as_dict())
        elif request.json['action'] == 'move':
            new_parent_id = request.json['path'].split('/')[1]
            new_parent = session.query(File).filter(File.id == new_parent_id).one()
            file_folder.parent = new_parent

            if request.json['rename']:
                file_folder.name = request.json['rename']

            save(file_folder)
            session.refresh(file_folder)
            return paginate_response(file_folder.as_dict())
    elif request.method=='DELETE':
        session.query(File).filter(File.id==file_id and File.user==get_user()).delete()
        #todo: unclear what to return in this case right now.
        return jsonify({'success':'true'})









