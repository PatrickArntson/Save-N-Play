import re
import threading
import time
import urllib.request

import discord
import youtube_dl
from discord.ext import commands
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

TOKEN = 'YOUR DISCORD BOT TOKEN HERE'


client = commands.Bot(command_prefix='?', intents=discord.Intents.all())

# Globals
song_q = []                 # queue of video urls
song_list = []              # list of videos names and urls that are in song_q
song_duration_list = []     # list of video durations of videos in song_q
current_song = None         # name of current video that/. is playing
duration = None             # The length of the video that is playing
outer_ctx = None            # used to give the background loop access to the voice client

# Youtube Playlist/Web-scraping Setup
options = Options()
file_path = 'FILE PATH TO AN EMPTY FOLDER HERE'
options.add_argument("user-data-dir=" + str(file_path))
playlists = {'funny': 'YOUR PLAYLIST URL PAGE HERE',
             'music': 'YOUR PLAYLIST URL PAGE HERE'}


class WebdriverError(Exception):
    pass


class InvalidPlaylistName(Exception):
    pass


class QueueFailure(Exception):
    pass


def background():
    """
    This is the background thread that keeps the song queue running.
    """
    while True:
        time.sleep(2)
        if len(song_q) > 0:
            if outer_ctx is not None:
                try:
                    if not outer_ctx.voice_client.is_playing() and not outer_ctx.voice_client.is_paused():
                        song = song_q.pop(0)
                        outer_ctx.voice_client.play(song)
                        global current_song
                        global duration
                        current_song = song_list.pop(0)
                        duration = song_duration_list.pop(0)
                except QueueFailure:
                    print('Queue messed up')


