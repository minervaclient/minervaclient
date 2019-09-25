import minervaclient3
from minervaclient3 import minerva_common
opt_out = 'bztkopto.pm_opt_out_processing'

def _save_page(req,name):
    with open(name,'wb') as f:
        f.write(req.content)

mnvc = minerva_common.MinervaCommon()
mnvc.initial_login(inConsole=False,reLogin=False)
mnvc._minerva_login_request()
r = mnvc._minerva_get(opt_out)
p = mnvc.minerva_parser(r.content)
l = p.select('a')
link_text = '/pban1/bztkopto.pm_agree_opt_out?'
nl = [item for item in l if 'href' in item.attrs and link_text in item.attrs['href'] ]
partial_fail = False
for item in nl:
    try:
        r1 = mnvc._minerva_get(item.attrs['href'][7:])
        p1 = mnvc.minerva_parser(r1.content)
        l1 = [item for item in  p1.select('form') if 'action' in item.attrs and 'bztkopto.pm_confirm_opt_out' in item.attrs['action']]
        data = { i.attrs['name']:i.attrs['value'] for i in l1[0] if hasattr(i,'attrs') and 'name' in i.attrs and 'value' in i.attrs}
        # print(p1.select('h2'))
        name = p1.select('h2')[1].text.strip()
        question = 'Do you wish to opt out of "{}"? [y]/n default(y) : '.format(name)
        # print(question) # DEBUG
        answer = (input(question)).lower() != 'n'
        if answer:
            print('opting out of "{}"'.format(name))
            mnvc._minerva_post('bztkopto.pm_confirm_opt_out',data)
    except KeyboardInterrupt:
        print("Exited opt-out program")
        break
    except:
        print("Couldn't parse an opt-out page")
        partial_fail = True

print('One or more opt-outs failed, and may be performed manually at https://horizon.mcgill.ca/pban1/bztkopto.pm_opt_out_processing')