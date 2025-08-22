import requests
import re
import subprocess
import time
import random
from bs4 import BeautifulSoup

# The main URL where the list of episodes is located
MAIN_URL = "https://myanime.live/tag/qin-chen/"
LAST_EPISODE_TO_GRAB = 600
FIRST_EPISODE_TO_GRAB = 551
PAGE_URL_PATTERN = r"https?://myanime\.live/\d{4}/\d{2}/\d{2}/(?:wu-shen-zhu-zai)?-?(?:martial-master)?(?:-anime)?-episode-\d{2,3}-english-sub/?"
SHOW_NAME = "Martial Master"

# --- Main function to run the script ---
def main():
    """
    Main function to find and download episodes.
    """
    print(f"🔎 Checking for episodes at: {MAIN_URL}")
    page_num = 1
    try:
        # Get the list of episode pages
        episode_urls = get_episode_urls(MAIN_URL)
        if not episode_urls:
            print("❌ Could not find any episode links. The website structure might have changed.")
            return
        
        latest_episode = episode_urls[0]
        match = re.search(r"episode-(\d+)", latest_episode)
        latest_episode_num = int(match.group(1))

        last_episode = episode_urls[len(episode_urls)-1]
        match = re.search(r"episode-(\d+)", last_episode)
        episode_num = int(match.group(1))

        episode_diff = latest_episode_num - LAST_EPISODE_TO_GRAB
        if episode_diff > 10:
            page_num += ((episode_diff // 10) -1)
            episode_urls.clear()

        
        while episode_num > FIRST_EPISODE_TO_GRAB:
            time.sleep(random.randint(0, 2))
            page_num += 1
            more_episodes = get_episode_urls(MAIN_URL + "page/" + str(page_num) + "/")
            if not more_episodes:
                print("No more episodes found on this page.")
                break
            episode_urls.extend(more_episodes)
            last_episode = episode_urls[len(episode_urls)-1]
            match = re.search(r"episode-(\d+)", last_episode)
            episode_num = int(match.group(1))

        
        # Remove any episode not wanted on the last page
        extra = abs(episode_num - FIRST_EPISODE_TO_GRAB)
        if extra > 0:
            del episode_urls[-extra:]  # Remove any episodes beyond the last one we want to grab

        # Remove any episodes we've already downloaded
        latest_episode = episode_urls[0]
        match = re.search(r"episode-(\d+)", latest_episode)
        latest_episode_num = int(match.group(1))
        extra = latest_episode_num - LAST_EPISODE_TO_GRAB
        del episode_urls[:extra]

        print("Episodes to grab:")
        print(episode_urls)
        # Process each episode link
        for i, link in enumerate(episode_urls):
            print(f"--- Processing Episode {i+1}/{len(episode_urls)} ---")
            print(f"Page URL: {link}")
            
            # Get the page source for the episode
            response = requests.get(link)
            response.raise_for_status() # Raises an error for bad status codes

            # Find the ok.ru video URL in the page source
            ok_ru_url = find_video_url(response.text)

            if ok_ru_url:
                print(f"🎬 Found Video URL: {ok_ru_url}")
                match = re.search(r"episode-(\d+)", link)
                episode_num = int(match.group(1))
                download_video(ok_ru_url, episode_num)
            else:
                print("⚠️ Could not find an ok.ru video URL on this page.")

            print("-" * 20 + "\n")
            time.sleep(random.randint(15, 30))

    except requests.RequestException as e:
        print(f"❌ An error occurred with the network request: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

def get_episode_urls(url):
    # Scrapes the URL to find all individual episode page links.
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    
    links = []
    episode_urls = []
    content_divs = soup.find_all('div', class_='entry-main-content')
    for content_div in content_divs:
        #a_hrefs = content_div.find_all('a', href=True)
        for a_tag in content_div.find_all('a', href=True):
            #print(a_tag)
            links.append(a_tag['href'])
    episode_urls = get_filtered_links(links)
    return episode_urls

def find_video_url(page_source):
    """
    Searches the provided HTML source for an ok.ru video URL using regex.
    """
    # Regex to find a URL pattern like: https://geo.dailymotion.com/player.html?video=k1QT6Kj34oOHxhAt5iu&#038;
    #match = re.search(r'src="//ok\.ru/videoembed/(\d+)', page_source)
    match = re.search(r'https://geo\.dailymotion\.com/player\.html\?video=([^"?]+)', page_source)
    if match:
        return match.group(0)
    else:
        match = re.search(r'https://www\.dailymotion\.com/embed/video/([^"?]+)', page_source)
        if match:
            return match.group(0)
    return None

def download_video(video_url, episode_num):
    """
    Calls yt-dlp to download the video from the given URL.
    """
    try:
        print("🚀 Starting download with yt-dlp...")
        # Command to execute: yt-dlp -o "output_filename.ext" video_url
        command = [
            "yt-dlp",
            "-o", f"{SHOW_NAME} - " + str(episode_num) + "[%(resolution)s].%(ext)s", # Sensible filename template
            video_url
        ]
        subprocess.run(command, check=True)
        print("✅ Download complete!")
    except FileNotFoundError:
        print("❌ ERROR: 'yt-dlp' command not found.")
        print("Please make sure yt-dlp is installed and in your system's PATH.")
    except subprocess.CalledProcessError as e:
        print(f"❌ yt-dlp returned an error: {e}")

def get_filtered_links(url_list):
    """
    Filters a list of URLs to find ones that match a specific pattern.
    """
    # Regex to find a URL with a date and specific show name format.
    # We use re.compile for efficiency if we were using the pattern many times.
    pattern = re.compile(PAGE_URL_PATTERN)
    filtered_links = []
    for url in url_list:
        if pattern.match(url):
            filtered_links.append(url)
    return filtered_links

if __name__ == "__main__":
    main()