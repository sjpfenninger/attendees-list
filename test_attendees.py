"""Tests the script that retrieves user information.

The script is tested on the live instance through retrieving actual data. Tests
can hence easily break, whenever (1) there is no internet connection, (2) the
forum is unavailable, (3) test data on the server has changed. In the latter
case, update the TEST_USERS data manually to match the information on the server.
"""
from collections import namedtuple
import re

import pytest
import requests

import attendees

User = namedtuple("User", "username,name,location,website,bio,affiliation")
Group = namedtuple("Group", "name,id")


TEST_USERS = [
    User(
        username="timtroendle",
        name="Tim Tröndle",
        location="Zürich",
        website="http://www.rep.ethz.ch/people/person-detail.html?persid=240778",
        bio="PhD researcher in the Renewable Energy Policy group at ETH Zürich",
        affiliation="ETH Zürich"
    ),
    User(
        username="tom_brown",
        name="Tom Brown",
        location="",
        website="https://www.nworbmot.org/",
        bio="",
        affiliation=""
    )
]

TEST_GROUPS = [
    Group(
        name="admins",
        id=1
    ),
    Group(
        name="moderators",
        id=2
    )
]

VALID_IMAGE_MIME_TYPES = ["image/png", "image/jpeg"]
EMAIL_REGEX = r"[^@]+@[^@]+\.[^@]+" # https://stackoverflow.com/a/8022584/1856079


@pytest.fixture(params=TEST_USERS)
def user(request):
    return request.param


@pytest.fixture(params=TEST_GROUPS)
def group(request):
    return request.param


def test_returns_username_as_index(user):
    users = attendees.attendee_list(usernames=[user.username])
    assert user.username in users.index


@pytest.mark.parametrize("parameter", [
    "name",
    "location",
    "website",
    "bio",
    "affiliation"
])
def test_returns_parameter(user, parameter):
    users = attendees.attendee_list(usernames=[user.username])
    assert users.loc[user.username, parameter] == user.__getattribute__(parameter)


def test_returns_avatar_url(user):
    users = attendees.attendee_list(usernames=[user.username])
    avatar_url = users.loc[user.username, "avatar_url"]
    assert _valid_image_url(avatar_url)
    assert user.username in avatar_url


@pytest.mark.skipif(
    not pytest.config.getoption("--emails"),
    reason="needs --emails option to run"
)
def test_returns_email_addresses(variables, user):
    users = attendees.attendee_list(
        usernames=[user.username],
        api_username=variables["api_username"],
        api_key=variables["api_key"],
        retrieve_emails=True
    )
    assert re.match(EMAIL_REGEX, users.loc[user.username, "email"])


def _valid_image_url(url):
    r = requests.get(url)
    return r.status_code == 200 and r.headers['content-type'] in VALID_IMAGE_MIME_TYPES


def test_username_check():
    usernames = ["timtroendle", "TIMTROENDLE", "abcdefghijk654321", "Wolf"]
    assert attendees.check_usernames(usernames) == ["abcdefghijk654321"]


@pytest.mark.parametrize("group_name", [
    "asdasd231234",
    "dasvhzt6"
])
def test_group_id_retrieval_fails_with_unknown_group_name(variables, group_name):
    with pytest.raises(ValueError):
        attendees._group_name_to_id(group_name, variables["api_username"], variables["api_key"])


def test_group_id_retrieval(variables, group):
    retrieved = attendees._group_name_to_id(group.name, variables["api_username"], variables["api_key"])
    assert retrieved == group.id


@pytest.mark.parametrize("admin", [
    "tom_brown",
    "timtroendle"
])
def test_user_in_admin_group(variables, admin):
    admins = attendees.group_members("admins", variables["api_username"], variables["api_key"])
    assert admin in admins


def test_no_moderators(variables):
    moderators = attendees.group_members("moderators", variables["api_username"], variables["api_key"])
    assert len(moderators) == 0
