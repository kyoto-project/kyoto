import termformat


def is_valid_info(request):
  if isinstance(request, tuple):
    if len(request) == 3:
      if request[0] == ":info":
        if request[1] in (":stream", ":callback", ":cache"):
          if isinstance(request[2], list):
            return True
  return False

def is_valid_request(request):
  if isinstance(request, tuple):
    if len(request) == 4:
      if request[0] in (":call", ":cast"):
        if termformat.is_atom(request[1]):
          if termformat.is_atom(request[2]):
            if isinstance(request[3], list):
              return True
  return False

def is_valid_error_response(response):
  if isinstance(response, tuple):
    if len(response) == 2:
      if response[0] == ":error":
        if isinstance(response[1], tuple):
          if len(response[1]) == 5:
            if response[1][0] in (":protocol", ":server", ":user", ":proxy"):
              if isinstance(response[1][1], int):
                if isinstance(response[1][2], str):
                  if isinstance(response[1][3], str):
                    if isinstance(response[1][4], list):
                      return True
  return False
