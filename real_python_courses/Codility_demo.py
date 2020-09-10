

S = "CBACD"

#S = "CABABD"

#S = "ACBDACBD"

#The string can be transformed by removing letter A together with adjacent letter
#B, or by removing letter C with adjascent letter D

string = 'CABBACBDAC'
def solution(string):
    string_list = ['AB','BA','CD','DC']
    for element in string_list:
        if element in string:
            string = string.replace(element, "")
            string = string.strip(' ')
    return string

solution(string)
