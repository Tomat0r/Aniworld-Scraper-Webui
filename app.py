import subprocess
import threading
import time
import platform
import os
import logging
#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
import requests
from bs4 import BeautifulSoup
import shlex
from flask import Flask, render_template, request, jsonify
from src.logic.search_for_links import (find_cache_url,
                                        get_redirect_link_by_provider)
import subprocess
import urllib.request
output_path = "./data"
site_url = {
    "serie": "https://s.to",  # maybe you need another dns to be able to use this site
    "anime": "https://aniworld.to"
}
app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def individual():
    if request.method == 'POST':
        Itype = request.form.get('type')
        Iname = request.form.get('name').replace(" ", "-")
        Ilanguage = request.form.get('language')
        if not Itype or not Iname:
            show_alert = True
            return render_template('individual_selection.html', show_alert=show_alert)
        
        base_url = site_url[Itype].rstrip('/')
        
        constructed_url = f"{base_url}/{Itype}/stream/{urllib.parse.quote(Iname)}/"  # Construct URL with URL-encoded Iname
        logging.info(constructed_url)
        counter_seasons = get_season(constructed_url)
        seasons_data = get_episodes(constructed_url, counter_seasons)
        
        return render_template('individual_overview.html', Itype=Itype, Iname=Iname, url=constructed_url, counter_seasons=counter_seasons, seasons_data=seasons_data, Ilanguage=Ilanguage)

    return render_template('individual_selection.html')

@app.route('/download_episode', methods=['POST'])
def download_episode():
    data = request.json
    season = data['season']
    episode_number = data['episodeNumber']
    episode_title = data['episodeTitle']
    episode_link = data['episodeLink']
    language = data['Ilanguage']
    name = data['Iname']
    type = data['Itype']

    logging.info(f"Download requested for {type} | {name}, Season {season}, Episode {episode_number}, Language: '{language}': '{episode_title}', Link: '{episode_link}'")
    anime_url = f"https://aniworld.to/anime/stream/{name}/"
    link = f"{anime_url}staffel-{season}/episode-{episode_number}"
    
    # Retrieve redirect link and cache URL
    redirect_link, provider = get_redirect_link_by_provider(site_url[type], link, language)
    logging.debug(f"Link to redirect is: {redirect_link}")
    cache_url = find_cache_url(redirect_link, provider)
    logging.debug(f"{provider} Cache URL is: {cache_url}")  

    # Modify here to create the desired file path and name
    file_name = f"{output_path}/{name}/Season {season}/E{episode_number} - {episode_title}.mp4"
    directory = os.path.dirname(file_name)
    if not os.path.exists(directory):
        os.makedirs(directory)
        logging.info(f"Created directory: {directory}")

    # Now, check if the file exists
    if os.path.exists(file_name):
        logging.info(f"Episode {file_name} already downloaded.")
    else:
        logging.info(f"File not downloaded. Downloading: {file_name}")
        create_new_download_thread(cache_url, file_name, provider)

    return jsonify({'message': f'Download initiated for Season {season}, Episode {episode_number}, Title: {episode_title}'})

@app.route('/download_season', methods=['POST'])
def download_season():
    data = request.json
    season = data['season']
    language = data['language']
    name = data['name']
    type = data['type']

    # Base URL for the series
    base_url = f"https://aniworld.to/anime/stream/{name}/"
    episodes_data = get_episodes(base_url, season)

    # Check if any episodes are available for the season
    if season in episodes_data and episodes_data[season]:
        first_download_initiated = False  # Flag to check if the first download has started

        for episode in episodes_data[season]:
            episode_number = episode['number']
            episode_title = episode['title']
            episode_link = episode['link']

            logging.info(f"Download requested for {type} | {name}, Season {season}, Episode {episode_number}, Language: '{language}': '{episode_title}', Link: '{episode_link}'")
            anime_url = f"{base_url}staffel-{season}/episode-{episode_number}"

            # Retrieve redirect link and cache URL
            redirect_link, provider = get_redirect_link_by_provider(site_url[type], anime_url, language)
            logging.debug(f"Link to redirect is: {redirect_link}")
            cache_url = find_cache_url(redirect_link, provider)
            logging.debug(f"{provider} Cache URL is: {cache_url}")

            # Define file path and name
            file_name = f"{output_path}/{name}/Season {season}/E{episode_number} - {episode_title}.mp4"
            directory = os.path.dirname(file_name)
            if not os.path.exists(directory):
                os.makedirs(directory)
                logging.info(f"Created directory: {directory}")

            # Check if the file exists
            if os.path.exists(file_name):
                logging.info(f"Episode {file_name} already downloaded.")
            else:
                logging.info(f"File not downloaded. Downloading: {file_name}")
                create_new_download_thread(cache_url, file_name, provider)
                logging.info("Delaying Download")
                time.sleep(20)  # Delay for 20 seconds

    else:
        return jsonify({'message': f'No episodes found for Season {season}'})

    return jsonify({'message': f'Download initiated for Season {season}'})



