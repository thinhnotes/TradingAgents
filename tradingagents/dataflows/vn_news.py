"""
vn_news.py - News fetcher module for Vietnamese stock market news.

This module provides functions to fetch stock news from Vietnamese sources
like CafeF, Vietstock, and other Vietnamese financial news portals.

Features:
- Fetch news by ticker symbol
- HTML content cleaned and converted to plain text
- Output format compatible with existing news data format
- Error handling for network failures
- Caching to reduce API calls (30 minutes TTL for news)
"""

from typing import Annotated, List, Dict, Optional
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests
from bs4 import BeautifulSoup
import time
import random
import re

# Import caching utilities
from .cache import (
    get_cache,
    generate_cache_key,
    DEFAULT_NEWS_TTL_SECONDS,
)


# TTL constants for VN news data (in seconds)
VN_NEWS_TTL = DEFAULT_NEWS_TTL_SECONDS  # 30 minutes for news


# User agent for web requests
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Request headers
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


def _clean_html_text(html_text: str) -> str:
    """
    Clean HTML content and convert to plain text.

    Removes HTML tags, extra whitespace, and normalizes text for LLM consumption.

    Args:
        html_text: Raw HTML content string

    Returns:
        Cleaned plain text string
    """
    if not html_text:
        return ""

    # Parse HTML and extract text
    soup = BeautifulSoup(html_text, "html.parser")

    # Remove script and style elements
    for element in soup(["script", "style", "noscript", "iframe"]):
        element.decompose()

    # Get text content
    text = soup.get_text(separator=" ", strip=True)

    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    return text


def _make_request(url: str, timeout: int = 10) -> Optional[requests.Response]:
    """
    Make HTTP request with error handling and rate limiting.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        Response object or None if request failed
    """
    # Random delay to avoid rate limiting
    time.sleep(random.uniform(1, 3))

    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        return None


def _fetch_cafef_news(ticker: str, max_articles: int = 10) -> List[Dict[str, str]]:
    """
    Fetch news from CafeF for a specific ticker.

    CafeF is one of the major Vietnamese financial news portals.

    Args:
        ticker: Vietnamese stock ticker (e.g., 'VNM', 'FPT', 'TCB')
        max_articles: Maximum number of articles to fetch

    Returns:
        List of news article dictionaries
    """
    news_results = []
    ticker_upper = ticker.upper()

    # CafeF stock page URL pattern
    url = f"https://cafef.vn/tim-kiem.chn?keywords={ticker_upper}"

    try:
        response = _make_request(url)
        if not response:
            return news_results

        soup = BeautifulSoup(response.content, "html.parser")

        # Find news articles - CafeF uses various container classes
        articles = soup.select("div.tlitem, div.box-category-item, li.news-item")[:max_articles]

        for article in articles:
            try:
                # Extract title
                title_elem = article.select_one("h3 a, h2 a, a.title")
                if not title_elem:
                    continue

                title = _clean_html_text(title_elem.get_text())
                link = title_elem.get("href", "")

                # Make link absolute if relative
                if link and not link.startswith("http"):
                    link = f"https://cafef.vn{link}"

                # Extract snippet/description
                snippet_elem = article.select_one("p.sapo, div.sapo, p.description")
                snippet = _clean_html_text(snippet_elem.get_text()) if snippet_elem else ""

                # Extract date
                date_elem = article.select_one("span.time, span.date, div.time")
                date = _clean_html_text(date_elem.get_text()) if date_elem else ""

                if title:
                    news_results.append({
                        "title": title,
                        "snippet": snippet,
                        "link": link,
                        "date": date,
                        "source": "CafeF",
                    })

            except Exception:
                continue

    except Exception:
        pass

    return news_results


