"""Order service for fetching and processing OMS order data."""

import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import current_app
from app.utils.cache import cache

logger = logging.getLogger(__name__)


class OrderService:
    """Handles order fetching, detail retrieval, and analytics processing."""

    def __init__(self, base_url, auth_service):
        self.base_url = base_url.rstrip('/')
        self.auth_service = auth_service

    def _get_headers(self):
        """Build authorization headers with cached token."""
        token = self.auth_service.get_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def fetch_orders(self, from_date, to_date):
        """Fetch orders from the OMS API for a date range."""
        import requests
        import json

        # The API expects ISO format with timezone
        if len(from_date) == 10:
            from_date = f"{from_date}T00:00:00+05:30"
        if len(to_date) == 10:
            to_date = f"{to_date}T23:59:59+05:30"

        cache_key = f'orders_{from_date}_{to_date}'
        cached = cache.get(cache_key)
        if cached:
            logger.debug('Returning cached orders.')
            return cached

        logger.info(f'Fetching orders from {from_date} to {to_date}')

        try:
            payload = json.dumps({'fromDate': from_date, 'toDate': to_date})
            response = requests.post(
                f'{self.base_url}/services/rest/v1/oms/saleOrder/search',
                headers=self._get_headers(),
                data=payload,
                timeout=60
            )

            response.raise_for_status()
            data = response.json()
            orders = data.get('elements', data.get('saleOrderDTOs', []))

            if not isinstance(orders, list):
                orders = []

            cache.set(cache_key, orders, ttl=current_app.config.get('CACHE_TTL', 300))
            logger.info(f'Fetched {len(orders)} orders.')
            return orders

        except requests.exceptions.RequestException as e:
            error_text = getattr(e.response, 'text', 'No response text')
            logger.error(f'Error fetching orders: {e} - Response: {error_text}')
            raise

    def fetch_order_detail(self, order_code):
        """Fetch detailed information for a single order."""
        import requests
        import json

        cache_key = f'order_detail_{order_code}'
        cached = cache.get(cache_key)
        if cached:
            return cached

        logger.info(f'Fetching order detail for {order_code}')

        try:
            payload = json.dumps({'code': order_code})
            response = requests.post(
                f'{self.base_url}/services/rest/v1/oms/saleorder/get',
                headers=self._get_headers(),
                data=payload,
                timeout=30
            )
            response.raise_for_status()

            detail = response.json()
            cache.set(cache_key, detail, ttl=current_app.config.get('CACHE_TTL', 300))
            return detail

        except requests.exceptions.RequestException as e:
            logger.error(f'Error fetching order detail for {order_code}: {e}')
            raise

    def fetch_order_details_batch(self, order_codes, on_progress=None):
        """Fetch details for multiple orders in parallel."""
        max_workers = current_app.config.get('MAX_WORKERS', 5)
        details = {}
        total = len(order_codes)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.fetch_order_detail, code): code
                for code in order_codes
            }

            for i, future in enumerate(as_completed(futures), 1):
                code = futures[future]
                try:
                    result = future.result()
                    details[code] = result
                except Exception as e:
                    logger.error(f'Failed to fetch detail for {code}: {e}')
                    details[code] = {'code': code, 'error': str(e)}

                if on_progress:
                    on_progress(i, total)

        return details

    def process_orders(self, orders, on_progress=None):
        """Process raw orders into analytics data and sync to persistent database."""
        import typing
        from datetime import datetime
        from app import db
        from app.models.order import Order
        
        prefixes: typing.List[str] = current_app.config.get('STORE_PREFIXES', ['PA', 'PI', 'MA', 'BL'])  # type: ignore

        store_orders: typing.Dict[str, list] = {prefix: [] for prefix in prefixes}
        all_filtered: list = []

        # 1. Filter orders
        for order in orders:
            code = order.get('code', order.get('displayOrderCode', ''))
            for prefix in prefixes:
                if code.upper().startswith(prefix):
                    store_orders[prefix].append(order)
                    all_filtered.append(order)
                    break
        
        # 2. Extract needed codes
        order_codes: typing.List[str] = [str(o.get('code', o.get('displayOrderCode', ''))) for o in all_filtered]
        
        # 3. Fetch details in batch (required for packaging/dispatch time)
        details_map: typing.Dict[str, dict] = self.fetch_order_details_batch(order_codes, on_progress)

        # Calculate analytics & Sync DB
        total_orders: int = len(all_filtered)
        awb_count: int = 0
        dispatch_times: typing.List[float] = []
        within_24h: int = 0
        beyond_24h: int = 0
        store_within_24h: typing.Dict[str, int] = {p: 0 for p in prefixes}
        store_beyond_24h: typing.Dict[str, int] = {p: 0 for p in prefixes}

        for order in all_filtered:
            code = str(order.get('code', order.get('displayOrderCode', '')))
            created_ms = order.get('created', 0)
            order_time_hrs = float(created_ms) / 3600000.0 if created_ms else 0.0
            
            detail = details_map.get(code, {})
            sale_order_dto = detail.get('saleOrderDTO', {})
            packages = sale_order_dto.get('shippingPackages', [])
            
            prefix_match = ''
            for prefix in prefixes:
                if code.upper().startswith(prefix):
                    prefix_match = str(prefix)
                    break
                    
            if not prefix_match:
                continue

            has_awb = False
            final_dispatch_ms = None
            final_diff_hours = None
            awb = ''
            
            for pkg in packages:
                if not awb:
                    awb = pkg.get('trackingNumber', pkg.get('awbNumber', ''))
                if awb:
                    has_awb = True
                
                dispatch_ms = pkg.get('dispatched', pkg.get('dispatchedOn'))
                if dispatch_ms and created_ms:
                    if final_dispatch_ms is None or dispatch_ms > final_dispatch_ms:
                        final_dispatch_ms = dispatch_ms
                        
                    dispatch_time_hrs = float(dispatch_ms) / 3600000.0
                    diff_hours = float(dispatch_time_hrs - order_time_hrs)
                    final_diff_hours = diff_hours
                    
                    if diff_hours > 0:
                        dispatch_times.append(diff_hours)
                        if diff_hours <= 24:
                            within_24h = int(within_24h) + 1
                            store_within_24h[prefix_match] = int(store_within_24h.get(prefix_match, 0)) + 1
                        else:
                            beyond_24h = int(beyond_24h) + 1
                            store_beyond_24h[prefix_match] = int(store_beyond_24h.get(prefix_match, 0)) + 1
                            
            if has_awb:
                awb_count = int(awb_count) + 1
                
            # Database Sync
            existing = Order.query.filter_by(order_code=code).first()
            created_dt = datetime.fromtimestamp(created_ms/1000.0) if created_ms else None
            dispatch_dt = datetime.fromtimestamp(final_dispatch_ms/1000.0) if final_dispatch_ms else None
            
            if not existing:
                new_order = Order(
                    order_code=code,
                    store_type=prefix_match,
                    created_time=created_dt,
                    dispatch_time=dispatch_dt,
                    shipping_hours=final_diff_hours,
                    awb=awb,
                    raw_data=order
                )
                db.session.add(new_order)
            else:
                existing.dispatch_time = dispatch_dt
                if final_diff_hours is not None:
                    existing.shipping_hours = final_diff_hours
                if awb:
                    existing.awb = awb
                existing.raw_data = order
                
        db.session.commit()

        avg_dispatch = 0.0
        if dispatch_times:
            avg_dispatch = round(float(sum(dispatch_times) / len(dispatch_times)), 1)
        
        total_dispatches = int(len(dispatch_times))
        within_24h_rate = 0
        if total_dispatches > 0:
            within_24h_rate = int(round(float(within_24h) / float(total_dispatches) * 100.0))

        return {
            'summary': {
                'total_orders': total_orders,
                'awb_count': awb_count,
                'avg_dispatch_time': avg_dispatch,
                'within_24h_rate': within_24h_rate
            }
        }

    def get_analytics_from_db(self, from_date, to_date):
        """Read persistently stored orders and calculate analytics dynamically, skipping external systems."""
        from datetime import datetime
        from app.models.order import Order
        import typing
        
        prefixes: typing.List[str] = current_app.config.get('STORE_PREFIXES', ['PA', 'PI', 'MA', 'BL'])  # type: ignore

        if len(from_date) == 10:
            from_dt = datetime.strptime(f"{from_date}T00:00:00", "%Y-%m-%dT%H:%M:%S")
        else:
            from_dt = datetime.strptime(from_date[:19], "%Y-%m-%dT%H:%M:%S")
            
        if len(to_date) == 10:
            to_dt = datetime.strptime(f"{to_date}T23:59:59", "%Y-%m-%dT%H:%M:%S")
        else:
            to_dt = datetime.strptime(to_date[:19], "%Y-%m-%dT%H:%M:%S")

        query = Order.query.filter(Order.created_time >= from_dt, Order.created_time <= to_dt)
        all_orders = query.all()

        total_orders = len(all_orders)
        awb_count = 0
        dispatch_times = []
        within_24h = 0
        beyond_24h = 0
        
        store_orders = {p: 0 for p in prefixes}
        store_within_24h = {p: 0 for p in prefixes}
        store_beyond_24h = {p: 0 for p in prefixes}
        orders_by_date = {}
        table_data = []

        for o in all_orders:
            store_p = str(o.store_type) if o.store_type else 'Unknown'
            if store_p in store_orders:
                store_orders[store_p] += 1
            
            if o.awb:
                awb_count += 1
                
            if o.shipping_hours is not None and o.shipping_hours > 0:
                dispatch_times.append(o.shipping_hours)
                if o.shipping_hours <= 24:
                    within_24h += 1
                    if store_p in store_within_24h:
                        store_within_24h[store_p] += 1
                else:
                    beyond_24h += 1
                    if store_p in store_beyond_24h:
                        store_beyond_24h[store_p] += 1
            
            if o.created_time:
                date_key = o.created_time.strftime('%Y-%m-%d')
                orders_by_date[date_key] = orders_by_date.get(date_key, 0) + 1
                
            raw = o.raw_data or {}
            table_data.append({
                'code': o.order_code,
                'store_type': store_p,
                'awb': o.awb or '',
                'dispatch_time': round(o.shipping_hours, 1) if o.shipping_hours is not None else None,
                'status': raw.get('status', raw.get('statusCode', 'Unknown'))
            })

        avg_dispatch = 0.0
        if len(dispatch_times) > 0:
            avg_dispatch = float(round(sum(dispatch_times) / len(dispatch_times), 1))
            
        within_24h_rate = 0
        if len(dispatch_times) > 0:
            within_24h_rate = int(round((float(within_24h) / float(len(dispatch_times))) * 100.0))

        return {
            'summary': {
                'total_orders': total_orders,
                'awb_count': awb_count,
                'avg_dispatch_time': avg_dispatch,
                'within_24h_rate': within_24h_rate
            },
            'store_distribution': store_orders,
            'dispatch_analysis': {
                'within_24h': within_24h,
                'beyond_24h': beyond_24h,
                'by_store': {
                    'within': store_within_24h,
                    'beyond': store_beyond_24h
                }
            },
            'orders_over_time': dict(sorted(orders_by_date.items())),
            'table_data': table_data
        }
