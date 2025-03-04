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
        cap_income = req.params["income"]
        cap_race = req.params["race"]
        cap_homeownership = req.params["homeownership"]
        cap_education = req.params["education"]
        cap_urban = req.params["urban"]
        cap_redistribution = req.params["redistribution"]
        cap_id = req.params["id"]
        py_session = req.params["session"] + ".RData"

        py_exact_var = ["race", "homeownership"]
        py_exact_val = [cap_race, cap_homeownership]

        py_covar_var = ["income", "education", "urban", "redistribution"]
        py_covar_val = [cap_income, cap_education, cap_urban, cap_redistribution]

        robjects.r('''
                       f <- function(id, exact_var, exact_val, covar_var, covar_val, session) {

                        # the session has not been seen before, then the corresponding file doesn't exist
                        # and this must be the first assignment
                        if(!file.exists(session)) {
                            seqout <- seqblock(query = FALSE
                                            , id.vars = "ID"
                                            , id.vals = id
                                            , n.tr = 2
                                            , tr.names = c("nonprofit", "for-profit")
                                            , assg.prob = c(1/2, 1/2)
                                            , exact.vars = exact_var
                                            , exact.vals = exact_val
                                            , covar.vars = covar_var
                                            , covar.vals = covar_val
                                            , file.name = session)
                        }
                        else {
                            seqout <- seqblock(query = FALSE
                                            , object = session
                                            , id.vals = id
                                            , n.tr = 2
                                            , tr.names = c("nonprofit", "for-profit")
                                            , assg.prob = c(1/2, 1/2)
                                            , exact.vals = exact_val
                                            , covar.vals = covar_val
                                            , file.name = session)
                        }
                        seqout$x[seqout$x['ID'] == id , "Tr"]
                        }
                       ''')

        r_f = robjects.r['f']
        out = r_f(cap_id, py_exact_var, py_exact_val, py_covar_var, py_covar_val, py_session)
        resp.body = 'Treatment=' + str(out[0])

# falcon.API instances are callable WSGI apps
app = falcon.API()

app.add_route('/test', DiagResource())

# this code is appropriated & modified from https://github.com/diagdavenport/rpy2-heroku/blob/master/diag.py
