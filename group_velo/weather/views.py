from http import HTTPStatus

from celery.result import AsyncResult
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET


class HttpResponseNoContent(HttpResponse):
    status_code = HTTPStatus.NO_CONTENT


@require_GET
def check_task_status(request, task_id):
    """
    Check the status of an asynchronous task
    """

    if not task_id:
        return JsonResponse({"error": "No task ID provided"}, status=400)

    # Get the task result object
    task_result = AsyncResult(task_id)

    # Check if the task is ready
    if task_result.ready():
        result = task_result.result
        if isinstance(result, dict) and "error" in result:
            # error
            return HttpResponse("")
        else:
            # complete
            response = render_to_string(
                "events/ride_card/weather/_load_day_weather_on_ready.html",
                {
                    "zip_code": request.GET.get("zip_code"),
                    "event_date": request.GET.get("event_date"),
                    "task_id": task_id,
                    "ride_id": request.GET.get("ride_id"),
                },
            )
            return HttpResponse(response)
    else:
        # pending
        HttpResponseNoContent()
