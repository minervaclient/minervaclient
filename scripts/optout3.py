from minervaclient3 import minerva_common,opt_out
opt_out = 'bztkopto.pm_opt_out_processing'

if __name__=='__main__':
    mnvc = minerva_common.MinervaCommon()
    mnvc.initial_login(inConsole=True)
    opt_out.opt_out(mnvc)