import logging
import requests
from flask import redirect, url_for, Blueprint, flash, request, session, current_app as app
from redash.authentication.org_resolving import current_org

from redash import models, settings
from redash.authentication import (
    create_and_login_user,
    logout_and_redirect_to_index,
    get_next_path,
)

from authlib.integrations.flask_client import OAuth

logger = logging.getLogger("oauth")
blueprint = Blueprint("oauth", __name__)


def get_oauth_client(app):
    oauth = OAuth(app)
    CONF_URL = current_org.get_setting("auth_oauth_url")
    CONF_NAME = current_org.get_setting('auth_oauth_name')

    client_data = {
        f'{CONF_NAME.upper()}_CLIENT_ID': current_org.get_setting('auth_oauth_client_id'),
        f'{CONF_NAME.upper()}_CLIENT_SECRET': current_org.get_setting('auth_oauth_client_secret'),
    }
    print('client data', client_data)
    try:
        getattr(oauth, CONF_NAME)
    except AttributeError:
        oauth = OAuth(app)
        oauth.register(
            name=CONF_NAME,
            server_metadata_url=CONF_URL,
            client_kwargs={"scope": "openid email profile"},
            **client_data,
        )
    return getattr(oauth, CONF_NAME)  # might need to change this to dot notation


def verify_profile(org, profile):
    if org.is_public:
        return True

    email = profile["email"]
    domain = email.split("@")[-1]

    if domain in org.auth_oauth_domains:
        return True

    if org.has_user(email) == 1:
        return True

    return False


def get_user_profile(access_token):
    CONF_URL = current_org.get_setting("auth_oauth_url")
    headers = {"Authorization": "OAuth {}".format(access_token)}

    try:
        userinfo_endpoint = requests.get(CONF_URL).json()["userinfo_endpoint"]
    except Exception:
        logger.warning("Failed getting userinfo endpoint")
        return None

    response = requests.get(userinfo_endpoint, headers=headers)

    if response.status_code == 401:
        logger.warning("Failed getting user profile (response code 401).")
        return None

    return response.json()

@blueprint.route(f"/<org_slug>/oauth/app", endpoint="authorize_org")
def org_login(org_slug):
    session["org_slug"] = current_org.slug
    return redirect(url_for(".authorize", next=request.args.get("next", None)))

@blueprint.route(f"/oauth/app", endpoint="authorize")
def login():
    oauth_client = get_oauth_client(app)
    redirect_uri = url_for(".callback", _external=True)

    next_path = request.args.get(
        "next", url_for("redash.index", org_slug=session.get("org_slug"))
    )
    logger.debug("Callback url: %s", redirect_uri)
    logger.debug("Next is: %s", next_path)

    session["next_url"] = next_path

    return oauth_client.authorize_redirect(redirect_uri)

@blueprint.route("/oauth/app_callback", endpoint="callback")
def authorized():

    logger.debug("Authorized user inbound")

    resp = get_oauth_client(app).authorize_access_token()
    user = resp.get("userinfo")
    if user:
        session["user"] = user

    access_token = resp["access_token"]

    if access_token is None:
        logger.warning("Access token missing in call back request.")
        flash("Validation error. Please retry.")
        return redirect(url_for("redash.login"))

    profile = get_user_profile(access_token)
    if profile is None:
        flash("Validation error. Please retry.")
        return redirect(url_for("redash.login"))

    if "org_slug" in session:
        org = models.Organization.get_by_slug(session.pop("org_slug"))
    else:
        org = current_org

    if not verify_profile(org, profile):
        logger.warning(
            "User tried to login with unauthorized domain name: %s (org: %s)",
            profile["email"],
            org,
        )
        flash(
            "Your account ({}) isn't allowed.".format(profile["email"])
        )
        return redirect(url_for("redash.login", org_slug=org.slug))

    picture_url = "%s?sz=40" % profile["picture"]
    user = create_and_login_user(
        org, profile["name"], profile["email"], picture_url
    )
    if user is None:
        return logout_and_redirect_to_index()

    unsafe_next_path = session.get("next_url") or url_for(
        "redash.index", org_slug=org.slug
    )
    next_path = get_next_path(unsafe_next_path)

    return redirect(next_path)
