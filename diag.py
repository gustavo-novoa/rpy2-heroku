import falcon
import rpy2.robjects.packages as rpackages
import rpy2.robjects as robjects
import sys

# import R's utility package
utils = rpackages.importr('utils')

# select a mirror for R packages
utils.chooseCRANmirror(ind=1) # select the first mirror in the list

# Finally, import BlockTools
bt = rpackages.importr('blockTools')

# Falcon follows the REST architectural style, meaning (among
# other things) that you think in terms of resources and state
# transitions, which map to HTTP verbs.
class DiagResource(object):
    def on_get(self, req, resp):
        """Handles GET requests"""
        resp.status = falcon.HTTP_200  # This is the default status
        
        # capture each of the blocking vars
        cap_iso = req.params["isolationism"]
        cap_id = req.params["id"]
        py_session = req.params["session"] + ".RData"
        
        py_exact_var = ["isolationism"]
        py_exact_val = [cap_iso]
        
        if (len(req.params["isolationism"]) == 1):
            robjects.r('''
                           f <- function(id, exact_var, exact_val, session) {
                            
                            # the session has not been seen before, then the corresponding file doesn't exist
                            # and this must be the first assignment
                            if(!file.exists(session)) {
                                seqout <- seqblock(query = FALSE
                                                , id.vars = "ID"
                                                , id.vals = id
                                                , n.tr = 5
                                                , tr.names = c("control", "0shaming", "0silence", "1shaming", "2shaming") 
                                                , assg.prob = c(1/5, 1/5, 1/5, 1/5, 1/5)
                                                , exact.vars = exact_var
                                                , exact.vals = exact_val
                                                , seed = 19930531
                                                , file.name = session)
                            }
                            else {
                                seqout <- seqblock(query = FALSE
                                                , object = session
                                                , id.vals = id
                                                , n.tr = 5
                                                , tr.names = c("control", "0shaming", "0silence", "1shaming", "2shaming")
                                                , assg.prob = c(1/5, 1/5, 1/5, 1/5, 1/5)
                                                #, assg.prob.method = "ktimes"
                                                #, assg.prob.kfac = 2
                                                #, distance = "mahalanobis"
                                                , exact.vals = exact_val
                                                , seed = 19930531
                                                , file.name = session)
                            }
                            seqout$x[seqout$x['ID'] == id , "Tr"]
                            }
                           ''')

            r_f = robjects.r['f']
            out = r_f(cap_id, py_exact_var, py_exact_val, py_session)
            resp.body = 'Treatment=' + str(out[0])
        else:
            resp.body = 'Treatment=' + "error: isolationism=" + req.params["isolationism"]
        
# falcon.API instances are callable WSGI apps
app = falcon.API()

app.add_route('/test', DiagResource())
