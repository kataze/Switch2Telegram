from twitter import *
import requests as req
import os
import io
import time
import telebot

class Switch2Telegram:
    def __init__(self):
        self.twitter_consumer_key = os.getenv("TWITTER_OAUTH_CONSUMER_KEY")
        self.twitter_consumer_secret = os.getenv("TWITTER_OAUTH_CONSUMER_SECRET")
        self.twitter_target_user = os.getenv("TWITTER_TARGET_USER")
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_target_chat_id = os.getenv("TELEGRAM_TARGET_CHAT_ID")

        self.t = Twitter(auth=OAuth("",
                                    "",
                                    self.twitter_consumer_key,
                                    self.twitter_consumer_secret))
        last_tweet = self.t.statuses.user_timeline(screen_name=self.twitter_target_user, count=1)[0]
        self.last_tweet_id = last_tweet["id"]
        self.tb = telebot.TeleBot(self.telegram_bot_token)

    def new_tweets(self):
        new_tweets = self.t.statuses.user_timeline(screen_name=self.twitter_target_user, since_id=self.last_tweet_id)
        if len(new_tweets) > 0:
            self.update_last_tweet_id(new_tweets)
        return new_tweets

    def update_last_tweet_id(self, new_tweets):
        max_tweet_id = 0
        for tweet in new_tweets:
            max_tweet_id = max(max_tweet_id, tweet["id"])
        self.last_tweet_id = max_tweet_id

    def send_telegram_message(self, message):
        self.tb.send_message(self.telegram_target_chat_id, message)

    def send_telegram_photo(self, photo):
        self.tb.send_photo(self.telegram_target_chat_id, photo)

    def send_telegram_video(self, video):
        self.tb.send_video(self.telegram_target_chat_id, video)

    def check_for_new_tweets_and_send(self):
        new_tweets = self.new_tweets()
        if len(new_tweets) > 0:
            self.send_new_tweets(new_tweets)

    def send_new_tweets(self, tweets):
        for tweet in tweets:
            if "extended_entities" in tweet:
                self.send_media_to_telegram(tweet)

    def send_media_to_telegram(self, tweet):
        for media in tweet["extended_entities"]["media"]:
            if media["type"] == "photo":
                photo = self.get_photo_from_media(media)
                self.send_telegram_photo(photo)
            if media["type"] == "video":
                video = self.get_video_from_media(media)
                self.send_telegram_video(video)

    def get_video_from_media(self, media):
        valid_variants = [variant for variant in media["video_info"]["variants"] if "bitrate" in variant]
        highest_bitrate_variant = valid_variants[0]
        for variant in valid_variants[1:]:
            if "bitrate" not in variant:
                continue
            if variant["bitrate"] > highest_bitrate_variant["bitrate"]:
                highest_bitrate_variant = variant
        url = highest_bitrate_variant["url"]
        return self.get_url_as_file(url)

    def get_photo_from_media(self, media):
        return self.get_url_as_file(media["media_url_https"])

    def get_url_as_file(self, url):
        return io.BytesIO(req.get(url).content)


s2t = Switch2Telegram()

while True:
    s2t.check_for_new_tweets_and_send()
    time.sleep(1)
