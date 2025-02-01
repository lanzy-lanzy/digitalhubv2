class HtmxMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.htmx = False
        if 'HX-Request' in request.headers:
            request.htmx = True
        return self.get_response(request)