def get_season(url):
    counter_seasons = 1
    html_page = urllib.request.urlopen(url, timeout=50)
    soup = BeautifulSoup(html_page, features="html.parser")
    for link in soup.findAll('a'):
        seasons = str(link.get("href"))
        if "/staffel-{}".format(counter_seasons) in seasons:
            counter_seasons = counter_seasons + 1
    return counter_seasons - 1


def scrape_episode_title(episode_url):
    try:
        response = requests.get(episode_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            element = soup.find('small', class_='episodeEnglishTitle')
            if element:
                title = element.get_text()
                logging.info(f"Title scraped successfully: {title}")
                return title
            else:
                logging.warning(f"No title found for URL: {episode_url}")
                return "Title Not Found"
        else:
            logging.error(f"Failed to retrieve page: {episode_url}, Status code: {response.status_code}")
            return "Request Failed"
    except Exception as e:
        logging.exception(f"Exception occurred while scraping title: {e}")
        return "Error: " + str(e)



def get_episodes(base_url, num_seasons):
    seasons_data = {}
    for season in range(1, num_seasons + 1):
        season_url = f"{base_url}staffel-{season}/"
        episodes = []
        processed_links = set()  # Store processed links to avoid duplicates
        episode_number = 1  # Initialize episode number for each season
        try:
            html_page = urllib.request.urlopen(season_url, timeout=50)
            soup = BeautifulSoup(html_page, features="html.parser")
            for link in soup.findAll('a'):
                relative_episode_link = link.get("href")
                if (relative_episode_link and 
                    f"/staffel-{season}/episode-" in relative_episode_link and 
                    relative_episode_link not in processed_links):
                    processed_links.add(relative_episode_link)  # Add to processed links
                    absolute_episode_link = urllib.parse.urljoin(base_url, relative_episode_link)
                    episode_title = scrape_episode_title(absolute_episode_link)
                    episodes.append({
                        'number': episode_number,
                        'title': episode_title,
                        'link': absolute_episode_link
                    })
                    episode_number += 1  # Increment episode number
            seasons_data[season] = episodes
            logging.info(f"Episodes for Season {season} fetched successfully.")
        except Exception as e:
            logging.exception(f"Exception occurred while fetching episodes for Season {season}: {e}")

    # Log the summary of seasons data
    for season, eps in seasons_data.items():
        logging.info(f"Season {season}: {len(eps)} episodes")

    return seasons_data

def already_downloaded(file_name):
    if os.path.exists(file_name) and os.path.getsize(file_name) > 0:
        logging.info("Episode {} already downloaded.".format(file_name))
        return True
    logging.debug("File not downloaded. Downloading: {}".format(file_name))
    return False

def download(link, file_name):
    retry_count = 0
    while True:
        logging.debug("Entered download with these vars: Link: {}, File_Name: {}".format(link, file_name))
        r = requests.get(link, stream=True)
        with open(file_name, 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        if os.path.getsize(file_name) != 0:
            logging.info("Finished download of {}.".format(file_name))
            break
        elif retry_count == 1:
            logging.error("Server error. Could not download {}. Please manually download it later.".format(file_name))
            break
        else:
            logging.info("Download did not complete! File {} will be retried in a few seconds.".format(file_name))
            logging.debug("URL: {}, filename {}".format(link, file_name))
            time.sleep(20)
            retry_count = 1

def download_and_convert_hls_stream(hls_url, file_name):    
    try:
        
        ffmpeg_cmd = ['ffmpeg', '-i', hls_url, '-c', 'copy', file_name]
        if platform.system() == "Windows":
            logging.info("Running on Windows ")
            subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)    
        logging.info("Finished download of {}.".format(file_name))
    except subprocess.CalledProcessError as e:
        logging.error("Server error. Could not download {}. Please manually download it later.".format(file_name))

def create_new_download_thread(url, file_name, provider):
    logging.debug("Entered Downloader.")
    
    if provider in ["Vidoza", "Streamtape"]:
        threading.Thread(target=download, args=(url, file_name)).start()
    elif provider == "VOE":
        threading.Thread(target=download_and_convert_hls_stream, args=(url, file_name)).start()
        logging.debug("Downloader VOE")
    
    logging.info("File {} added to queue.".format(file_name))





if __name__ == '__main__':
    app.run(debug=True)

