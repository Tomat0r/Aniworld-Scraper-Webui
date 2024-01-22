import re
import urllib.request
from urllib.error import URLError
from bs4 import BeautifulSoup
import logging

from src.logic.language import ProviderError, get_href_by_language

# Basic logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Patterns
VOE_PATTERN = re.compile(r"'hls': '(?P<url>.+)'")
STREAMTAPE_PATTERN = re.compile(r'get_video\?id=[^&\'\s]+&expires=[^&\'\s]+&ip=[^&\'\s]+&token=[^&\'\s]+\'')

# Cache attempts counter
cache_url_attempts = 0

def get_redirect_link_by_provider(site_url, internal_link, language):
    for provider in ["VOE", "Streamtape", "Vidoza"]:
        try:
            return get_redirect_link(site_url, internal_link, language, provider)
        except ProviderError:
            continue
    raise ProviderError("No suitable provider found.")

def get_redirect_link(site_url, html_link, language, provider):
    html_response = urllib.request.urlopen(html_link)
    href_value = get_href_by_language(html_response, language, provider)
    link_to_redirect = site_url + href_value
    logging.debug("Link to redirect is: " + link_to_redirect)
    return link_to_redirect, provider

def find_cache_url(url, provider):
    global cache_url_attempts
    logging.debug(f"Entered {provider} to cache")
    try:
        html_page = urllib.request.urlopen(url)
        soup = BeautifulSoup(html_page, features="html.parser")
        if provider == "Vidoza":
            cache_link = soup.find("source").get("src")
        elif provider == "VOE":
            cache_link = VOE_PATTERN.search(html_page.read().decode('utf-8')).group("url")
        elif provider == "Streamtape":
            cache_link = STREAMTAPE_PATTERN.search(html_page.read().decode('utf-8'))
            if cache_link:
                cache_link = "https://" + provider + ".com/" + cache_link.group()[:-1]
            else:
                raise AttributeError
    except (URLError, AttributeError) as e:
        logging.warning(f"Attempt {cache_url_attempts + 1} failed for {provider}: {e}")
        if cache_url_attempts < 5:
            cache_url_attempts += 1
            return find_cache_url(url, provider)
        else:
            logging.error(f"Could not find cache url for {provider}.")
            return None
    logging.debug(f"Found cache link for {provider}: {cache_link}")
    return cache_link
