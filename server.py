import json
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, request, make_response, redirect
import requests


ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app: Flask = Flask(__name__)
app.secret_key: str = env.get("APP_SECRET_KEY")

oauth: OAuth = OAuth(app)

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
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True, _scheme=env.get("URL_SCHEME"))
    )


@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    print(token)
    #print(token["access_token"])
    #userinfo = oauth.auth0.userinfo()
    #print(userinfo)
    #session["userinfo"] = token["userinfo"]
    session["access_token"] = token["access_token"]
    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://"
        + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for(
                    "home", _external=True, _scheme=env.get("URL_SCHEME")
                ),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )


@app.route("/")
def home():
  access_token = session.get("access_token")
  if access_token:
    userinfo = requests.get(f"https://{env.get('AUTH0_DOMAIN')}/userinfo",params={"access_token": access_token}).content
    print(userinfo)
  return render_template(
      "home.html",
      #session=session.get("userinfo"),
      session = access_token
      #pretty=json.dumps(session.get("userinfo"), indent=4),
  )

@app.route("/verify")
def verify():
  # save state in cookie
  state = request.args.get("state")
  #print("state: " + state)
  
  resp = make_response(render_template(
    "verify.html",
    continue_url = url_for(
      "verify_continue", _external=True,
      _scheme=env.get("URL_SCHEME")
    )
  ))

  resp.set_cookie("verify_state", state)

  return resp

@app.route("/verify-continue")
def verify_continue():
  # retrieve state and /continue
  state = request.cookies.get("verify_state")
  #print("second state: " + state)

  continue_uri = f"https://{env.get('AUTH0_DOMAIN')}/continue?state={state}"

  resp = make_response(redirect(continue_uri, code=302))
  
  resp.delete_cookie("verify_state")
  
  return resp


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(env.get("PORT")))