def foreground():
    """
    This is the main foreground thread in which all the bot commands occur.
    """

    @client.command()
    async def join(ctx):
        """
        This method allows the bot to join the voice channel. Bot can only join if the user is currently in a voice
        channel.
        """
        if ctx.author.voice is None:
            await ctx.send("Please enter a voice channel :)")
        else:
            voice_channel = ctx.author.voice.channel
            if ctx.voice_client is None:
                await voice_channel.connect()
                global outer_ctx
                outer_ctx = ctx
                await ctx.send('Bot has joined!')
            else:
                await ctx.voice_client.move_to(voice_channel)

    @client.command()
    async def disconnect(ctx):
        """
        This method disconnects the bot from the voice chat.
        """
        song_q.clear()
        song_list.clear()
        song_duration_list.clear()
        await ctx.send('Ta-ta for now!')
        await ctx.voice_client.disconnect()

    @client.command()
    async def play(ctx, *query):
        """
        This method allows the user to search anything into youtube and the first result is played back. The user enters
        a string input, the method then queries Youtube with the users input. The video id's of the results are sent back
        as a response from the request query. The first video id is then added to a Youtube watch url. The resulting
        url is what is needed for youtube_dl.py to stream the audio to the discord server.
        """
        if ctx.voice_client is None:
            await ctx.send('Please use the "?join" command!')
            return
        url = str(format('+'.join(query)))
        html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + url)
        video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
        new_url = str('https://www.youtube.com/watch?v=' + video_ids[0])

        FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        YDL_OPTIONS = {'format': "bestaudio"}

        with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(new_url, download=False)
            song_duration_list.append(info['duration'])
            url2 = info['formats'][0]['url']
            song_list.append((info['title'], new_url))
            source = await discord.FFmpegOpusAudio.from_probe(url2,  **FFMPEG_OPTIONS)
            song_q.append(source)
            if not threading.Thread(target=background).is_alive():
                x = threading.Thread(target=background)
                x.start()

    @client.command()
    async def skip(ctx):
        """
        This method allows a user to skip to the next song in the queue.
        """
        if ctx.voice_client is None:
            await ctx.send('Please use the "?join" command!')
            return
        ctx.voice_client.stop()
        await ctx.send('Skipped!')

    @client.command()
    async def pause(ctx):
        """
        This method allows a user to pause the current song.
        """
        if ctx.voice_client is None:
            await ctx.send('Please use the "?join" command!')
            return
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send('Paused')
        else:
            await ctx.send('Nothing is playing at the moment.')

    @client.command()
    async def resume(ctx):
        """
        This method allows a user to resume the current song if paused. If the song is not paused, the song carries on
        as usual.
        """
        if ctx.voice_client is None:
            await ctx.send('Please use the "?join" command!')
            return
        if ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send('Resumed')
            return
        if ctx.voice_client.is_playing():
            await ctx.send('The current song is not paused.')
        else:
            await ctx.send('Nothing is playing at the moment.')

    @client.command()
    async def np(ctx):
        """
        This method gives the current name and length of the song currently playing.
        """
        if ctx.voice_client is None:
            await ctx.send('Please use the "?join" command!')
            return
        if ctx.voice_client.is_playing():
            hours = duration//3600
            mins = (duration - (hours*3600)) // 60
            secs = duration % 60
            if mins < 10:
                mins = '0' + str(mins)
            if secs < 10:
                secs = '0' + str(secs)
            if hours > 0:
                expanded_dur = f'{hours}:{mins}:{secs}'
            else:
                expanded_dur = f'{mins}:{secs}'
            await ctx.send(f'The current Youtube video playing is: {current_song[0]}')
            await ctx.send(f'Duration of current song is: {expanded_dur}')
        else:
            await ctx.send('Nothing is playing at the moment.')

    @client.command()
    async def q(ctx):
        """
        This method returns a list of the songs in the song queue to the voice channel.
        """
        if ctx.voice_client is None:
            await ctx.send('Please use the "?join" command!')
            return
        if len(song_q) == 0:
            await ctx.send('Song queue is empty!')
        else:
            await ctx.send(song_list)

    @client.command()
    async def clear(ctx):
        """
        This method clears the song queue.
        """
        if ctx.voice_client is None:
            await ctx.send('Please use the "?join" command!')
            return
        song_q.clear()
        song_list.clear()
        song_duration_list.clear()
        await ctx.send('Song queue is cleared!')

    @client.command()
    async def add2(ctx, playlist):
        """
        This method adds the current video playing to the specified playlist.
        """
        if ctx.voice_client is None:
            await ctx.send('Please use the "?join" command!')
            return
        try:
            driver = webdriver.Chrome(options=options)
            driver.get(playlists[playlist])
            driver.find_element_by_xpath(
                '/html/body/ytd-app/div/ytd-page-manager/ytd-browse/ytd-playlist-sidebar-renderer/div/ytd-playlist-sidebar-primary-info-renderer/div[4]/ytd-menu-renderer/yt-icon-button/button').click()
            driver.find_element_by_xpath(
                '/html/body/ytd-app/ytd-popup-container/tp-yt-iron-dropdown/div/ytd-menu-popup-renderer/tp-yt-paper-listbox/ytd-menu-service-item-renderer[1]').click()
            driver.switch_to.frame(driver.find_element_by_class_name('picker-frame'))
            driver.implicitly_wait(1)
            driver.find_element_by_xpath('/html/body/div[2]/div/div[3]/div[2]/div/div[1]/div/div/div[2]').click()
            driver.find_element_by_xpath(
                '/html/body/div[2]/div/div[3]/div[2]/div/div[2]/div/div[2]/div[1]/div/input').send_keys(current_song[1])
            driver.find_element_by_xpath('/html/body/div[2]/div/div[3]/div[2]/div/div[2]/div/div[2]/div[2]').click()
            driver.find_element_by_xpath(
                '/html/body/div[2]/div/div[3]/div[2]/div/div[2]/div/div[2]/div[2]/div[1]/div/div[1]').click()
            time.sleep(3)
            driver.close()
            await ctx.send('Video added to playlist!')
        except WebdriverError:
            await ctx.send('Sorry, something went wrong with the Web Driver.')

    @client.command()
    async def qp(ctx, playlist):
        """
        This method adds an entire playlist to the queue.
        """
        if ctx.voice_client is None:
            await ctx.send('Please use the "?join" command!')
            return
        if playlist in playlists:
            playlist_url = playlists[playlist]
        else:
            playlist_url = playlist
        await ctx.send('Adding Playlist to Queue. Please wait a moment before giving any new commands.')
        try:
            FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                              'options': '-vn'}
            YDL_OPTIONS = {'format': "bestaudio"}

            with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(playlist_url, download=False)
                for i in range(len(info['entries'])):
                    song_duration_list.append(info['entries'][i]['duration'])
                    song_url = str('https://www.youtube.com/watch?v=' + info["entries"][i]["id"])
                    song_list.append((info['entries'][i]['title'], song_url))
                    source = await discord.FFmpegOpusAudio.from_probe(info["entries"][i]["url"], **FFMPEG_OPTIONS)
                    song_q.append(source)
                    if not threading.Thread(target=background).is_alive():
                        x = threading.Thread(target=background)
                        x.start()
                await ctx.send('Playlist has been added to the Queue!')
        except InvalidPlaylistName:
            await ctx.send('Invalid Playlist Name/URL')


f = threading.Thread(target=foreground)
f.start()
b = threading.Thread(target=background)
b.daemon = True
b.start()


client.run(TOKEN)
