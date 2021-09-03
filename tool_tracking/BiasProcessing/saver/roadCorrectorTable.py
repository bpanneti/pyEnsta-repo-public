from tool_tracking.BiasProcessing.corrector.roadCorrector import RoadCorrector
from tool_tracking.BiasProcessing.saver.biasCorrectorTable import BiasCorrectorTable
import saver as Saver

class RoadCorrectorTable(BiasCorrectorTable):
    name = "roadCorrector_t"

    @staticmethod
    def createTables(conn):
        BiasCorrectorTable.createTables(conn)
        RoadCorrectorTable.createTable(conn)

    @staticmethod
    def createTable(conn):
        Saver.saveData.executeRequest(conn, 'DROP TABLE {}'.format(RoadCorrectorTable.name))

        command = RoadCorrectorTable.createCommand()

        Saver.saveData.executeRequest(conn, command)

    @staticmethod
    def createCommand():
        
        command = []
        command.append("CREATE TABLE IF NOT EXISTS {} (".format(RoadCorrectorTable.name))
        command.append("id              INTEGER,") #Node ID
        command.append("integration     INTEGER,")
        command.append("threshold       INTEGER,")
        command.append("FOREIGN KEY(id) REFERENCES biasCorrector_t(id) ON UPDATE CASCADE ON DELETE CASCADE")
        command.append(");")
        command = ''.join(command)

        return command