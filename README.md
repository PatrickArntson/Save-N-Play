# Save-N-Play

Discord Bot for streaming Youtube audio to a Discord voice server. The bot allows users to create a video queue by adding videos individually or by adding existing Youtube playlists to the queue. If the user is signed in to Youtube, it also allows the user to save videos to their own playlists. 

**REQUIREMENTS/NOTES**

- FFMPEG must be in an executable path for this to work. (i.e. /usr/local/bin for Mac users)

- Must have Chrome Browser installed or change the browser in the selenium import statement.

- In order to add to a playlist, you must run the script once with the 'file_path' set to a non-existant or empty folder. Go down to the ?add2 command and comment out the 'driver.close()' statement near the end of the function. Once you run the script and the browser opens up, sign in to a youtube account. The login info will be saved in your specified file path so that it can stay logged in. Remember to uncomment the 'driver.close()' statement afterewards.

- When using the ?play command search for the name of the video you wish to listen to, not the exact url. This command works by querying youtube for your search and picking the first video in the results. However, for the ?qp command, you can specify a saved playlist from the paylists dictionary or enter a youtube playlist url.
