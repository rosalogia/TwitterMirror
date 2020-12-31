from mastodon import Mastodon
import json
import requests
import os
from getpass import getpass

if os.path.exists("./config.json"):
    with open("./config.json") as f:
        cfg = json.load(f)
else:
    with open("./config.json", "w") as f:
        cfg = {}

        print("It seems like this is your first time running this program, so you'll need to provide it with some information to get started.")
        cfg["applicationName"] = input("What name would you like to give your mirroring bot? This name will be seen as the \"source tag\" when your bot posts content.\n")

        cfg["instance"] = input("Which Mastodon instance will your bot be posting to? This should be a URL\n")

        cfg["username"] = input("What's the email associated with your bot's account?\n")
        cfg["password"] = getpass(prompt="What's the password you use to log in to your bot's account on Mastodon?\n")

        cfg["twitter"] = {}

        cfg["twitter"]["apiKey"] = input("What's your Twitter API key?\n")
        cfg["twitter"]["apiKeySecret"] = input("What's your Twitter API key secret?\n")
        cfg["twitter"]["accessToken"] = input("What's your Twitter access token?\n")
        cfg["twitter"]["accessTokenSecret"] = input("What's your Twitter access token secret?\n")

        cfg["mediaOnly"] = True if input("Do you want to restrict mirrored tweets to only those which include media? (Y/N)\n").lower() == "y" else False
        cfg["follow"] = input("Enter the usernames (without the @, separated by spaces) of some accounts you want your bot to mirror. You can extend this list by hand later by editing your config.json file\n").split()

        print("Your bot is ready to go! As soon as an account you entered above posts a tweet (depending on whether or not you chose the media-only option) you should see the tweet's content in your console and the tweet should be posted by the bot to Mastodon! If you are receiving errors, you may have incorrect log-in information for either Mastodon or Twitter.")

        json.dump(cfg, f, indent=4)


if "client.secret" not in os.listdir("."):
    Mastodon.create_app(
         cfg["applicationName"],
         api_base_url=cfg["instance"],
         to_file="client.secret"
    )

mastodon = Mastodon(
    client_id="client.secret",
    api_base_url =cfg["instance"]
)

mastodon.log_in(
    cfg["username"],
    cfg["password"],
    to_file="user_credentials.secret"
)

# We no longer need the old mastodon object, which was used for logging in
mastodon = Mastodon(
    access_token="user_credentials.secret",
    api_base_url=cfg["instance"]
)

import tweepy

auth = tweepy.OAuthHandler(cfg["twitter"]["apiKey"], cfg["twitter"]["apiKeySecret"])
auth.set_access_token(cfg["twitter"]["accessToken"], cfg["twitter"]["accessTokenSecret"])

api = tweepy.API(auth)

usernames = cfg["follow"]
following = [api.get_user(user).id_str for user in usernames]


def prepare_status(status):
    text = status["text"]
    user = status["user"]["screen_name"]

    media_ids = []
        
    try:
        # Expand Twitter shortened URLs
        for url in status["entities"]["urls"]:
            text = text.replace(url["url"], url["expanded_url"])
        
        # Download media attachments and upload them to the instance, then keep track of their IDs
        media_urls = [media["media_url_https"] for media in status["entities"]["media"]]
        
        for murl in media_urls:
            fname = murl.split("/")[-1]
            r = requests.get(murl, allow_redirects=True)

            if not os.path.exists("./media/"):
                os.makedirs("./media/")

            with open(f"./media/{fname}", "wb") as f:
                f.write(r.content)

            mpost = mastodon.media_post(f"./media/{fname}")
            media_ids.append(mpost["id"])

    except KeyError:
        print("No URLs or Media")

    return {"text": f"@{user}: {text}", "media": media_ids}

# Stream listener for real-time tweet grabbing
class SListener(tweepy.StreamListener):
    def on_status(self, status):
        # Avoid grabbing replies and retweets
        if status._json["user"]["screen_name"] in usernames:
            prepared_status = prepare_status(status._json)
            if cfg["mediaOnly"]:
                if prepared_status["media"]:
                    print(prepared_status["text"])
                    mastodon.status_post(prepared_status["text"], media_ids=prepared_status["media"])

            else:
                print(prepared_status["text"])
                mastodon.status_post(prepared_status["text"], media_ids=prepared_status["media"])

            # This should be safe! Let me know if it causes you any problems
            for media_file in os.listdir("./media/"):
                os.remove(os.path.join("./media/", media_file))


sl = SListener()
stream = tweepy.Stream(auth=api.auth, listener=sl)

stream.filter(follow=following)
