# This file will contain base calles which out custom exception classes will inherit
# This base classes will be inherited from FaseApi's core exception class

# Reason to take this approach is that if we want to apply some common thing in all custom exception class
# Then we will be easily able to do
class BaseException(Exception):
    pass