import sys
from socket import *
from time import sleep
import traceback
import json
import sqlite3
import threading
import hashlib
import random
from logging import debug, info, warning, basicConfig, INFO, DEBUG, WARNING

basicConfig(level=DEBUG)

#Protocols
"""
Menu drawing - (Reserved, String, IP, Response?, Response_Command, Token?, Secondary_response, Local, Reserved)
Standard communication - (Message, (Payload), Token)
Server relay communications - (Relay, (Message, (Payload)), Token, (Recipients)

Menu
0. Reserved - A reserved character
1. String - The string displayed on the client side
2. IP - Who is the message being set to? Constants = pi, server. Or just the direct IP address
3. Response? - Does the user need to fill in some extra information?
4. Command sent to the server to run the instruction
5. Token?
6. Secondary_response - Does the client need to wait for a reply?
7. Local - Is it a command only for the local user, it will use the client IP address
8. Reserved




"""

def broadcaster():
    s = socket(AF_INET, SOCK_DGRAM)
    s.bind(('', 0))
    s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    s.sendto('hello', ('<broadcast>', 50010))
    info('Broadcasting to network my IP')
    s.close()


class clientMenu(threading.Thread):

    def __init__(self, ip, level, menuOpt = "Main", clientList = ""):
        super(clientMenu, self).__init__()
        self.menu =[]
        self.ipMenu = []
        self.ip = ip
        self.level = level
        self.menuOpt = menuOpt
        self.clientList = clientList

        #--------------------------------
        self.allShutdown = 2
        self.allReboot = 2
        self.allGPIO = 2
        self.allScreenShare = 2
        self.allBlankScreen = 2


        self.viewAccessAllPis = 2
        self.viewMyPi = 1



        #--------------------------------

        self.exit = 0
        self.shutdown = 2
        self.localShutdown = 1
        self.reboot = 2
        self.localReboot = 1
        self.scratch = 1
        self.assignName = 2
        self.localLED = 1
        self.LED = 2
        self.GPIO = 2
        self.addToGroup = 2
        self.resetPassword = 2

        #--------------------------------

    def run(self):
        if self.menuOpt == "Main":
            self.sendMainMenu(self.mainBuild(self.level))
        elif self.menuOpt == "Home":
            self.sendHomeMenu(self.homeMenuBuild(self.level))



# Menu drawing - (Reserved, String, IP, Response?, Response_Command, Token?, Secondary_response, Local, Reserved)
    def mainBuild(self, level):
        debug("Level is " + str(level))
        if self.shutdown <= level:
            value = ("", "Shutdown", "pi", False, "Shutdown", True, "None", False, "" )
            self.menu.append(value)

        if self.localShutdown <= level:
            value = ("", "Shutdown my Pi", "pi", False, "Shutdown", True, "None", True, "" )
            self.menu.append(value)

        if self.reboot <= level:
            value = ("", "Reboot", "pi", False, "Reboot", True, "None", False, "" )
            self.menu.append(value)

        if self.localReboot <= level:
            value = ("", "Reboot my Pi", "pi", False, "Reboot", True, "None", True, "" )
            self.menu.append(value)

        if self.assignName <= level:
            value = ("", "Assign a name to this Pi", "server", "Please enter a new name", "name", True, "None", False, "" )
            self.menu.append(value)





        if self.exit <= level:
            value = ("", "Exit", "Exit", False, "Exit", True, "None", True, "" )
            self.menu.append(value)

        return self.menu


    def sendMainMenu(self, menuList):
        sleep(0.3)
        s = sender((self.ip,), ("MenuDraw", menuList, "1"), 50010, 1)
        s.run()

    def sendHomeMenu(self, menuList):
        sleep(0.3)
        s = sender((self.ip,), ("HomeDraw", menuList, "1"), 50009, 1)
        s.run()


    def homeMenuBuild(self, level):
        debug("Level is " + str(level))
        if self.allShutdown <= level:
            value = ("", "Shutdown all Pis", "all", False, "Shutdown", True, "None", False, "" )
            self.menu.append(value)

        if self.allReboot <= level:
            value = ("", "Reboot all Pis", "all", False, "Reboot", True, "None", False, "" )
            self.menu.append(value)

        for count in range(0, len(self.clientList)):
            if (self.viewAccessAllPis <= level):
                value = ("", self.clientList[count][0], "ClientMenu", False, "ClientMenu", True, "None", False, "" )
                self.ipMenu.append(value)
        print("Menu now built, it is")
        totalMenu = [self.menu, self.ipMenu]
        print(totalMenu)
        return totalMenu




