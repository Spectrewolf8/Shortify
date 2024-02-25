import base64
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_pymongo import PyMongo
import os
import datetime
from pymongo.errors import ServerSelectionTimeoutError
import hashlib


app = Flask(__name__)
app.config["DEBUG"] = True
app.config["MONGO_URI"] = os.environ["DB_URI"]

try:
    mongo = PyMongo(app)
except ServerSelectionTimeoutError as e:
    print("Could not connect to MongoDB:", e)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")

        if not url:
            flash("Please enter a URL!")
            return redirect(url_for("index"))

        # Check if the URL is already in the database
        existing_url = mongo.db.urls.find_one({"original_url": url})

        if existing_url:
            # If the URL is already in the database, just create the short URL
            short_url = request.host_url + existing_url["url_identifier"]
        else:
            # If the URL is not in the database, index and shorten it
            shrinked_id = base64.urlsafe_b64encode(
                hashlib.sha1(url.encode("UTF-8")).digest()
            )[:10].decode("UTF-8")

            mongo.db.urls.insert_one(
                {
                    "url_identifier": shrinked_id,
                    "original_url": url,
                    "created": datetime.datetime.utcnow(),
                    "clicks": 0,
                }
            )

            short_url = request.host_url + shrinked_id

        return render_template("index.html", short_url=short_url)

    return render_template("index.html")


@app.route("/<id>")
def url_redirect(id):
    url_id = str(id)

    if "." in url_id or "/" in url_id:
        # Treat it as an original_url
        url_data = mongo.db.urls.find_one({"original_url": url_id})
    else:
        # Treat it as a url_identifier
        url_data = mongo.db.urls.find_one({"url_identifier": url_id})

    if url_data:
        original_url = url_data["original_url"]

        if not ("." in url_id or "/" in url_id):
            # Increment clicks only for url_identifier
            mongo.db.urls.update_one(
                {"url_identifier": url_id}, {"$inc": {"clicks": 1}}
            )

        if "https://" in original_url:
            return redirect(original_url, code=302)
        else:
            return redirect("https://" + original_url, code=302)

    flash("Invalid URL")
    return redirect(url_for("index"))


@app.route("/stats")
def stats():
    # Retrieve all URLs from the MongoDB collection
    db_urls = mongo.db.urls.find()

    # Generate a list of URLs with short_url information
    urls = [
        {
            "short_url": request.host_url + str(url["url_identifier"]),
            "url_identifier": str(url["url_identifier"]),
            "original_url": str(url["original_url"]),
            "clicks": str(url["clicks"]),
            "created": str(url["created"]),
        }
        for url in db_urls
    ]
    return render_template("stats.html", urls=urls)


@app.route("/favicon.ico")
def favicon():
    return "", 204


if __name__ == "__main__":
    app.run()
