from MainModule import func1, loginSessions


ip = '15.186.9.21'
api = '1400'
username = 'admin'
password = 'passwd'
auth = 'MjI1OTIxNzcwNDYzBSN80kMvckTpa6srNMV0qnrpqR8Axd7M'
server_hw_uri = '/rest/server-hardware/39313738-3034-584D-5139-313530313244'


func1(ip, api, auth, server_hw_uri)

loginSessions(ip, auth, api, username, password)