class console(threading.Thread):

    def __init__(self):
        super(console, self).__init__()
    def run(self):
        while True:
            response = raw_input()
            if response == "c":
                response = ""
                self.cMenu()
    def cMenu(self):
        sqlU = sqlite3.connect('Pi-control.db')
        sqlUc = sqlU.cursor()
        notdone = True
        while notdone:
            print("\n" * 5)
            print("Server Console menu")
            print("-------------------")
            print("")
            print("1. Add new user")
            print("2. Delete user")
            print("3. Modify user permission")
            print("4. Display all users and their permissions")
            print("5. Reset a users password")
            answer = raw_input()
            if answer == "1":
                self.newUser(sqlU, sqlUc)
            elif answer == "2":
                self.displayUsers(sqlU, sqlUc)
                self.deleteUser(sqlU, sqlUc)
            elif answer == "3":
                self.modifyPerms(sqlU, sqlUc)
            elif answer == "4":
                self.displayUsers(sqlU, sqlUc, True)
            elif answer == "5":
                self.resetPassword(sqlU, sqlUc)



    def newUser(self, sqlU, sqlUc):
        print("\n" * 5)
        correct = False
        while correct == False:
            username = (raw_input("Enter new username : ")).lower()
            password1 = raw_input("Enter password : ")
            password2 = raw_input("Enter password : ")
            level = raw_input("Enter permission level (1-3) : ")
            if not (password1 == password2):
                correct = False
                print("Passwords must match, try again")
                wait()
                break
            else:
                correct = True
                usernamex = (username, )
                sqlUc.execute("""SELECT UserID, Username, Salt, Hash, PermissionLevel, Token FROM User WHERE Username = ? """, usernamex)
                result = sqlUc.fetchone()
                if result == None:
                    hashresult = createHash(password1)
                    debug((username, hashresult[0], hashresult[1], level))
                    sqlUc.execute("""INSERT INTO User VALUES(NULL,?,?,?,?, NULL)""", ((username, str(hashresult[0]), str(hashresult[1]), level)))
                    sqlU.commit()
                    print("User " + str(username) + " has been successfully added")
                    wait()
                else:
                    print("")
                    print("Username already exists!")
                    wait()
                    break


    def displayUsers(self, sqlU, sqlUc, delay = False):
        sqlUc.execute("""SELECT UserID, Username, PermissionLevel FROM User""")
        table = sqlUc.fetchall()
        print("ID : Name - Permission level")
        print("-----------------------")
        for count in range(0, len(table)):
            #print(str(table[count]))
            print(str(table[count][0]) + " : " + str(table[count][1]) + " - " + str(self.userperm(table[count][2])))
        if delay:
            wait()


    def checkIfUserExists(self, sqlU, sqlUc, cID, searchby = "UserID", display = False):
        cID = ((cID, ))
        debug(str(cID))
        sqlUc.execute("""SELECT UserID, Username FROM User WHERE UserID = ? """, cID)
        result = sqlUc.fetchone()
        if result == None:
            return False
        else:
            print(result[1])
            return True


    def deleteUser(self, sqlU, sqlUc):
        print("Enter the ID to delete")
        cID = raw_input()
        if self.checkIfUserExists(sqlU, sqlUc, cID, "UserID", True):
            print("Are you sure you want to remove this user? Type yes or no")
            user = raw_input().lower()
            if user == "yes":
                users = ((int(cID), ))
                sqlUc.execute("""DELETE FROM User WHERE UserID = ? """, users)
                sqlU.commit()
                print("User successfully deleted")
                wait()


    def resetPassword(self, sqlU, sqlUc):
        self.displayUsers(sqlU, sqlUc)
        print("Enter User ID to reset the password of")
        cID = raw_input()
        if self.checkIfUserExists(sqlU, sqlUc, cID):
            print("Please enter a password to set it to")
            print("To exit, type 0")
            password = raw_input()
            hashresult = createHash(password)
            sqlUc.execute("""UPDATE "main"."User" SET "Salt" = ?, "Hash" = ? WHERE  "UserID" = ?""",(str(hashresult[0]), str(hashresult[1]), int(cID)))
            sqlU.commit()
            print("Password successfully changed")
            wait()


    def userperm(self, value):
        value = str(value)
        if value == "1":
            return "Student"
        elif (value == "2"):
            return "Teacher"
        elif value == "3":
            return "Admin"
        else:
            return "Unknown.."


    def modifyPerms(self, sqlU, sqlUc):
        self.displayUsers(sqlU, sqlUc)
        print("Please enter a user ID to modify permissions of")
        cID = raw_input()
        if self.checkIfUserExists(sqlU, sqlUc, cID):
            print("Please enter the new permission level, must be between 1-3")
            print("1:Student - 2:Teacher - 3:Admin")
            level = raw_input()
            if (level == "1") or (level == "2") or (level == "3"):
                sqlUc.execute("""UPDATE "main"."User" SET "PermissionLevel" = ? WHERE  "UserID" = ?""",(int(level), int(cID), ))
            else:
                print("Error, value must be between 1 and 3")

