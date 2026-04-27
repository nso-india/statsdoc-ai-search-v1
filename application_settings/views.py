from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Config
from .serializers import ConfigSerializer, NamespaceConfigSerializer


class IsStaffPermission:
    """Custom permission to check if user is staff."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff


class ConfigListView(APIView):
    """List all configuration namespaces (staff only)."""
    permission_classes = [IsAuthenticated, IsStaffPermission]

    def get(self, request):
        configs = Config.objects.all()
        serializer = ConfigSerializer(configs, many=True)
        return Response(serializer.data)


class NamespaceConfigView(APIView):
    """Get or update configuration for a specific namespace (staff only)."""
    permission_classes = [IsAuthenticated, IsStaffPermission]

    def get_default_values(self, namespace):
        """Get default values for known namespaces."""
        defaults = {
            'chat': {
                'file_size_limit_mb': 20,
                'questions_per_chat': 10,
                'chats_per_day': 50
            }
        }
        return defaults.get(namespace, {})

    def get(self, request, namespace):
        # Get configuration with defaults if it doesn't exist
        default_values = self.get_default_values(namespace)
        data = Config.get_namespace(namespace, default_values)

        return Response({
            "namespace": namespace,
            "data": data
        })

    def put(self, request, namespace):
        serializer = NamespaceConfigSerializer(
            data=request.data,
            context={'namespace': namespace}
        )
        if serializer.is_valid():
            config_data = request.data.get('config_data', {})
            updated_data = Config.update_namespace(namespace, config_data)
            return Response({
                "namespace": namespace,
                "data": updated_data,
                "message": f"Configuration for '{namespace}' updated successfully."
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NamespaceResetView(APIView):
    """Reset namespace(s) to default values (staff only)."""
    permission_classes = [IsAuthenticated, IsStaffPermission]

    def get_default_values(self, namespace=None):
        """Get default values for known namespaces."""
        defaults = {
            'chat': {
                'file_size_limit_mb': 20,
                'questions_per_chat': 10,
                'chats_per_day': 50
            }
        }

        if namespace:
            return defaults.get(namespace)
        return defaults

    def post(self, request, namespace=None):
        if namespace:
            # Reset specific namespace
            default_values = self.get_default_values(namespace)

            if default_values is None:
                return Response(
                    {"error": f"No default configuration found for namespace '{namespace}'."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            reset_data = Config.set_namespace(namespace, default_values)
            return Response({
                "namespace": namespace,
                "data": reset_data,
                "message": f"Configuration for '{namespace}' reset to defaults."
            })
        else:
            # Reset all namespaces
            all_defaults = self.get_default_values()
            reset_results = {}

            if all_defaults:
                for ns, default_data in all_defaults.items():
                    if isinstance(default_data, dict):
                        reset_data = Config.set_namespace(ns, default_data)
                        reset_results[ns] = reset_data

                return Response({
                    "message": f"All configurations reset to defaults. Reset {len(reset_results)} namespaces.",
                    "reset_namespaces": list(reset_results.keys()),
                    "data": reset_results
                })
            else:
                return Response({
                    "message": "No default configurations found to reset.",
                    "reset_namespaces": [],
                    "data": {}
                })
