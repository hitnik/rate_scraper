from app.scraper import RateScraper

def main():
    rs = RateScraper()
    data = rs.scrape_rates()
    RateScraper.put_to_db(data)


if __name__ == "__main__":
    main()