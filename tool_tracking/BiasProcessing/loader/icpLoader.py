from tool_tracking.BiasProcessing.corrector.icp import Icp
import sqlite3


class IcpLoader():
    name = "icp_t"

    @staticmethod
    def load(conn, nodes, emitBiasCorrectors):
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        stmt = "SELECT name  FROM sqlite_master WHERE type='table'  AND name='{}' ; ".format(IcpLoader.name)
        c = cur.execute(stmt)
        result = c.fetchone()

        if result:
            try :
                c = cur.execute(("SELECT biasCorrector_t.id, biasCorrector_t.name, roadCorrector_t.integration, roadCorrector_t.threshold, icp_t.maxIteration, icp_t.tolerance FROM {} "
                + "cross join biasCorrector_t on biasCorrector_t.id = roadCorrector_t.id "
                + "cross join roadCorrector_t on {}.id = roadCorrector_t.id;").format(IcpLoader.name, IcpLoader.name))
                data = c.fetchall()
    
                biasCorrectors = dict()
                node = None
    
                for row in data:
                    if nodes != None:
                        for elt in nodes:
                            if int(elt.id) == row['id']:
                                node = elt
                                break
                        
                        biasCorrectors[row['id']] = Icp(node, row['name'], row['integration'], row['maxIteration'], row['tolerance'], row['threshold'])
    
                emitBiasCorrectors.emit(biasCorrectors)
            except:
                pass
        else:
            print('no table {}'.format(IcpLoader.name))
        
        conn.row_factory = False
        
