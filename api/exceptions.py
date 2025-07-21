from rest_framework.views import exception_handler
from django.db.utils import IntegrityError
from django.db.models import ProtectedError
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Now, add the handling for IntegrityError and ProtectedError
    if isinstance(exc, (IntegrityError, ProtectedError)) and response is None:
        # You can customize this message further based on the exception details if needed
        # For example, by inspecting exc.args to see which constraint was violated.
        custom_message = "操作失败：该项目已被其他数据关联，无法删除。请先解除所有关联后再试。"
        
        response = Response(
            {"detail": custom_message},
            status=status.HTTP_400_BAD_REQUEST
        )

    return response
