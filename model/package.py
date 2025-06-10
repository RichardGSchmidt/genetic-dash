import datetime
import csv


#UI Methods I wrote.  They look ugly in here but nice on screen.
def format_package_text(id_text, address_text, status_text, time_departed_text, time_due_text, time_delivered_text):
    if len(address_text) < 25:
        address_text = address_text + " " * (25 - len(address_text))
    if len(status_text) < 20:
        status_text = status_text + " " * (20 - len(status_text))
    if len(time_departed_text) < 9:
        time_departed_text = " " * (9 - len(time_departed_text)) + time_departed_text
    if len(time_due_text) < 9:
        time_due_text =  time_due_text + " " * (9 - len(time_due_text))
    if len(time_delivered_text) < 9:
        time_delivered_text = " " * (9 - len(time_delivered_text)) + time_delivered_text

    return f'{id_text}\t{address_text[:15:]}\t{status_text[:15:]}\t{time_departed_text[:9:]}\t{time_due_text[:9:]}\t{time_delivered_text[:9:]}'


def get_header():
    return format_package_text("Id","Address", "Status", "Departure", "Due", "Delivered",)

#(Task A and Task B)  This class allows for the easy implementation of packages inside the hashchain class
class Package:
    def __init__(self, package_id, address, time_due):
        self.id = package_id
        self.address = int(address)

        if time_due == 'EOD':
            self.time_due = datetime.timedelta(hours=23, minutes=59, seconds=59)
        else:
            #using python stripping here for easy inputs from the csv
            self.time_due = datetime.timedelta(hours = int (time_due[0:2]), minutes = int(time_due[3:5]), seconds = int(0))

        self.status = "Unavailable"
        self.time_departed = None
        self.time_delivered = None


    #  returns a string displaying desired info for the user
    def __str__(self):
        id_text = str(self.id)
        with open("./data/addresses.csv", 'r') as myFile:
            addresses = list(csv.reader(myFile))

        address_text = ''
        for row in addresses:
            if int(self.address) == int(row[0]):
                address_text = row[2]
        city_text = str(self.city)
        zip_text = str(self.zip)
        weight_text = str(self.weight)
        status_text = str(self.status)
        time_departed_text = str(self.time_departed)
        if self.time_due == datetime.timedelta(hours=23, minutes=59, seconds=59):
            time_due_text = "EOD"
        else:
            time_due_text = str(self.time_due)
        time_delivered_text = str(self.time_delivered)
        time_available_text = str(self.time_available)
        return format_package_text(id_text,address_text,city_text,zip_text,weight_text,status_text, time_departed_text,time_due_text,time_delivered_text,time_available_text)

    #updates package status for a given time
    def update(self, request_time):
        if self.time_available > request_time:
            self.status = "Unavailable"
        elif self.time_delivered < request_time:
            if self.ontime():
                self.status = "Delivered"
            else:
                self.status = "LATE-Delivered"
        elif self.time_departed < request_time:
            self.status = "Out for Delivery"
        else:
            self.status = "At Hub"

    def ontime(self, for_time=datetime.timedelta(hours=24)):
        if self.time_delivered is None:
            return for_time < self.time_due
        else:
            return self.time_delivered < self.time_due