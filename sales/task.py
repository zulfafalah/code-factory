from celery import shared_task

from .scraper_registry import SCRAPER_CLASS_REGISTRY


@shared_task
def run_scraper(order_id):
    from .models import SalesOrder

    order = SalesOrder.objects.get(order_id=order_id)
    service_name = order.service_name.item_name
    scraper_class = SCRAPER_CLASS_REGISTRY.get(service_name)

    if scraper_class:
        scraper = scraper_class(order)
        scraper.run()
    else:
        print(f"No scraper found for {service_name}")
