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
class Resource(object):
    def on_get(self, req, resp):
        """Handles GET requests"""
        resp.status = falcon.HTTP_200  # This is the default status
        
        # capture each of the blocking vars
        cap_prog = req.params["pretest"]
        cap_id = req.params["id"]
        py_session = req.params["session"] + ".RData"
        
        py_exact_var = ["pretest"]
        py_exact_val = [cap_prog]
        
        if (len(req.params["pretest"]) != 0):
            try:
                robjects.r('''
                           f <- function(id, exact_var, exact_val, session) {
                            
                            # the session has not been seen before, then the corresponding file doesn't exist
                            # and this must be the first assignment
                            if(!file.exists(session)) {
                                seqout <- seqblock(query = FALSE
                                                , id.vars = "ID"
                                                , id.vals = id
                                                , n.tr = 3
                                                , tr.names = c("control", "lossprotect", "lossclimate") 
                                                , assg.prob = c(1/3, 1/3, 1/3)
                                                , assg.prob.stat = "trimmean"
                                                , trim = 0.01
                                                , assg.prob.method = "ktimes"
                                                , exact.vars = exact_var
                                                , exact.vals = exact_val
                                                , seed = 815
                                                , seed.dist = 19930531
                                                , file.name = session)
                            }
                            else {
                                seqout <- seqblock(query = FALSE
                                                , object = session
                                                , id.vals = id
                                                , n.tr = 3
                                                , tr.names = c("control", "lossprotect", "lossclimate")
                                                , assg.prob = c(1/3, 1/3, 1/3)
                                                , assg.prob.stat = "trimmean"
                                                , trim = 0.01
                                                , assg.prob.method = "ktimes"
                                                , exact.vars = exact_var
                                                , exact.vals = exact_val
                                                , seed = 815
                                                , seed.dist = 19930531
                                                , file.name = session)
                            }
                            seqout$x[seqout$x['ID'] == id , "Tr"]
                            }
                           ''')

                r_f = robjects.r['f']
                out = r_f(cap_id, py_exact_var, py_exact_val, py_session)
                resp.text = "TrAssg=" + str(out[-1])
            except IOError:
                raise falcon.HTTPNotFound()
        else:
            try:
                resp.text = "TrAssg=error"
            except IOError:
                raise falcon.HTTPNotFound()
# falcon.API instances are callable WSGI apps
app = falcon.API()

app.add_route('/test', Resource())
