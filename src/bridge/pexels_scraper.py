"""Scrape Pexels videos via Chrome Bridge — no API key needed (CC0 license)."""
from playwright.sync_api import sync_playwright
import time, json, sys

CDP_URL = "http://localhost:9222"

def search_pexels(query: str, max_results: int = 5):
    """Open Pexels search and extract video URLs."""
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0]
        page = context.new_page()

        url = f"https://www.pexels.com/search/videos/{query.replace(' ', '%20')}/"
        print(f"[NAV] {url}")
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)
        page.evaluate("window.scrollTo(0, 600)")
        time.sleep(2)

        # Pexels embeds <video> tags with sources
        video_data = page.evaluate("""
        () => {
          const items = [];
          document.querySelectorAll('article a[href*="/video/"]').forEach(a => {
            const href = a.href;
            const img = a.querySelector('img');
            const src = img ? img.src : null;
            items.push({href, thumb: src});
          });
          return items.slice(0, 20);
        }
        """)
        page.close()
        return video_data[:max_results]


def get_pexels_download_url(video_page_url: str) -> str:
    """Open a Pexels video page and extract the download URL."""
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0]
        page = context.new_page()
        page.goto(video_page_url, wait_until="domcontentloaded", timeout=20000)
        time.sleep(3)

        # Look for video source
        video_src = page.evaluate("""
        () => {
          const v = document.querySelector('video source');
          if (v) return v.src;
          const v2 = document.querySelector('video');
          if (v2 && v2.src) return v2.src;
          return null;
        }
        """)
        page.close()
        return video_src


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "molten metal"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    results = search_pexels(query, n)
    print(f"\n=== {len(results)} resultados para '{query}' ===")
    for r in results:
        print(f"  - {r['href']}")
    print()
    print(json.dumps(results, indent=2))
