import json
import statistics
import codecs
from collections import defaultdict
import re
import geoip2.database
training_Path= "traning_set.json"
testing_Path = "test_set.json"
userToIP= "User2IP.json"

class User:
    def __init__(self):
        self.author= ""
        self.IPs= set()
        self.IPcount= defaultdict(int)
        self.mainlyIP = ""
        self.isTroll = False
        self.region= ""
        
    def addIP(self, ip):
        self.IPs.add(ip)
        self.IPcount[ip] += 1
    
    def checkMainlyUse(self):
        mainly= 0
        for ip in self.IPcount:
            mainly = max(mainly, self.IPcount[ip])
            if mainly == self.IPcount[ip]:
                self.mainlyIP= ip

class IPProcessor:
    def __init__(self):
        self.DBreader = geoip2.database.Reader('GeoLite2-City.mmdb')
        self.allUser= {}
        self.normals= set() # all normal users
        self.trolls= set() 
        self.normalIPs = defaultdict(set) # normal author -> IPs
        self.trollIPs = defaultdict(set)
        self.otherIPs= defaultdict(set)
        self.IPusers = defaultdict(set)  # IP -> authors use this IP
        self.region = defaultdict(int)
        ip_mean = 0.0
        ip_stdev= 0.0
        population_mean= 0.0 # calculate the mean of how many IP used per user in the population
        population_stdev= 0.0 # standard deviation
        normal_mean= 0.0
        normal_stdev= 0.0
        troll_mean= 0.0
        troll_stdev = 0.0
        other_mean= 0.0
        other_stdev = 0.0
        self.normal_count = 0
        self.troll_count = 0
        

    def AddToSet(self, author, ip):
        if "." not in ip:
            return

        if author in self.normals:
            self.normalIPs[author].add(ip)
        elif author in self.trolls:
            self.trollIPs[author].add(ip)
        else:
            self.otherIPs[author].add(ip)
            if author not in self.allUser:
                newuser = User()
                newuser.author = author
                self.allUser[newuser.author] = newuser
                
        self.allUser[author].addIP(str(ip))
        self.IPusers[ip].add(author)
        
    def testAddToSet(self, author, ip):
        print("TestAdd %s, %s " %(author, ip), end=' ')
        print(self.allUser[author].IPcount[ip])

    def printIPs(author):
        if author in self.normals:
            for key in self.normals:
                print(key, end = ' ')
                for IP in self.normalIPs[key]:
                    print(IP, end = ' ')
                print()
        if author in self.trolls:
            for key in self.trolls:
                print(key, end = ' ')
                for IP in self.trollIPs[key]:
                    print(IP, end = ' ')
                print()

    def testinit(self):
        print("len of normal users: %d" % (len(self.normals)))
        for normaluser in self.normals:
            print("ID is %s, %s, %r" % (normaluser, self.allUser[normaluser].author, self.allUser[normaluser].isTroll))
        print("len of troll users: %d" % (len(self.trolls)))
        for trolluser in self.trolls:
            print("ID is %s, %s, %r" % (trolluser, self.allUser[trolluser].author, self.allUser[trolluser].isTroll))
    
    def initUsers(self):
        for normaluser in self.normals:
            newuser = User()
            newuser.author = normaluser
            self.allUser[newuser.author]= newuser
        
        for trolluser in self.trolls:
            newuser = User()
            newuser.author = trolluser
            newuser.isTroll = True
            self.allUser[newuser.author] = newuser
            
    def loadtesting(self, testing_Path):
        # read troll and normal users from training sets
        with open(testing_Path, "r", encoding="utf-8") as read_file:
            data = json.load(read_file)
        for user_comment in data["user_comments"]:
            if user_comment["isTroll"] is True:
                self.testing_trolls.add(user_comment["id"])
            else:
                self.testing_normals.add(user_comment["id"])
        self.initUsers()    

    def loadtraining(self, training_path):
        # read troll and normal users from training sets
        with open("user_comments_all.json", "r", encoding="utf-8") as read_file:
            data = json.load(read_file)
        for user_comment in data["user_comments"]:
            if user_comment["isTroll"] is True:
                self.trolls.add(user_comment["id"])
            else:
                self.normals.add(user_comment["id"])
        # construct trolls and normal user instance
        self.initUsers() 

    def loadfiles(self):
        # read troll and normal users from training sets
        with open("user_comments_all.json", "r", encoding="utf-8") as read_file:
            data = json.load(read_file)
        for user_comment in data["user_comments"]:
            if user_comment["isTroll"] is True:
                self.trolls.add(user_comment["id"])
            else:
                self.normals.add(user_comment["id"])

        # construct trolls and normal user instance
        self.initUsers() 

        # read author, ip from raw data
        with open("Gossiping-20400-24800.json", "r", encoding="utf-8") as read_file:
            data = json.load(read_file)
        for article in data["articles"]:
            # extract article IP 
            if article.get("author") and article.get("ip"):
                author= article["author"].split()[0]
                ip= article["ip"]
                self.AddToSet(author, ip)

            # extract comments IP 
            for comment in article["messages"]:
                if comment.get("push_userid") and comment.get("push_ipdatetime"):
                    author = comment["push_userid"]
                    ip = comment["push_ipdatetime"].split()[0]
                    self.AddToSet(author, ip)

        for author in self.allUser:
            self.allUser[author].checkMainlyUse()
            self.allUser[author].region = self.IPRegion(self.allUser[author].mainlyIP)
            self.region[self.allUser[author].region] += 1

    def domath(self):
        numbers = [len(self.IPusers[key]) for key in self.IPusers] #if len(self.IPusers[key])< 10000]
        self.ip_mean = statistics.mean(numbers)
        self.ip_stdev= statistics.stdev(numbers)
        print("avg per IP used by %3f users\nstdev: %3f" % (self.ip_mean, self.ip_stdev))

        numbers = [len(self.normalIPs[key]) for key in self.normalIPs]
        self.normal_mean = statistics.mean(numbers)
        self.normal_stdev= statistics.stdev(numbers)
        print("avg normal user use %3f IP\nstdev: %3f" % (self.normal_mean, self.normal_stdev))

        numbers = [len(self.trollIPs[key]) for key in self.trollIPs]
        self.troll_mean = statistics.mean(numbers)
        self.troll_stdev= statistics.stdev(numbers)
        print("avg troll user use %3f IP\nstdev: %3f" % (self.troll_mean, self.troll_stdev))

        numbers = [len(self.otherIPs[key]) for key in self.otherIPs]
        self.other_mean= statistics.mean(numbers)
        self.other_stdev= statistics.stdev(numbers)
        print("avg other user use %3f IP\nstdev: %3f" % (self.other_mean, self.other_stdev))

        self.population_mean = (self.normal_mean + self.troll_mean + self.other_mean) / 3
        self.population_stdev= (self.normal_stdev + self.troll_stdev + self.other_stdev) / 3
        print("avg population user use %3f IP\nstdev: %3f" % (self.population_mean, self.population_stdev))

    def chkUser(self, author):
        if author in self.allUser:
            numIP= len(self.allUser[author])
            print(author, numIP, self.normal_mean + 2 * self.normal_stdev)
            if numIP > self.normal_mean + 2 * self.normal_stdev:
                return True
            else:
                return False
        return False    
    
    def compIP(self, author):
        if author in self.normals:
            numIP= len(self.normalIPs[author])
            if numIP > self.normal_mean+ 2*self.normal_stdev:
                self.normalweird.add(author)
                if author in self.testing_normals or self.testing_trolls:
                    if author in self.testing_normals:
                        print(author, " is Normal in testing set")
                        self.normal_count += 1
                    elif author in self.testing_trolls:
                        print(author, " is Troll in testing set")
                        self.troll_count += 1
                    
        elif author in self.trolls:
            numIP= len(self.trollIPs[author])
            if numIP > self.normal_mean + 2 * self.normal_stdev:# or ((numIP - self.normal_mean - 2 * self.normal_stdev > 0) and numIP < self.normal_mean - 2 * self.normal_stdev):
                if author in self.testing_normals or self.testing_trolls:
                    if author in self.testing_normals:
                        print(author, " is Normal in testing set")
                        self.normal_count += 1
                    elif author in self.testing_trolls:
                        print(author, " is Troll in testing set")
                        self.troll_count += 1

    def getDecision(self):
        self.loadtesting(testing_Path)
        true_positive, false_positive, true_negative, false_negative = 0,0,0,0
        for author in self.testing_trolls:
            numIP = len(self.trollIPs[author])
            if numIP > self.population_mean + 2 * self.population_stdev:
                true_negative += 1
            else:
                false_negative += 1
        for author in self.testing_normals:
            numIP = len(self.normalIPs[author])
            if numIP > self.population_mean + 2 * self.population_stdev:
                false_positive += 1
            else:
                true_positive += 1

        print("precision: ", true_positive/(true_positive+false_positive), "recall: ", true_positive/(true_positive+false_negative))

    def writeUserJson(self):
        allset = {}
        for key in self.normalIPs:
            allset[key]= list(self.normalIPs[key])
        for key in self.trollIPs:
            allset[key]= list(self.trollIPs[key])
        for key in self.otherIPs:
            allset[key]= list(self.otherIPs[key])

        with codecs.open('User2IP.json', 'a', encoding='utf-8') as f:
            f.write('{"User2IP":[\n')
        for k in allset:
            classified_data = {'id' : k,
                               'ip' : allset[k],
                               }
            d = json.dumps(classified_data, sort_keys=False, ensure_ascii=False)
            d = d + ',\n'
            with codecs.open('User2IP.json', 'a', encoding='utf-8') as f:
                f.write(d)
        with codecs.open('User2IP.json', 'a', encoding='utf-8') as f:
            f.write(']}\n')

    def writeIPJson(self):
        allset = {}
        for key in self.IPusers:
            allset[key]= list(self.IPusers[key])
        with open("IP2User.json", "w") as write_file:
            json.dump(allset, write_file, sort_keys=True, indent=2, separators=(',', ': '))
    
    def writemath(self):
        with codecs.open('IPstat.json', 'a', encoding='utf-8') as f:
            f.write('{"stat":[\n')
            group= {}
            group['population']= []
            group['population'].append({
                'average': self.population_mean,
                'stdev': self.population_stdev
            })
            
            group['normal']= []
            group['normal'].append({
                'average': self.normal_mean,
                'stdev': self.normal_stdev
            })

            group['troll']= []
            group['troll'].append({
                'average': self.troll_mean,
                'stdev': self.troll_stdev
            })

            group['other']= []
            group['other'].append({
                'average': self.other_mean,
                'stdev': self.other_stdev
            })
            d = json.dumps(group, sort_keys=False, ensure_ascii=False)
            f.write(d)
        with codecs.open('IPstat.json', 'a', encoding='utf-8') as f:
            f.write(']}\n')

    def loadIPJson(self):
        with open("User2IP.json", "r", encoding="utf-8") as read_file:
            data = json.load(read_file)
        for item in data["User2IP"]:
            self.allUser[item['id']]= item['ip']

    def loadStat(self):
        with open("IPstat.json", "r", encoding="utf-8") as read_file:
            data = json.load(read_file)
        for item in data['stat']:
            if item['group'] == 'population':
                self.population_mean= item['average']
                self.population_stdev= item['stdev']
            elif item['group'] == 'normal':
                self.normal_mean= item['average']
                self.normal_stdev= item['stdev']
            elif item['group'] == 'troll':
                self.troll_mean= item['average']
                self.troll_stdev= item['stdev']
            elif item['group'] == 'other':
                self.other_mean= item['average']
                self.other_stdev= item['stdev']

    def IPRegion(self, ip):
        response = self.DBreader.city(ip)
        return response.country.iso_code
    
    def SummarizeRegion(self):
        with codecs.open('Region.json', 'a', encoding='utf-8') as f:
            for key in self.region:
                print(key, self.region[key])
    
if __name__=="__main__":    
    cIP = IPProcessor()
    cIP.loadIPJson()
    cIP.loadStat()
