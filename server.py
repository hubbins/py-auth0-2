# 📁 server.py -----

import json
import os
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for


ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
)


@app.route("/login")
def login():
    scheme = "http" if os.getenv("REPLIT") == "0" else "https"
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True, _scheme=scheme)
    )


@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    print(token["userinfo"])
    session["userinfo"] = token["userinfo"]
    return redirect("/")


@app.route("/logout")
def logout():
    scheme = "http" if os.getenv("REPLIT") == "0" else "https"
    session.clear()
    return redirect(
        "https://"
        + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True, _scheme=scheme),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )


@app.route("/")
def home():
    return render_template(
        "home.html",
        session=session.get("userinfo"),
        pretty=json.dumps(session.get("userinfo"), indent=4),
    )


if __name__ == "__main__":
    if env.get("REPLIT") == "0":
        app.run(host="0.0.0.0", port=env.get("PORT", 3000))
    else:
        app.run(host="0.0.0.0", port=int(os.getenv("PORT")))