#-------------------------------------------END OF CONSOLE CLASS-------------------------------------------
#-------------------------------------------END OF CONSOLE CLASS-------------------------------------------
#-------------------------------------------END OF CONSOLE CLASS-------------------------------------------

class sender(threading.Thread):

    def __init__(self, sendlist, data, port = 50008, timeout = 0.3):
        super(sender, self).__init__()
        self.sendlist = sendlist
        self.data = data
        self.dport = port
        self.timeout = timeout
    def run(self):
        for client in range(0, len(self.sendlist)):
            try:
                self.send(self.sendlist[client], self.data)
            except:
                warning("Command to "+ str(self.sendlist[client])+ " failed, commmand was " + str(self.data))
    def send(self, client, data):
        debug("sending " + str(client) + " " + str(data))
        s = socket(AF_INET, SOCK_STREAM)
        s.settimeout(self.timeout)
        debug("Connecting to client at " +str(client) + " " + str(self.dport))
        s.connect((client, self.dport))
        s.sendall(json.dumps((data,)))
        s.close()
        debug("Data is sent!")

#-------------------------------------------END OF SENDER CLASS-------------------------------------------

class ping(threading.Thread):

    def __init__(self):
        super(ping, self).__init__()
        self.pingFreq = 3

    def run(self):
        sql = sqlite3.connect('Pi-control.db')
        while True:
            self.pinger2(sql)
            sleep(self.pingFreq)

    def pinger2(self,sql):
        sqlp = sql.cursor()
        for row in sqlp.execute("""SELECT IP FROM ClientID"""):
            s = socket(AF_INET, SOCK_STREAM)
            s.settimeout(0.3)
            try:
                s.connect((row[0], 50008))
                s.sendall(json.dumps(('Ping',)))
                self.data = s.recv(1024)
                s.close()
            except error:
                sqlp.execute("""DELETE FROM ClientID WHERE IP = ?""", row)
                sql.commit()

#-------------------------------------------END OF PINGER CLASS-------------------------------------------

class transmissionHandler(threading.Thread):
    def __init__(self, ip, data):
        super(transmissionHandler, self).__init__()
        debug(ip)
        self.ip = ip
        self.data = data

    def run(self):
        sql = sqlite3.connect('Pi-control.db')
        self.Handler(self.ip, self.data, sql)
    def Handler(self, ip, data, sql):
        info("Handler called!!")
        level = checkToken(self.data[2])
        self.interpreter(ip, data, level, sql)
    def interpreter(self, ip, data, level, sql):
        debug(data)
        if (data[0] == "name") and (level >1):
            self.name = (data[1][0])
            self.ip = (data[1][1])
            print("IP is " + str(self.ip) + " Name is " + str(self.name))
            sqld = sql.cursor()
            debug(self.ip)
            sqld.execute("""SELECT Serial FROM ClientID WHERE Ip = ? """,(self.ip,) )
            d = (self.name, sqld.fetchone()[0])
            sqld.execute("""UPDATE Metadata SET Name = ? WHERE Serial = ?""",d)
            sql.commit()
            sql.close()
        if (data[0] == "FeatureList"):
            MenuMake = clientMenu(self.ip, checkToken(data[2]))
            MenuMake.run()
        if (data[0] == "Relay"):
            print("Relay data arrived!")
            print(data[1][1])
            if data[1][1] == []:
                s = sender(data[3], (data[1][0]))
                s.run()

