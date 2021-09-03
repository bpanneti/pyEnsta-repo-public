from tool_tracking.BiasProcessing.corrector.icp import Icp
from tool_tracking.BiasProcessing.saver.roadCorrectorTable import RoadCorrectorTable
import saver as Saver

class IcpTable(RoadCorrectorTable):
    name = "icp_t"

    @staticmethod
    def createTables(conn):
        RoadCorrectorTable.createTables(conn)
        IcpTable.createTable(conn)

    @staticmethod
    def createTable(conn):
        Saver.saveData.executeRequest(conn, 'DROP TABLE {}'.format(IcpTable.name))

        command = IcpTable.createCommand()

        Saver.saveData.executeRequest(conn, command)

    @staticmethod
    def createCommand():
        
        command = []
        command.append("CREATE TABLE IF NOT EXISTS {} (".format(IcpTable.name))
        command.append("id              INTEGER,") #Node ID
        command.append("maxIteration    INTEGER,")
        command.append("tolerance       REAL,")
        command.append("FOREIGN KEY(id) REFERENCES roadCorrector_t(id) ON UPDATE CASCADE ON DELETE CASCADE")
        command.append(");")
        command = ''.join(command)

        return command