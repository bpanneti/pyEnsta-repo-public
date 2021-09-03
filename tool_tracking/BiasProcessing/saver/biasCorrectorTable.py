# from abc import ABCMeta, abstractmethod

import saver as Saver
from tool_tracking.BiasProcessing.corrector.biasCorrector import BiasCorrector

class BiasCorrectorTable:
    name = "biasCorrector_t"

    @staticmethod
    def createTables(conn):
        BiasCorrectorTable.createTable(conn)

    @staticmethod
    def createTable(conn):
        Saver.saveData.executeRequest(conn, 'DROP TABLE {}'.format(BiasCorrectorTable.name))

        command = BiasCorrectorTable.createCommand()

        Saver.saveData.executeRequest(conn, command)

    @staticmethod
    def createCommand():
        
        command = []
        command.append("CREATE TABLE IF NOT EXISTS {} (".format(BiasCorrectorTable.name))
        command.append("id INTEGER,") #Node ID
        command.append("name TEXT,")
        command.append("FOREIGN KEY(id) REFERENCES node_t(id)")
        command.append(");")
        command = ''.join(command)

        return command