#-------------------------------------------END OF transmissionHandler CLASS-------------------------------------------


#*******************************************START OF MAIN PROGRAM*******************************************
#*******************************************START OF MAIN PROGRAM*******************************************
#*******************************************START OF MAIN PROGRAM*******************************************

def wait():
    print("")
    raw_input("Press any key to continue..")
    print("")


def randomDigits(digits):
    lower = 10**(digits-1)
    upper = 10**digits - 1
    toreturn = random.randint(lower, upper)
    info("Hash generated is " + str(toreturn))
    return toreturn


def createHash(password):
    salt = randomDigits(32)
    hashResult = hashlib.sha512(str(salt) + str(password)).hexdigest()
    return (salt, hashResult)


def decodeHash(hash, salt, password):
    info("At hash, hash is " + str(hash) + " and password is " + str(password))
    hashResult = hashlib.sha512(str(salt) + str(password)).hexdigest()
    info("Hash in database is " + str(hashResult) + " While hash provided is " + str(hash))
    if hashResult == hash:
        return True
    else:
        return False


def getToken(credentials, sql, sqlc):
    username = (credentials[0],)
    sqlc.execute("""SELECT UserID, Username, Salt, Hash, PermissionLevel, Token FROM User WHERE Username = ? """, username)
    fetch = sqlc.fetchone()
    debug(str(fetch))
    if not (fetch == None):
        sqlc.execute("""SELECT Hash, Salt FROM User WHERE Username = ? """, username)
        hashSalt = sqlc.fetchone()
        if (decodeHash(hashSalt[0], hashSalt[1], credentials[1])) == True:
            return randomDigits(10)
        else:
            return False
    else:
        return False


def checkToken(token):
    sqls = sqlite3.connect('Pi-control.db')
    sqld = sqls.cursor()
    token = (token, )
    sqld.execute("""SELECT PermissionLevel FROM User WHERE Token = ? """, token)
    result = sqld.fetchone()
    if not (result == None):
        debug(str(result))
        return result[0]
    else:
        return 0




def getPermission(user):
    pass

def checkPermission(ID, Required):
    pass

def datachecker2(sql, sqlc):
    info('')
    info('Waiting for incoming messages')
    s.settimeout(10) #Time to wait before going onto next function
    try:
        client, address = s.accept()
        sleep(0.1)
        data = client.recv(size)
        if data:
            data = json.loads(data)
            if (data[0] == 'Register'):
                ip = (address[0],)
                sqlc.execute("""SELECT CId, IP, Serial FROM ClientID WHERE IP = ? """, ip)
                if sqlc.fetchone() == None:
                    serial = str(data[1])
                    dat = (address[0], serial)
                    sqlc.execute("""INSERT INTO ClientID VALUES(NULL,?, ?)""", dat)
                    sqlc.execute("""SELECT Serial FROM Metadata WHERE Serial = ? """, (serial,))
                    if sqlc.fetchone() == None:
                        sqlc.execute("""INSERT INTO Metadata VALUES(?,NULL) """, (serial,))
                    sql.commit()
                    info('')
                    info('-------------------------------------')
                    info('Client at ' + str(address[0]) +' added to list')
                    info('-------------------------------------')
                    info('')
                client.send(json.dumps(('Accept',)))
                sleep(0.05)

            elif data[0] == "Token":
                credentials = data[1]
                ip = (address[0],)
                result = getToken(credentials, sql, sqlc)
                if not (result == False):
                    d = (result, credentials[0])
                    debug(str(d))
                    sqlc.execute("""UPDATE "main"."User" SET "Token" = ? WHERE  "Username" = ?""", d)
                    sql.commit()
                    #sqlc.execute("""UPDATE User SET Token = ? WHERE Username = ?""",d)
                else:
                    result = 0
                client.send(json.dumps((result,)))

            else:
                debug(data)
                debug("Data it cant get is" + str(data[2]))
                if (checkToken(data[2]) > 0):
                    if data[0] == 'RequestList':
                        sqlc.execute("""SELECT ClientID.IP, ClientID.Serial, Metadata.Name
                                    FROM ClientID
                                    INNER JOIN Metadata
                                    ON ClientID.Serial = Metadata.Serial""")
                        tosendlist = sqlc.fetchall()
                        cm = clientMenu(address[0], checkToken(data[2]), "Home", tosendlist)
                        cm.run()


                        #client.send(json.dumps((tosendlist,)))
                    else:
                        t = transmissionHandler(address[0], data)
                        t.daemon = True
                        t.start()

                    client.close()
                else:
                    warning("Invalid login")
    except timeout:
        pass
    #except:
        #pass


