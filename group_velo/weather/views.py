from celery.result import AsyncResult
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def check_task_status(request, task_id):
    """
    Check the status of an asynchronous task
    """

    if not task_id:
        return JsonResponse({"error": "No task ID provided"}, status=400)

    # Get the task result object
    task_result = AsyncResult(task_id)

    print(task_result)

    # Check if the task is ready
    if task_result.ready():
        result = task_result.result
        if isinstance(result, dict) and "error" in result:
            return JsonResponse({"status": "failed", "error": result["error"]}, status=500)
        else:
            return JsonResponse({"status": "completed", "data": result})
    else:
        return JsonResponse({"status": "pending", "message": "Task is still processing"})
