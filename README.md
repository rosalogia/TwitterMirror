# TwitterMirror for Mastodon

TwitterMirror for Mastodon is a Mastodon bot that mirrors content posted by specified Twitter accounts to a mastodon instance.
It requires that you have both a Mastodon bot account and a Twitter API key and access token, and works via streaming API. Upon initially
being run, the script will guide the user through setting up a configuration file with all relevant and necessary details, but the configuration
file (in JSON format) can be edited manually with ease.

# Running

TwitterMirror was developed using Python 3.8 but is likely to work for versions of Python from 3.6 onwards.

```
$ pip install -r requirements.txt
$ python bot.py
```

# Configuration

The accounts followed by the bot can be manually edited in `config.json`, as can whether posts that do not include media should be mirrored.
