import logging
from typing import Dict, Any, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def fetch_interest_rates(url: Optional[str] = None, timeout: int = 5) -> Dict[str, Any]:
    
    fallback = {
        "source": url or "fallback",
        "rates": {
            "savings": "0.50%",
            "checking": "0.10%",
            "term_deposit": "1.25%",
        },
    }

    if not url:
        return fallback

    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "BMS-Scraper/1.0"})
        resp.raise_for_status()
    except Exception as exc:
        logger.warning("Failed to fetch %s: %s", url, exc)
        return fallback

    try:
        soup = BeautifulSoup(resp.text, "html.parser")
        rates = {}
        
        table = soup.find("table")
        if table:
            headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
            for tr in table.find_all("tr"):
                cols = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
                if len(cols) >= 2:
                    name = cols[0].lower()
                    val = cols[1]
                    rates[name] = val
        if not rates:
            for dt, dd in zip(soup.find_all("dt"), soup.find_all("dd")):
                rates[dt.get_text(strip=True).lower()] = dd.get_text(strip=True)

        if not rates:
            text = soup.get_text(" ", strip=True)
            import re
            matches = re.findall(r"([A-Za-z ]{3,20}) rate[s]?:\s*([0-9\.]+%?)", text, flags=re.IGNORECASE)
            for name, val in matches:
                rates[name.strip().lower()] = val

        if not rates:
            return {"source": url, "rates": fallback["rates"]}

        return {"source": url, "rates": rates}
    except Exception as exc:
        logger.exception("Error parsing page %s: %s", url, exc)
        return fallback
    