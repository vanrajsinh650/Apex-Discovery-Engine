# Apex Discovery Engine 🚀

A high-performance, autonomous web scraping agent designed to discover, extract, and organize lead data (PGs, Hostels, Businesses) from the web.

## 🌟 Key Features

- **Multi-Engine Discovery**: Intelligently switches between Brave, Bing, DuckDuckGo, and Google Maps to find targets.
- **Deep Crawling**: Automatically navigates to "Contact Us" pages and detail views to uncover hidden numbers.
- **Google Maps dedicated Scraper**: Bypasses website blocks by extracting direct phone numbers from Google Maps side panels.
- **Resumable State**: Remembers where it left off (pagination handling).
- **Smart Deduplication**: Uses advanced heuristics to remove duplicate entries while preserving unique leads.
- **Excel Export**: Delivers clean, structured data ready for use.

## 📂 Project Structure

The project follows a modular, professional architecture:

```
/
├── main.py                 # Entry point (Unified CLI & Interactive Mode)
├── src/
│   ├── cli.py              # CLI Command Definitions
│   ├── core/               # Core Utilities & Configuration
│   │   ├── config.py
│   │   └── utils.py
│   ├── scrapers/           # scraping Logic Modules
│   │   ├── search.py       # Search Engine Connectors (Brave, Bing, etc.)
│   │   ├── listing.py      # Website Extraction Logic (HTML Parsing)
│   │   └── maps.py         # Google Maps Side-Panel Scraper
│   └── exporters/          # Data Export Modules
│       └── excel.py        # Excel Export Logic
├── scripts/                # Helper & Debug Scripts
│   ├── analyze_yield.py
│   └── ...
└── data/                   # Data Storage (JSON/Excel)
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Playwright

### Installation

```bash
pip install -r requirements.txt
playwright install chromium
```

### Usage

**1. Interactive Mode (Recommended)**

```bash
python main.py
```

Follow the on-screen prompts to discover and extract data.

**2. CLI Commands**

- **Discover URLs**:

  ```bash
  python main.py discover --query "PG in Ahmedabad" --limit 50
  ```

- **Maps Scraper (High Yield)**:

  ```bash
  python main.py maps --query "PG in Ahmedabad" --limit 100
  ```

- **Extract Data from URLs**:

  ```bash
  python main.py extract
  ```

- **Export to Excel**:
  ```bash
  python main.py export
  ```

## 🛠 Advanced Configuration

Configuration settings (User Agents, Timeouts) can be found in `src/core/config.py`.

## 📝 License

Proprietary Software.