def _fetch_vietstock_news(ticker: str, max_articles: int = 10) -> List[Dict[str, str]]:
    """
    Fetch news from Vietstock for a specific ticker.

    Vietstock is another major Vietnamese financial news and data portal.

    Args:
        ticker: Vietnamese stock ticker (e.g., 'VNM', 'FPT', 'TCB')
        max_articles: Maximum number of articles to fetch

    Returns:
        List of news article dictionaries
    """
    news_results = []
    ticker_upper = ticker.upper()

    # Vietstock company news URL pattern
    url = f"https://finance.vietstock.vn/{ticker_upper}/tin-tuc.htm"

    try:
        response = _make_request(url)
        if not response:
            return news_results

        soup = BeautifulSoup(response.content, "html.parser")

        # Find news articles
        articles = soup.select("div.news-item, li.news-item, div.article-item")[:max_articles]

        for article in articles:
            try:
                # Extract title
                title_elem = article.select_one("a.title, h3 a, h2 a")
                if not title_elem:
                    continue

                title = _clean_html_text(title_elem.get_text())
                link = title_elem.get("href", "")

                # Make link absolute if relative
                if link and not link.startswith("http"):
                    link = f"https://finance.vietstock.vn{link}"

                # Extract snippet
                snippet_elem = article.select_one("p.sapo, div.description, p.desc")
                snippet = _clean_html_text(snippet_elem.get_text()) if snippet_elem else ""

                # Extract date
                date_elem = article.select_one("span.date, span.time, div.date")
                date = _clean_html_text(date_elem.get_text()) if date_elem else ""

                if title:
                    news_results.append({
                        "title": title,
                        "snippet": snippet,
                        "link": link,
                        "date": date,
                        "source": "Vietstock",
                    })

            except Exception:
                continue

    except Exception:
        pass

    return news_results


def _fetch_vnexpress_finance_news(ticker: str, max_articles: int = 10) -> List[Dict[str, str]]:
    """
    Fetch financial news from VnExpress mentioning a specific ticker.

    VnExpress is one of Vietnam's largest online newspapers with comprehensive
    financial coverage.

    Args:
        ticker: Vietnamese stock ticker (e.g., 'VNM', 'FPT', 'TCB')
        max_articles: Maximum number of articles to fetch

    Returns:
        List of news article dictionaries
    """
    news_results = []
    ticker_upper = ticker.upper()

    # VnExpress search URL
    url = f"https://timkiem.vnexpress.net/?q={ticker_upper}&cate_code=kinhdoanh"

    try:
        response = _make_request(url)
        if not response:
            return news_results

        soup = BeautifulSoup(response.content, "html.parser")

        # Find news articles
        articles = soup.select("article.item-news, div.item-news")[:max_articles]

        for article in articles:
            try:
                # Extract title
                title_elem = article.select_one("h2.title-news a, h3.title-news a, a.title-news")
                if not title_elem:
                    continue

                title = _clean_html_text(title_elem.get_text())
                link = title_elem.get("href", "")

                # Extract snippet
                snippet_elem = article.select_one("p.description, p.lead, div.description")
                snippet = _clean_html_text(snippet_elem.get_text()) if snippet_elem else ""

                # Extract date
                date_elem = article.select_one("span.time-ago, span.date, span.time")
                date = _clean_html_text(date_elem.get_text()) if date_elem else ""

                if title:
                    news_results.append({
                        "title": title,
                        "snippet": snippet,
                        "link": link,
                        "date": date,
                        "source": "VnExpress",
                    })

            except Exception:
                continue

    except Exception:
        pass

    return news_results


def get_vn_stock_news(
    ticker: Annotated[str, "Vietnamese stock ticker symbol (e.g., VNM, FPT, TCB)"],
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "Number of days to look back for news"],
) -> str:
    """
    Fetch stock news from Vietnamese financial news sources.

    This function aggregates news from multiple Vietnamese financial news sources
    including CafeF, Vietstock, and VnExpress. The output is cleaned and formatted
    for LLM consumption. Results are cached for 30 minutes to reduce API calls.

    Args:
        ticker: Vietnamese stock ticker (e.g., 'VNM', 'FPT', 'TCB')
        curr_date: Current date in YYYY-MM-DD format
        look_back_days: Number of days to look back for news

    Returns:
        Formatted string with news articles from Vietnamese sources
    """
    ticker = ticker.upper().strip()

    # Validate date format
    try:
        end_date = datetime.strptime(curr_date, "%Y-%m-%d")
        start_date = end_date - relativedelta(days=look_back_days)
    except ValueError:
        return f"Error: Invalid date format. Please use YYYY-MM-DD format."

    # Generate cache key
    cache = get_cache()
    cache_key = generate_cache_key(
        "vn_stock_news",
        ticker=ticker,
        curr_date=curr_date,
        look_back_days=look_back_days
    )

    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    # Fetch news from multiple sources
    all_news = []

    try:
        cafef_news = _fetch_cafef_news(ticker, max_articles=5)
        all_news.extend(cafef_news)
    except Exception as e:
        pass  # Silently handle CafeF failures

    try:
        vietstock_news = _fetch_vietstock_news(ticker, max_articles=5)
        all_news.extend(vietstock_news)
    except Exception as e:
        pass  # Silently handle Vietstock failures

    try:
        vnexpress_news = _fetch_vnexpress_finance_news(ticker, max_articles=5)
        all_news.extend(vnexpress_news)
    except Exception as e:
        pass  # Silently handle VnExpress failures

    # If no news found, return informative message
    if not all_news:
        return f"No news found for {ticker} from Vietnamese sources (CafeF, Vietstock, VnExpress) in the past {look_back_days} days."

    # Format news for output - same format as google.py
    news_str = ""
    for news in all_news:
        title = news.get("title", "")
        source = news.get("source", "Unknown")
        snippet = news.get("snippet", "")
        date = news.get("date", "")

        news_str += f"### {title} (source: {source}"
        if date:
            news_str += f", {date}"
        news_str += f")\n\n{snippet}\n\n"

    # Build result header
    start_str = start_date.strftime("%Y-%m-%d")
    header = f"## Vietnamese Stock News for {ticker}, from {start_str} to {curr_date}:\n\n"
    header += f"# Sources: CafeF, Vietstock, VnExpress\n"
    header += f"# Total articles found: {len(all_news)}\n\n"

    result = header + news_str

    # Cache the result
    cache.set(cache_key, result, ttl_seconds=VN_NEWS_TTL)

    return result


