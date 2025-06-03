import json
from pathlib import Path

from django.contrib import messages
from django.http import Http404
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import YouTubeMP3


def download_list(request):
    """View to display all YouTube MP3 downloads"""
    downloads = YouTubeMP3.objects.all().order_by("-created_at")
    return render(request, "yttoolkit/download_list.html", {"downloads": downloads})


def start_download(request):
    """View to start a new YouTube MP3 download"""
    if request.method == "POST":
        video_url = request.POST.get("video_url")

        if not video_url:
            messages.error(request, "Please provide a YouTube URL")
            return redirect("yttoolkit:download_list")

        try:
            # Create or get existing YouTubeMP3 instance
            youtube_mp3, created = YouTubeMP3.objects.get_or_create(
                video_url=video_url, defaults={"download_status": "pending"}
            )

            if created:
                # Start the download task
                task = youtube_mp3.start_download()
                messages.success(
                    request, f"Download started successfully! Task ID: {task.id}"
                )
            else:
                if youtube_mp3.download_status in ["completed", "in_progress"]:
                    messages.warning(
                        request,
                        "This video is already downloaded or currently downloading",
                    )
                else:
                    # Retry failed download
                    youtube_mp3.download_status = "pending"
                    youtube_mp3.error_message = None
                    youtube_mp3.save()

                    task = youtube_mp3.start_download()
                    messages.success(request, f"Download restarted! Task ID: {task.id}")

        except ValueError as e:
            messages.error(request, f"Error: {e}")
        except Exception as e:
            messages.error(request, f"Unexpected error: {e}")

    return redirect("yttoolkit:download_list")


@csrf_exempt
@require_http_methods(["POST"])
def api_start_download(request):
    """API endpoint to start a YouTube MP3 download"""
    try:
        data = json.loads(request.body)
        video_url = data.get("video_url")

        if not video_url:
            return JsonResponse({"error": "video_url is required"}, status=400)

        # Create or get existing YouTubeMP3 instance
        youtube_mp3, created = YouTubeMP3.objects.get_or_create(
            video_url=video_url, defaults={"download_status": "pending"}
        )

        if created or youtube_mp3.download_status in ["pending", "failed"]:
            if not created:
                # Reset for retry
                youtube_mp3.download_status = "pending"
                youtube_mp3.error_message = None
                youtube_mp3.save()

            # Start the download task
            task = youtube_mp3.start_download()

            return JsonResponse(
                {
                    "success": True,
                    "message": "Download started successfully",
                    "task_id": task.id,
                    "download_id": youtube_mp3.id,
                    "status": youtube_mp3.download_status,
                }
            )
        else:
            return JsonResponse(
                {
                    "success": False,
                    "message": f"Download already exists with status: {youtube_mp3.download_status}",
                    "download_id": youtube_mp3.id,
                    "status": youtube_mp3.download_status,
                }
            )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)


def api_download_status(request, download_id):
    """API endpoint to check download status"""
    try:
        youtube_mp3 = get_object_or_404(YouTubeMP3, id=download_id)

        response_data = {
            "id": youtube_mp3.id,
            "video_url": youtube_mp3.video_url,
            "video_title": youtube_mp3.video_title,
            "download_status": youtube_mp3.download_status,
            "file_name": youtube_mp3.file_name,
            "file_size_mb": youtube_mp3.file_size_mb,
            "error_message": youtube_mp3.error_message,
            "created_at": youtube_mp3.created_at.isoformat(),
            "updated_at": youtube_mp3.updated_at.isoformat(),
            "is_downloadable": youtube_mp3.is_downloadable,
            "download_url": youtube_mp3.get_download_url(),
        }

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def download_file(request, download_id):
    """View to download the MP3 file"""
    youtube_mp3 = get_object_or_404(YouTubeMP3, id=download_id)

    if not youtube_mp3.is_downloadable:
        file_not_found_msg = "File not found or not ready for download"
        raise Http404(file_not_found_msg)

    file_path = Path(youtube_mp3.file_path)

    if not file_path.exists():
        file_not_found_server_msg = "File not found on server"
        raise Http404(file_not_found_server_msg)

    # Open and serve the file
    with file_path.open("rb") as f:
        response = HttpResponse(f.read(), content_type="audio/mpeg")
        content_disposition = f'attachment; filename="{youtube_mp3.file_name}"'
        response["Content-Disposition"] = content_disposition
        response["Content-Length"] = youtube_mp3.file_size
        return response
