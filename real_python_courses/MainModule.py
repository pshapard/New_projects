import sys

def func1(*args):

    print(args[0])
    print(args[1])
    print(args[2])
    print(args[3])


def loginSessions(*args):

	url = "https://%s/rest/login-sessions" % args[0]
	payload = "{\"userName\":\"%s\",\"password\":\"%s\"}" % (args[3], args[4])
	headers = {
		'x-api-version': args[2],
		'content-type': "application/json"
		}
	print(url, payload, headers,)
