"""PRE-002 — public liveness + readiness."""

from __future__ import annotations

from django.db import connection
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    """GET /api/v1/health/ — process liveness (DB yok)."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok", "service": "kuyumbank", "api": "v1"})


class ReadyView(APIView):
    """GET /api/v1/ready/ — DB bağlantı readiness (load balancer / deploy gate)."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            connection.ensure_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:
            return Response(
                {
                    "status": "not_ready",
                    "service": "kuyumbank",
                    "api": "v1",
                    "checks": {"database": "error"},
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(
            {
                "status": "ready",
                "service": "kuyumbank",
                "api": "v1",
                "checks": {"database": "ok"},
            }
        )
