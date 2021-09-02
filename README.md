# Save-N-Play

Discord Bot for streaming Youtube audio to a Discord voice server. The bot allows a user to play an existing Youtube playlists. If the user is signed in to Youtube, it allows the user to add videos to their own playlists. 

**REQUIREMENTS/NOTES**

- Make sure you are using the most up to date selenium and youtube_dl versions for saftey/privacy resaons.

- FFMPEG must be in an executable path for this to work. (i.e. /usr/local/bin for Mac users)

- Must have Chrome Browser installed or change the browser in the selenium import statement.

- In order to add to a playlist, you must run the script once with the 'file_path' set to a non-existant or empty folder. Once you run the script and the browser opens up, sign in to a youtube account. The login info will be saved in your specified file path so that it can stay logged in. 

- When using the ?play command search for the name of the video you wish to listen to, not the exact url. This command works by querying youtube for your search and picking the first video in the results. However, for the ?qp command, you can specify a saved playlist from the paylists dictionary or enter a youtube playlist url.
