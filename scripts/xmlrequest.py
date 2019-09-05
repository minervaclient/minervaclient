import requests
import xml

request_headers = {
    'Origin':'https://horizon.mcgill.ca',
    'Upgrade-Insecure-Requests':'1',
    'DNT':'1',
    'Content-Type':'application/x-www-form-urlencoded',
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
    'Sec-Fetch-Mode':'navigate',
    'Sec-Fetch-User':'?1',
    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',

}
data = {
    'attr_in':'',
    'coll_in':'%',
    'cred_from_in':'',
    'cred_to_in':'',
    'crse_end_in':'220',
    'crse_strt_in':'214',
    'dept_in':'%',
    'divs_in':'%',
    'last_updated':'',
    'levl_in':'',
    'schd_in':'',
    'subj_in':'\tANAT\t',
    'term_in':'201909',
    'title_in':'%%',
}

r = requests.post('https://horizon.mcgill.ca/pban1/bwckctlg.xml',data=data,headers=request_headers)