def get_vn_global_news(
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "Number of days to look back for news"],
) -> str:
    """
    Fetch global/market-wide news from Vietnamese financial news sources.

    This function fetches general market news from Vietnamese sources,
    covering topics like the VN-Index, market trends, and economic news.
    Results are cached for 30 minutes to reduce API calls.

    Args:
        curr_date: Current date in YYYY-MM-DD format
        look_back_days: Number of days to look back for news

    Returns:
        Formatted string with market news from Vietnamese sources
    """
    # Validate date format
    try:
        end_date = datetime.strptime(curr_date, "%Y-%m-%d")
        start_date = end_date - relativedelta(days=look_back_days)
    except ValueError:
        return f"Error: Invalid date format. Please use YYYY-MM-DD format."

    # Generate cache key
    cache = get_cache()
    cache_key = generate_cache_key(
        "vn_global_news",
        curr_date=curr_date,
        look_back_days=look_back_days
    )

    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    news_results = []

    # Fetch from CafeF market section
    try:
        url = "https://cafef.vn/thi-truong-chung-khoan.chn"
        response = _make_request(url)

        if response:
            soup = BeautifulSoup(response.content, "html.parser")
            articles = soup.select("div.tlitem, div.box-category-item, li.news-item")[:10]

            for article in articles:
                try:
                    title_elem = article.select_one("h3 a, h2 a, a.title")
                    if not title_elem:
                        continue

                    title = _clean_html_text(title_elem.get_text())
                    link = title_elem.get("href", "")
                    if link and not link.startswith("http"):
                        link = f"https://cafef.vn{link}"

                    snippet_elem = article.select_one("p.sapo, div.sapo, p.description")
                    snippet = _clean_html_text(snippet_elem.get_text()) if snippet_elem else ""

                    date_elem = article.select_one("span.time, span.date, div.time")
                    date = _clean_html_text(date_elem.get_text()) if date_elem else ""

                    if title:
                        news_results.append({
                            "title": title,
                            "snippet": snippet,
                            "link": link,
                            "date": date,
                            "source": "CafeF",
                        })
                except Exception:
                    continue

    except Exception:
        pass

    # If no news found
    if not news_results:
        return f"No global market news found from Vietnamese sources in the past {look_back_days} days."

    # Format news for output
    news_str = ""
    for news in news_results:
        title = news.get("title", "")
        source = news.get("source", "Unknown")
        snippet = news.get("snippet", "")
        date = news.get("date", "")

        news_str += f"### {title} (source: {source}"
        if date:
            news_str += f", {date}"
        news_str += f")\n\n{snippet}\n\n"

    # Build result header
    start_str = start_date.strftime("%Y-%m-%d")
    header = f"## Vietnamese Market News, from {start_str} to {curr_date}:\n\n"
    header += f"# Sources: CafeF (Market Section)\n"
    header += f"# Total articles found: {len(news_results)}\n\n"

    result = header + news_str

    # Cache the result
    cache.set(cache_key, result, ttl_seconds=VN_NEWS_TTL)

    return result
