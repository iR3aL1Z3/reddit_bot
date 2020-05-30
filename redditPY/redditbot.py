# This script is a bot to download a random top daily post from a subreddit and post it to Twetch at a scheduled time.

from twetch2py import Twetch
import praw
import requests

import time
import os
import random
import json

# We use random a couple times. Gotta seed it.
random.seed()

# We're going to use a file to store the scheduled time of each next post.
# This way, we don't have to worry about the script crashing and losing the scheduled time in memory.
# Here, we just set the name of the file as a constant. We'll be using it later.
PERSISTENT_FILENAME = "persistent.json"

# We'll be storing the images we post in a folder.
# This is the name of that folder.
IMAGE_DIRNAME = "images"

# In order to use the reddit api in python, we're using a wrapper called praw.
# You'll need to set your own client id, client secret, and user agent.
# Information on how to do this can be found at https://praw.readthedocs.io/en/latest/getting_started/quick_start.html
# Here, we instantiate a Reddit object from praw. We'll be using it later.
reddit = praw.Reddit(client_id="",
                     client_secret="",
                     user_agent="twetchbot")


# This function writes json data to the persistent file.
def write_persistent_data(data):
    with open(PERSISTENT_FILENAME, "w+") as f:
        f.write(json.dumps(data))


# This function reads json data from the persistent file.
def read_persistent_data():
    with open(PERSISTENT_FILENAME, "r") as f:
        return json.loads(f.read())


# This function reads the persistent data file and updates the value that the key specifies.
# The way we will be using it, the key will be a string, ("post_time") and the value will be a float, (the scheduled time of the next post).
def set_key_value(key, value):
    data = read_persistent_data()
    data[key] = value
    write_persistent_data(data)


# This function returns a list of the top 10 posts for the day of the specified subreddit.
def get_top_posts():
    top_posts = []                                                              # create an empty list
    for submission in reddit.subreddit("hmmm").top("day", limit=10):            # iterate through the top 10 daily submissions
        if not submission.over_18:                                              # if the submission is not NSFW (not safe for work),
            top_posts.append(submission)                                        # add the submission to the list
    return top_posts


# This function downloads the selected image file from reddit and uploads the file to twetch.
def save_and_twetch(url):
    file_name = url.split('/')[3]                   # split the url by slashes and get the fourth string (this gives us a filename like "ieuoexbqmvz41.jpg")
    file_path = IMAGE_DIRNAME + "/" + file_name     # concatenate the directory name to the file name
    if not os.path.exists(file_path):               # if the file doesn't already exist,
        r = requests.get(url)                       # send a web request to get the image
        file = r.content
        with open(file_path, 'wb') as f:            # create the file and open it in "write binary" mode
            f.write(file)                           # write the content from the web request to the file

        print("twetching " + file_path)
        twetch_object = Twetch(content=" ", media=file_path)    # instantiate a Twetch object with the filename of the image
        twetch_object.publish()                                 # publish the twetch!!!
        print("twetched " + file_path)

        next_post_time = time.time() + (random.randint(14400, 28800))   # add between 4 and 8 hours to the current time
        set_key_value("post_time", next_post_time)                      # save the scheduled next post time
        return True                                                     # return True so that we can stop the outer loop
    else:
        print("file already exists")
        return False                        # file already exists, so the function gets run again in the outer loop


if not os.path.exists(PERSISTENT_FILENAME):                         # if the persistent file doesn't exist,
    write_persistent_data({"post_time": time.time() + 60 * 60})     # create the file with an initial scheduled post time of 1 hour from now

if not os.path.exists(IMAGE_DIRNAME):   # if the image folder doesn't exist,
    os.mkdir(IMAGE_DIRNAME)             # create the folder

while True:
    next_post_time = read_persistent_data()["post_time"]  # read the scheduled post time from the persistent file

    if time.time() > next_post_time:    # if the current time is greater than the scheduled post time,
        top_posts = get_top_posts()     # make a list of the top posts' urls

        status = False
        while not status:                       # while the function fails to publish the twetch, just try it again
            post = random.choice(top_posts)     # randomly select one post from the list
            status = save_and_twetch(post.url)  # save and publish the image to twetch

    print("sleeping. next post at " + time.strftime("%H:%M:%S", time.localtime(next_post_time)))
    time.sleep(10 * 60)  # wait 10 minutes
