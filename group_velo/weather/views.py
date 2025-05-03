# from datetime import timedelta

# from celery.result import AsyncResult
# from django.contrib.auth.decorators import login_required
# from django.http import JsonResponse
# from django.shortcuts import get_object_or_404, render
# from django.utils import timezone
# from django.views.decorators.http import require_GET, require_POST

# from group_velo.events.models import EventOccurence

# from .models import WeatherForecastDay
# from .tasks import fetch_weather_data, process_upcoming_events_weather, refresh_event_weather


# def weather_page(request):
#     """
#     Render the main weather page with form to request weather data
#     """
#     return render(request, 'weather_app/weather_page.html')

# @require_GET
# def get_weather(request):
#     """
#     Start an asynchronous task to fetch weather data
#     """
#     location = request.GET.get('location')
#     zipcode = request.GET.get('zipcode')
#     forecast_date_str = request.GET.get('forecast_date')
#     force_refresh = request.GET.get('force_refresh', 'false').lower() == 'true'

#     # Make sure we have either location or zipcode
#     if not location and not zipcode:
#         return JsonResponse({
#             'error': 'Either location or zipcode must be provided'
#         }, status=400)

#     # Parse forecast date if provided
#     forecast_date = None
#     if forecast_date_str:
#         try:
#             forecast_date = timezone.datetime.strptime(forecast_date_str, '%Y-%m-%d').date()
#         except ValueError:
#             return JsonResponse({
#                 'error': 'Invalid forecast date format. Use YYYY-MM-DD.'
#             }, status=400)

#     # Check if we already have this data in our cache
#     if not force_refresh:
#         cached_data = WeatherForecastDay.get_cached_weather(
#             location=location,
#             zipcode=zipcode,
#             forecast_date=forecast_date
#         )
#         if cached_data:
#             # Return cached data immediately - no need for async task
#             return JsonResponse({
#                 'status': 'completed',
#                 'data': cached_data.to_dict(),
#                 'source': 'cache'
#             })

#     # Start the asynchronous task
#     task = fetch_weather_data.delay(location, zipcode,
#                                      forecast_date.isoformat() if forecast_date else None,
#                                      force_refresh)

#     # Return the task ID so the client can check for results
#     return JsonResponse({
#         'task_id': task.id,
#         'status': 'pending',
#         'message': f'Fetching weather data for {location or zipcode}',
#         'source': 'api'
#     })

# @require_GET
# def check_task_status(request):
#     """
#     Check the status of an asynchronous task
#     """
#     task_id = request.GET.get('task_id')

#     if not task_id:
#         return JsonResponse({'error': 'No task ID provided'}, status=400)

#     # Get the task result object
#     task_result = AsyncResult(task_id)

#     # Check if the task is ready
#     if task_result.ready():
#         result = task_result.result
#         if isinstance(result, dict) and 'error' in result:
#             return JsonResponse({
#                 'status': 'failed',
#                 'error': result['error']
#             }, status=500)
#         else:
#             return JsonResponse({
#                 'status': 'completed',
#                 'data': result
#             })
#     else:
#         return JsonResponse({
#             'status': 'pending',
#             'message': 'Task is still processing'
#         })

# @login_required
# def events_dashboard(request):
#     """
#     Display upcoming events with their weather forecasts
#     """
#     # Get date range
#     today = timezone.now().date()
#     end_date = today + timedelta(days=7)  # Show next 7 days
#     date_filter = request.GET.get('date')

#     if date_filter:
#         try:
#             filter_date = timezone.datetime.strptime(date_filter, '%Y-%m-%d').date()
#             events = Event.objects.filter(event_date=filter_date).order_by('start_time')
#         except ValueError:
#             events = Event.objects.filter(
#                 event_date__gte=today,
#                 event_date__lt=end_date
#             ).order_by('event_date', 'start_time')
#     else:
#         events = Event.objects.filter(
#             event_date__gte=today,
#             event_date__lt=end_date
#         ).order_by('event_date', 'start_time')

#     # Get unique dates for the date filter
#     unique_dates = Event.objects.filter(
#         event_date__gte=today,
#         event_date__lt=end_date
#     ).values_list('event_date', flat=True).distinct().order_by('event_date')

#     context = {
#         'events': events,
#         'unique_dates': unique_dates,
#         'selected_date': date_filter,
#     }

#     return render(request, 'weather_app/events_dashboard.html', context)

# @login_required
# @require_POST
# def update_events_weather(request):
#     """
#     Trigger background task to update weather data for all upcoming events
#     """
#     # Start the background task
#     task = process_upcoming_events_weather.delay()

#     return JsonResponse({
#         'task_id': task.id,
#         'status': 'started',
#         'message': 'Weather update process has been started'
#     })

# @login_required
# @require_POST
# def refresh_weather_for_event(request, event_id):
#     """
#     Refresh weather data for a specific event
#     """
#     event = get_object_or_404(Event, id=event_id)

#     # Start the background task
#     task = refresh_event_weather.delay(event_id)

#     return JsonResponse({
#         'task_id': task.id,
#         'status': 'started',
#         'message': f'Weather refresh for event "{event.title}" has been started'
#     }) cached_data:
#             # Return cached data immediately - no need for async task
#             return JsonResponse({
#                 'status': 'completed',
#                 'data': cached_data.to_dict(),
#                 'source': 'cache'
#             })

#     # Start the asynchronous task
#     task = fetch_weather_data.delay(location, zipcode, force_refresh)

#     # Return the task ID so the client can check for results
#     return JsonResponse({
#         'task_id': task.id,
#         'status': 'pending',
#         'message': f'Fetching weather data for {location}',
#         'source': 'api'
#     })

# @require_GET
# def check_task_status(request):
#     """
#     Check the status of an asynchronous task
#     """
#     task_id = request.GET.get('task_id')

#     if not task_id:
#         return JsonResponse({'error': 'No task ID provided'}, status=400)

#     # Get the task result object
#     task_result = AsyncResult(task_id)

#     # Check if the task is ready
#     if task_result.ready():
#         result = task_result.result
#         if isinstance(result, dict) and 'error' in result:
#             return JsonResponse({
#                 'status': 'failed',
#                 'error': result['error']
#             }, status=500)
#         else:
#             return JsonResponse({
#                 'status': 'completed',
#                 'data': result
#             })
#     else:
#         return JsonResponse({
#             'status': 'pending',
#             'message': 'Task is still processing'
#         })
