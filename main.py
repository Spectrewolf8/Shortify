import base64
from flask import (
    Flask,
    render_template,
    request,
    flash,
    redirect,
    url_for,
)
from flask_pymongo import PyMongo
import configparser
import os
import datetime
from pymongo.errors import ServerSelectionTimeoutError
import hashlib


config = configparser.ConfigParser()
config.read(os.path.abspath(os.path.join(".ini")))

app = Flask(__name__)
app.app_context().push()
app.config["SECRET_KEY"] = "for the night is dark and full of terrors"
app.config["DEBUG"] = True
app.config["MONGO_URI"] = config["PROD"]["DB_URI"]

# hashids = Hashids(min_length=4, salt=app.config["SECRET_KEY"])
try:
    mongo = PyMongo(app)
    print("MongoDB Server Info:", mongo.cx.server_info())
    print("MongDB connection status:", mongo.cx.get_database)
    print("Connected Database:", mongo.db)
except ServerSelectionTimeoutError as e:
    print("Could not connect to MongoDB: ", e)


@app.route("/", methods=("GET", "POST"))
@app.route("/", methods=("GET", "POST"))
def index():
    if request.method == "POST":
        url = request.form["url"]

        if not url:
            flash("Please enter a URL!")
            return redirect(url_for("index"))

        # Use base64 encoding to generate a URL-safe string
        shrinked_id = base64.urlsafe_b64encode(
            hashlib.sha1(url.encode("UTF-8")).digest()
        )[:10].decode("UTF-8")

        url_data = mongo.db.urls.insert_one(
            {
                "url_identifier": shrinked_id,
                "original_url": url,
                "created": datetime.datetime.utcnow(),
            }
        )
        short_url = request.host_url + shrinked_id
        return render_template("index.html", short_url=short_url)

    return render_template("index.html")


@app.route("/<id>")
def url_redirect(id):
    print(request.path, request.user_agent)
    url_id = str(id)
    print("original_id:", url_id)

    # Check if the provided id contains dots or slashes
    if "." in url_id or "/" in url_id:
        # Treat it as an original_url
        url_data = mongo.db.urls.find_one({"original_url": url_id})
        if url_data:
            original_url = url_data["original_url"]
            return redirect(original_url, code=302)
    else:
        # Treat it as a url_identifier
        url_data = mongo.db.urls.find_one({"url_identifier": url_id})
        if url_data:
            original_url = url_data["original_url"]
            clicks = url_data.get("clicks", 0)

            mongo.db.urls.update_one(
                {"url_identifier": url_id}, {"$inc": {"clicks": 1}}
            )
            print("original_url", original_url)
            return redirect(original_url, code=302)

    flash("Invalid URL")
    return redirect(url_for("index"))


# else:
#     flash("Invalid URL")
#     return redirect(url_for("index"))


@app.route("/stats")
def stats():
    db_urls = mongo.db.urls_db.find()

    urls = []
    for url in db_urls:
        url["short_url"] = request.host_url + hashids.encode(str(url["_id"]))
        urls.append(url)

    return render_template("stats.html", urls=urls)


@app.route("/favicon.ico")
def favicon():
    return "", 20


if __name__ == "__main__":
    app.run()