def createDatabase(sqlc, sql):
    info("Creating database")
    sqlc.execute('''CREATE TABLE ClientID
(
CId INTEGER PRIMARY KEY AUTOINCREMENT,
IP varchar(15) NOT NULL,
Serial varchar(4) NOT NULL
)''')
    sqlc.execute("""CREATE  TABLE IF NOT EXISTS "main"."Connection" ("UserID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE , "IP" VARCHAR NOT NULL , "Key" INTEGER)""")
    sqlc.execute("""CREATE  TABLE  IF NOT EXISTS "main"."Metadata" ("Serial" VARCHAR PRIMARY KEY  NOT NULL  UNIQUE , "Name" VARCHAR)""")
    sqlc.execute("""CREATE  TABLE  IF NOT EXISTS "main"."Group" ("GroupID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE , "Name" VARCHAR NOT NULL , "Description" VARCHAR)""")
    sqlc.execute("""CREATE  TABLE  IF NOT EXISTS "main"."GroupConnection" ("ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE , "Serial" VARCHAR NOT NULL , "GroupID" INTEGER NOT NULL )""")
    sqlc.execute("""CREATE  TABLE  IF NOT EXISTS "main"."User" ("UserID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE , "Username" VARCHAR NOT NULL , "Salt" VARCHAR NOT NULL , "Hash" VARCHAR NOT NULL , "PermissionLevel" INTEGER NOT NULL, "Token" INTEGER )""")
    #sql.commit()

def setupNetworking():
    host = ''
    port = 50000
    backlog = 5
    size = 1024
    s = socket(AF_INET, SOCK_STREAM)
    s.bind((host,port))
    s.listen(backlog)
    s.settimeout(5)
    return s


def InitalSQL(sql):

    sqlc = sql.cursor()
    try:
        sqlc.execute("""DROP TABLE "main"."ClientID" """)
    except:
        info("No database found, creating one")
    try:
        sqlc.execute("""DROP TABLE "main"."Connection" """)
    except:
        pass
    createDatabase(sql, sqlc)
    return sqlc


#**********************************************************- Main program - **********************************************************



while True:
    try:

        size = 1024
        s = setupNetworking()
        clientlist = []
        sql = sqlite3.connect('Pi-control.db')
        sqlc = InitalSQL(sql)

        p = ping()
        p.daemon = True
        p.start() #Starts the pinger thread
        c = console()
        c.daemon = True
        c.start()
        print("")
        print("---------------------")
        print("Server is now running")
        print("---------------------")
        print("")
        print("To access control console press c and then enter")
        print("------------------------------------------------")

        while 1:
            broadcaster()
            #pinger(clientlist)
            #p.pinger2(sql,sqlc)
            #clientlist = datachecker(clientlist)
            datachecker2(sql,sqlc)
    except:
        print('************************************')
        print("System error...")
        traceback.print_exc(file=sys.stdout) #Prints out traceback error
        print('************************************')
        print("")
        print("Hit any key to proceed")
        raw_input()
        print("RESTARTING")
        sleep(3)

