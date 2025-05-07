from celery.result import AsyncResult
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET

# from django.template.loader import render_to_string


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
        print(task_result.result)
        result = task_result.result
        if isinstance(result, dict) and "error" in result:
            # error
            return HttpResponse(status=500)
        else:
            # complete
            return HttpResponse(status=200)
    else:
        # pending
        return HttpResponse(status=202)
