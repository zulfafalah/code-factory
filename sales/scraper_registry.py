SCRAPER_CLASS_REGISTRY = {}


def register_scraper_class(service_key):
    def wrapper(cls):
        SCRAPER_CLASS_REGISTRY[service_key] = cls
        return cls

    return wrapper
