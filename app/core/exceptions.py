
class ApplicationError(Exception):

    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.message = message
        self.code = code


class LLMProviderError(ApplicationError):
    pass


class ServiceTimeoutError(ApplicationError):
    pass


# ---------------------------- v0 ---------------------------
# class ApplicationError(Exception):
#     def __init__(
#         self,
#         message: str,
#         code: str = "APPLICATION_ERROR"
#     ):
#         self.message = message
#         self.code = code
#         super().__init__(message)


# class LLMProviderError(ApplicationError):
#     def __init__(self, message: str):
#         super().__init__(
#             message,
#             code="LLM_PROVIDER_ERROR"
#         )


# class ServiceTimeoutError(ApplicationError):
#     def __init__(self, message: str):
#         super().__init__(
#             message,
#             code="SERVICE_TIMEOUT"
#         )