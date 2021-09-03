from tool_tracking.BiasProcessing.corrector.roadLms import RoadLms
from tool_tracking.BiasProcessing.saver.roadCorrectorTable import RoadCorrectorTable
import saver as Saver

class RoadLmsTable(RoadCorrectorTable):
    name = "roadLms_t"

    @staticmethod
    def createTables(conn):
        RoadCorrectorTable.createTables(conn)
        RoadLmsTable.createTable(conn)

    @staticmethod
    def createTable(conn):
        Saver.saveData.executeRequest(conn, 'DROP TABLE {}'.format(RoadLmsTable.name))

        command = RoadLmsTable.createCommand()

        Saver.saveData.executeRequest(conn, command)

    @staticmethod
    def createCommand():
        
        command = []
        command.append("CREATE TABLE IF NOT EXISTS {} (".format(RoadLmsTable.name))
        command.append("id              INTEGER,") #Node ID
        command.append("FOREIGN KEY(id) REFERENCES roadCorrector_t(id) ON UPDATE CASCADE ON DELETE CASCADE")
        command.append(");")
        command = ''.join(command)

        return command