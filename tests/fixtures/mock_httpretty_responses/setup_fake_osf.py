__author__ = 'himanshu'
from tests.utils.url_builder import *
import httpretty
import re
from tests.fixtures.mock_httpretty_responses.osf_api import (
    create_user,
    get_user,

    create_node,
    get_user_nodes,
    get_node_children,
    get_all_nodes,

    create_folder,

    get_children_for_folder,


)

REGEX_MATCH_PHRASE = "(\w+)"
# to make this fake osf work:


def setup_mock_osf_api():
    register_user_create_url()
    register_user_url()

    register_create_node_url()
    register_user_nodes_url()
    register_get_all_nodes_url()


    register_folder_create_url()
    register_file_get_url() # get files and folder

    # register_node_children()




def register_user_create_url():

    httpretty.register_uri(
        httpretty.POST,
        'http://localhost:8000/v2/users/',
        body=create_user,
        content_type="application/json"
    )


def register_user_url():
    httpretty.register_uri(
        httpretty.GET,
        re.compile('http://localhost:8000/v2/users/{}/$'.format(REGEX_MATCH_PHRASE)),
        body=get_user,
        content_type="application/json"
    )

def register_get_all_nodes_url():
    httpretty.register_uri(
        httpretty.GET,
        re.compile('http://localhost:8000/v2/nodes/'.format(REGEX_MATCH_PHRASE)),
        body=get_all_nodes,
        content_type="application/json"
    )


def register_create_node_url():
    httpretty.register_uri(
        httpretty.POST,
        re.compile('http://localhost:8000/v2/nodes/'.format(REGEX_MATCH_PHRASE)),
        body=create_node,
        content_type="application/json"
    )



def register_user_nodes_url():

    httpretty.register_uri(
        httpretty.GET,
        re.compile('http://localhost:8000/v2/users/{}/nodes/'.format(REGEX_MATCH_PHRASE)),
        body=get_user_nodes,
        content_type="application/json"
    )




# def register_node_providers_url():
#     httpretty.register_uri(
#         httpretty.GET,
#         re.compile('http://localhost:8000/v2/nodes/{}/files/'.format(REGEX_MATCH_PHRASE)),
#         body=get_providers_for_node,
#         content_type="application/json"
#     )

def register_node_children():
    httpretty.register_uri(
        httpretty.GET,
        re.compile('http://localhost:8000/v2/nodes/{}/children/'.format(REGEX_MATCH_PHRASE)),
        body=get_node_children,
        content_type="application/json"
    )


def register_file_get_url():
    httpretty.register_uri(
        httpretty.GET,
        re.compile('http://localhost:8000/v2/nodes/{}/files/'.format(REGEX_MATCH_PHRASE)),
        body=get_children_for_folder,
        content_type="application/json"
    )

def register_folder_create_url():
    httpretty.register_uri(
        httpretty.POST,
        'http://localhost:7777/file',
        body=create_folder,
        content_type="application/json"
    )


