from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import List, Dict
import requests
import os
import hashlib, uuid
import datetime

app = FastAPI()

#   Load .env
load_dotenv( '.env' )
user = os.getenv( 'user' )
password = os.getenv( 'password' )
MY_VARIABLE = os.getenv('MY_VARIABLE')

#   Connect to MongoDB
client = MongoClient(f"mongodb+srv://{user}:{password}@cluster0.dpx3ndy.mongodb.net/")
db = client['EventBud']
# collection = db['Events']

#   CORS
origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_credentials = True,
    allow_methods = ['*'],
    allow_headers = ['*'],
)

##############################################################
#
#   Class OOP
#

class Ticket( BaseModel ):
    ticketID : str
    validDatetime : datetime.datetime
    expiredDatetime : datetime.datetime
    status : str
    seatNo : str
    className : str
    eventID : str
    userID : str
    eventName : str
    eventImage : str
    location : str
    runNo : int

class NewTicketClass( BaseModel ):
    className: str
    amountOfSeat: int
    pricePerSeat: int
    rowNo: int
    columnNo: int
    validDatetime: datetime.datetime
    expiredDatetime: datetime.datetime
    zoneSeatImage: str

class TicketClass( BaseModel ):
    className: str
    amountOfSeat: int
    pricePerSeat: int
    rowNo: int
    columnNo: int
    seatNo: Dict[str, str]  #   seatNo: status
    validDatetime: datetime.datetime
    expiredDatetime: datetime.datetime
    zoneSeatImage: str

class ReservedTicket( BaseModel ):
    eventID: str
    userID: str
    className: str
    seatNo: List[str]

class NewTicket( BaseModel ):
    eventID: str
    userID: str
    className: str
    seatNo: List[str]   #   List of blank string if no seat

class ZoneRevenue( BaseModel ):
    className: str
    price: int
    ticketSold: int
    quota: int

class BankAccount( BaseModel ):
    bank: str
    accountName: str
    accountType: str
    accountNo: str
    branch: str

class Event( BaseModel ):
    eventID: str
    eventName: str
    startDateTime: datetime.datetime
    endDateTime: datetime.datetime
    onSaleDateTime: datetime.datetime
    endSaleDateTime: datetime.datetime
    location: str
    info: str
    featured: bool
    eventStatus: str
    tagName: List[str]
    posterImage: str
    seatImage: str
    staff: List[str]
    ticketType: str
    ticketClass: List[TicketClass]
    organizerName: str
    timeStamp: datetime.datetime
    totalTicket: int
    soldTicket: int
    totalTicketValue: int
    totalRevenue: int
    zoneRevenue: List[ZoneRevenue]
    bankAccount: BankAccount
    organizerEmail: str

class User( BaseModel ):
    userID: str
    email: str
    firstName: str
    lastName: str
    password_hash: str
    salt: str
    event: List[str]
    telephoneNumber: str

class User_Signup( BaseModel ):
    email: str
    password: str
    firstName: str
    lastName: str

class User_Signin( BaseModel ):
    email: str
    password: str

class User_Edit_Profile( BaseModel ):
    userID: str
    newEmail: str
    newFirstName: str
    newLastName: str
    newTelephoneNumber: str

class User_Reset_Password( BaseModel ):
    userID: str
    oldPassword: str
    newPassword: str

class EventOrganizer( BaseModel ):
    organizerID: str
    email: str
    organizerName: str
    organizerPhone: str
    password_hash: str
    salt: str

class EO_Signup( BaseModel ):
    email: str
    password: str
    organizerName: str
    organizerPhone: str

class EO_Signin( BaseModel ):
    email: str
    password: str

class EventSetting( BaseModel ):
    eventName: str
    tagName: List[str]
    startDateTime: datetime.datetime
    endDateTime: datetime.datetime
    onSaleDateTime: datetime.datetime
    endSaleDateTime: datetime.datetime
    info: str
    location: str
    posterImage: str
    ticketType: str
    seatImage: str

##############################################################
#
#   Helper Functions
#

def hash_password( password, salt = None ):
    '''
        Hash password with salt
        Input: password (str)
        Output: password_hash (str), password_salt (str)
    '''
    if not salt:
        salt = uuid.uuid4().hex
    password_salt = ( password + salt ).encode( 'utf-8' )
    password_hash = hashlib.sha512( password_salt ).hexdigest()
    return password_hash, salt

def generate_userID( email ):
    '''
        Generate userID from email
        Input: email (str)
        Output: userID (str)
    '''
    userID = email.split( '@' )[0]
    
    #   Check if userID already exists
    collection = db['User']
    number = 1
    while collection.find_one( { 'userID' : userID }, { '_id' : 0 } ):
        userID = userID + str( number )
        number += 1

    return userID

def generate_organizerID( email ):
    '''
        Generate organizerID from email
        Input: email (str)
        Output: organizerID (str)
    '''
    organizerID = email.split( '@' )[0]
    
    #   Check if organizerID already exists
    collection = db['EventOrganizer']
    number = 1
    while collection.find_one( { 'organizerID' : organizerID }, { '_id' : 0 } ):
        organizerID = organizerID + str( number )
        number += 1

    return organizerID

def generate_ticketID( eventID, userID, classID, seatNo ):
    '''
        Generate ticketID from eventID, userID, classID, and seatNo
        Input: eventID (str), userID (str), classID (str), seatNo (str)
        Output: ticketID (str)
    '''
    ticketID = eventID + userID + classID + seatNo
    
    #   Check if ticketID already exists
    collection = db['Ticket']
    number = 1
    copyTicketID = ticketID
    while collection.find_one( { 'ticketID' : ticketID }, { '_id' : 0 } ):
        ticketID = copyTicketID + str( number )
        number += 1

    return ticketID

def generate_eventID():
    '''
        Generate eventID
        Input: None
        Output: eventID (str)
    '''
    #   Connect to MongoDB
    collection = db['Events']

    #   Generate eventID
    eventID = 'EV' + str( collection.count_documents( {} ) + 1 ).zfill( 5 )

    number = 2
    #   Check if eventID already exists
    while collection.find_one( { 'eventID' : eventID }, { '_id' : 0 } ):
        eventID = 'EV' + str( collection.count_documents( {} ) + number ).zfill( 5 )
        number += 1

    return eventID

##############################################################
#
#   API
#

#   Root
@app.get('/')
def read_root():
    return { 'details' : f'Hello, this is EventBud API. Please go to {MY_VARIABLE} {user} for more details.' }

#   Get All On-going Events
@app.get('/event', tags=['Events'])
def get_all_event():
    '''
        Get all events
        Input: None
        Output: On-going Events (list)
    '''

    #   Connect to MongoDB
    collection = db['Events']

    #   Get all events
    events = list( collection.find( { 'eventStatus' : 'On-going' }, { '_id' : 0 } ) )

    #   Sort events by startDateTime
    sortedEvents = sorted( events, key = lambda i: i['startDateTime'] )

    #   Get current datetime
    currentDatetime = datetime.datetime.now()

    #   Loop for each event
    for event in sortedEvents:

        #   Check if event is expired
        if event['endDateTime'] < currentDatetime and event['eventStatus'] == 'On-going':
            #   Update event status to expired
            collection.update_one( { 'eventID' : event['eventID'] }, { '$set' : {
                'eventStatus' : 'Expired'
            } } )
            event['eventStatus'] = 'Expired'

    return sortedEvents

#   Get Event Details
@app.get('/event/{eventID}', tags=['Events'])
def get_event( eventID: str ):
    ''' 
        Get event details by eventID
        Input: eventID (str)
        Output: event (dict)
    '''

    #   Connect to MongoDB
    collection = db['Events']

    #   Get event details
    event = collection.find_one( { 'eventID' : eventID }, { '_id' : 0 } )

    #   Check if eventID exists
    if not event:
        raise HTTPException( status_code = 400, detail = 'Event not found' )
    
    #   Get current datetime
    currentDatetime = datetime.datetime.now()

    #   Check if event is expired
    if event['endDateTime'] < currentDatetime and event['eventStatus'] == 'On-going':
        #   Update event status to expired
        collection.update_one( { 'eventID' : eventID }, { '$set' : {
            'eventStatus' : 'Expired'
        } } )
        event['eventStatus'] = 'Expired'

    return event

#   Normal User Sign Up
@app.post('/signup', tags=['Users'])
def user_signup( user_signup: User_Signup ):
    ''' 
        Normal User Sign up
        Input: user_signup (User_Signup)
        Output: result (dict)
    '''

    #   Connect to MongoDB
    collection = db['User']

    #   Check if email already exists
    if collection.find_one( { 'email' : user_signup.email }, { '_id' : 0 } ):
        raise HTTPException( status_code = 400, detail = 'Email already exists.' )
    
    #   Generate userID
    genUserID = generate_userID( user_signup.email )

    #   Hash password
    password_hash, password_salt = hash_password( user_signup.password )
    
    #   Insert user to database
    newUser = User(
        userID = genUserID,
        email = user_signup.email,
        firstName = user_signup.firstName,
        lastName = user_signup.lastName,
        password_hash = password_hash,
        salt = password_salt,
        event = [],
        telephoneNumber = '',
    )
    collection.insert_one( newUser.dict() )
    
    return { 'result' : 'success' }

#   Normal User Signin
@app.post('/signin', tags=['Users'])
def user_signin( user_signin: User_Signin ):
    '''
        Normal User Signin
        Input: user_signin (User_Signin)
        Output: userInfo (dict)
    '''

    #   Connect to MongoDB
    collection = db['User']

    #   Check if email exists
    user = collection.find_one( { 'email' : user_signin.email }, { '_id' : 0 } )
    if not user:
        raise HTTPException( status_code = 400, detail = 'Email or Password incorrect' )
    
    #   Hash password
    password_hash, _ = hash_password( user_signin.password, user['salt'] )

    #   Check if password is correct
    if password_hash != user['password_hash']:
        raise HTTPException( status_code = 400, detail = 'Email or Password incorrect' )
    
    userInfo = {
        'userID' : user['userID'],
        'email' : user['email'],
        'name' : user['firstName'] + ' ' + user['lastName'],
    }
    
    return userInfo

#   Get User Ticket
@app.get('/user_ticket/{userID}', tags=['Users'])
def get_user_ticket( userID: str ):
    '''
        Get user ticket
        Input: userID (str)
        Output: tickets (list)
    '''

    #   Connect to MongoDB
    user_collection = db['User']
    ticket_collection = db['Ticket']
    transaction_collection = db['TicketTransaction']

    #   Check if userID exists
    user = user_collection.find_one( { 'userID' : userID }, { '_id' : 0 } )
    if not user:
        raise HTTPException( status_code = 400, detail = 'User not found' )
    
    #   Get user ticket
    tickets = list( ticket_collection.find( { 'userID' : userID }, { '_id' : 0 } ) )

    #   Sort tickets by ticket status
    status_order = { 'available' : 0, 'scanned' : 1, 'expired' : 2, 'transferred' : 3 }
    sortedTickets = sorted( tickets, key = lambda i: (status_order[i['status']], i['validDatetime']) )

    #   Get current datetime
    currentDatetime = datetime.datetime.now()

    #   Loop for each ticket
    for ticket in sortedTickets:

        #   Check if ticket is expired
        if ticket['expiredDatetime'] < currentDatetime:
            #   Update ticket status to expired
            ticket_collection.update_one( { 'ticketID' : ticket['ticketID'] }, { '$set' : {
                'status' : 'expired'
            } } )
            ticket['status'] = 'expired'

            #   Add transaction
            newTransaction = {
                'ticketID' : ticket['ticketID'],
                'timestamp' : datetime.datetime.now(),
                'transactionType' : 'expired'
            }
            transaction_collection.insert_one( newTransaction )

    return sortedTickets

#   User Edit Profile
@app.post('/update_profile', tags=['Users'])
def user_edit_profile( user_edit_profile: User_Edit_Profile ):
    '''
        User Edit Profile
        Input: user_edit_profile (User_Edit_Profile)
        Output: result (dict)
    '''

    #   Connect to MongoDB
    collection = db['User']

    #   Check if userID exists
    user = collection.find_one( { 'userID' : user_edit_profile.userID }, { '_id' : 0 } )
    if not user:
        raise HTTPException( status_code = 400, detail = 'User not found' )
    
    #   Check if email already exists
    if user_edit_profile.newEmail != user['email']:
        if collection.find_one( { 'email' : user_edit_profile.newEmail }, { '_id' : 0 } ):
            raise HTTPException( status_code = 400, detail = 'Email already exists.' )
    
    #   Update user profile
    collection.update_one( { 'userID' : user_edit_profile.userID }, { '$set' : {
        'email' : user_edit_profile.newEmail,
        'firstName' : user_edit_profile.newFirstName,
        'lastName' : user_edit_profile.newLastName,
        'telephoneNumber' : user_edit_profile.newTelephoneNumber,
    } } )

    return { 'result' : 'success' }

#   Get User Profile
@app.get('/profile/{userID}', tags=['Users'])
def get_user_profile( userID: str ):
    '''
        Get user profile
        Input: userID (str)
        Output: userInfo (dict)
    '''

    #   Connect to MongoDB
    collection = db['User']

    #   Check if userID exists
    user = collection.find_one( { 'userID' : userID }, { '_id' : 0 } )
    if not user:
        raise HTTPException( status_code = 400, detail = 'User not found' )
    
    userInfo = {
        'email' : user['email'],
        'firstName' : user['firstName'],
        'lastName' : user['lastName'],
        'telephoneNumber' : user['telephoneNumber'],
    }

    return userInfo

#   Reset Password
@app.post('/reset_password', tags=['Users'])
def user_reset_password( user_reset_password: User_Reset_Password ):
    '''
        User Reset Password
        Input: user_reset_password (User_Reset_Password)
        Output: result (dict)
    '''

    #   Connect to MongoDB
    collection = db['User']

    #   Check if userID exists
    user = collection.find_one( { 'userID' : user_reset_password.userID }, { '_id' : 0 } )
    if not user:
        raise HTTPException( status_code = 400, detail = 'User not found' )
    
    #   Check if old password is incorrect
    password_hash, _ = hash_password( user_reset_password.oldPassword, user['salt'] )
    if password_hash != user['password_hash']:
        raise HTTPException( status_code = 400, detail = 'Old password is incorrect' )

    #   Hash password
    password_hash, password_salt = hash_password( user_reset_password.newPassword )
    
    #   Update password
    collection.update_one( { 'userID' : user_reset_password.userID }, { '$set' : {
        'password_hash' : password_hash,
        'salt' : password_salt,
    } } )

    return { 'result' : 'success' }

#   Post Reserve Ticket
@app.post('/reserve_ticket', tags=['Users'])
def post_reserve_ticket( reserved_ticket: ReservedTicket ):
    '''
        Post reserve ticket
        Input: reserved_ticket (ReservedTicket)
        Output: result (dict)
    '''

    #   Connect to MongoDB
    user_collection = db['User']
    event_collection = db['Events']
    ticket_collection = db['Ticket']
    transaction_collection = db['TicketTransaction']

    #   Check if userID exists
    user = user_collection.find_one( { 'userID' : reserved_ticket.userID }, { '_id' : 0 } )
    if not user:
        raise HTTPException( status_code = 400, detail = 'User not found' )
    
    #   Check if eventID exists
    event = event_collection.find_one( { 'eventID' : reserved_ticket.eventID }, { '_id' : 0 } )
    if not event:
        raise HTTPException( status_code = 400, detail = 'Event not found' )

    #   Check if wrong ticket class
    for i in range( len( event['ticketClass'] ) ):
        if event['ticketClass'][i]['className'] == reserved_ticket.className:
            break
        if i == len( event['ticketClass'] ) - 1:
            raise HTTPException( status_code = 400, detail = 'Wrong ticket class' )
        
    #   Check if no seatNo
    if len( reserved_ticket.seatNo ) == 0:
        raise HTTPException( status_code = 400, detail = 'Please select seat' )
    
    #   Check if seatNo is already taken or wrong seatNo
    #       Loop find ticketClass
    if reserved_ticket.seatNo[0] != '':
        for ticketClass in event['ticketClass']:
            if ticketClass['className'] == reserved_ticket.className:
                for seatNo in reserved_ticket.seatNo:
                    if seatNo not in ticketClass['seatNo']:
                        raise HTTPException( status_code = 400, detail = f'{seatNo} Seat not found' )
                    if ticketClass['seatNo'][seatNo] != 'vacant':
                        raise HTTPException( status_code = 400, detail = f'{seatNo} Seat already taken' )
                break
    
    #   Reserve ticket
    #       Loop find ticketClass
    for ticketClass in event['ticketClass']:
        if ticketClass['className'] == reserved_ticket.className:
            for seatNo in reserved_ticket.seatNo:
                event_collection.update_one( { 'eventID' : reserved_ticket.eventID }, { '$set' : {
                    f'ticketClass.{i}.seatNo.{seatNo}' : 'reserved'
                } } )
            break

    return { 'result' : 'success' }

#   Post Cancel Reserve Ticket
@app.post('/cancel_reserve_ticket', tags=['Users'])
def post_cancel_reserve_ticket( reserved_ticket: ReservedTicket ):
    '''
        Post cancel reserve ticket
        Input: reserved_ticket (ReservedTicket)
        Output: result (dict)
    '''

    #   Connect to MongoDB
    user_collection = db['User']
    event_collection = db['Events']
    ticket_collection = db['Ticket']
    transaction_collection = db['TicketTransaction']

    #   Check if userID exists
    user = user_collection.find_one( { 'userID' : reserved_ticket.userID }, { '_id' : 0 } )
    if not user:
        raise HTTPException( status_code = 400, detail = 'User not found' )
    
    #   Check if eventID exists
    event = event_collection.find_one( { 'eventID' : reserved_ticket.eventID }, { '_id' : 0 } )
    if not event:
        raise HTTPException( status_code = 400, detail = 'Event not found' )

    #   Check if wrong ticket class
    for i in range( len( event['ticketClass'] ) ):
        if event['ticketClass'][i]['className'] == reserved_ticket.className:
            break
        if i == len( event['ticketClass'] ) - 1:
            raise HTTPException( status_code = 400, detail = 'Wrong ticket class' )
        
    #   Check if no seatNo
    if len( reserved_ticket.seatNo ) == 0:
        raise HTTPException( status_code = 400, detail = 'Please select seat' )
    
    #   Check if seatNo is not reserved or wrong seatNo
    #       Loop find ticketClass
    if reserved_ticket.seatNo[0] != '':
        for ticketClass in event['ticketClass']:
            if ticketClass['className'] == reserved_ticket.className:
                for seatNo in reserved_ticket.seatNo:
                    if seatNo not in ticketClass['seatNo']:
                        raise HTTPException( status_code = 400, detail = f'{seatNo} Seat not found' )
                    if ticketClass['seatNo'][seatNo] != 'reserved':
                        raise HTTPException( status_code = 400, detail = f'{seatNo} Seat not reserved' )
                break
    
    #   Cancel reserve ticket
    #       Loop find ticketClass
    for ticketClass in event['ticketClass']:
        if ticketClass['className'] == reserved_ticket.className:
            for seatNo in reserved_ticket.seatNo:
                event_collection.update_one( { 'eventID' : reserved_ticket.eventID }, { '$set' : {
                    f'ticketClass.{i}.seatNo.{seatNo}' : 'vacant'
                } } )
            break
    
    return { 'result' : 'success' }

#   Post New Ticket
@app.post('/post_ticket', tags=['Users'])
def post_new_ticket( new_ticket: NewTicket ):
    '''
        Post new ticket
        Input: new_ticket (NewTicket)
        Output: result (dict)
    '''

    #   Connect to MongoDB
    user_collection = db['User']
    event_collection = db['Events']
    ticket_collection = db['Ticket']
    transaction_collection = db['TicketTransaction']

    #   Check if userID exists
    user = user_collection.find_one( { 'userID' : new_ticket.userID }, { '_id' : 0 } )
    if not user:
        raise HTTPException( status_code = 400, detail = 'User not found' )
    
    #   Check if eventID exists
    event = event_collection.find_one( { 'eventID' : new_ticket.eventID }, { '_id' : 0 } )
    if not event:
        raise HTTPException( status_code = 400, detail = 'Event not found' )

    #   Check if wrong ticket class
    for i in range( len( event['ticketClass'] ) ):
        if event['ticketClass'][i]['className'] == new_ticket.className:
            break
        if i == len( event['ticketClass'] ) - 1:
            raise HTTPException( status_code = 400, detail = 'Wrong ticket class' )
        
    #   Check if no seatNo
    if len( new_ticket.seatNo ) == 0:
        raise HTTPException( status_code = 400, detail = 'Please select seat' )
    
    #   Check if ticket amount is enough
    #       Loop find ticketClass
    for ticketClass in event['zoneRevenue']:
        if ticketClass['className'] == new_ticket.className:
            if ticketClass['ticketSold'] + len( new_ticket.seatNo ) > ticketClass['quota']:
                raise HTTPException( status_code = 400, detail = 'Ticket amount is not enough' )
            break

    #   Check if seatNo is already taken or wrong seatNo
    #       Loop find ticketClass
    if new_ticket.seatNo[0] != '':
        for ticketClass in event['ticketClass']:
            if ticketClass['className'] == new_ticket.className:
                for seatNo in new_ticket.seatNo:
                    if seatNo not in ticketClass['seatNo']:
                        raise HTTPException( status_code = 400, detail = f'{seatNo} Seat not found' )
                    if ticketClass['seatNo'][seatNo] != 'reserved':
                        raise HTTPException( status_code = 400, detail = f'{seatNo} Seat already taken' )
                break

    #   Get validDatetime and expiredDatetime
    validDatetime = datetime.datetime.now()
    expiredDatetime = datetime.datetime.now()
    #       Loop find ticketClass
    for ticketClass in event['ticketClass']:
        if ticketClass['className'] == new_ticket.className:
            validDatetime = ticketClass['validDatetime']
            expiredDatetime = ticketClass['expiredDatetime']
            break
    
    cou = 0
    #   Loop for each seatNo
    for seatNo in new_ticket.seatNo:

        #   Update Counter
        cou = cou + 1

        #   Generate ticketID
        ticketID = generate_ticketID( new_ticket.eventID, new_ticket.userID, new_ticket.className, seatNo )

        #   Insert ticket to database
        newTicket = Ticket(
            ticketID = ticketID,
            validDatetime = validDatetime,
            expiredDatetime = expiredDatetime,
            status = 'available',
            seatNo = seatNo,
            className = new_ticket.className,
            eventID = new_ticket.eventID,
            userID = new_ticket.userID,
            eventName = event['eventName'],
            eventImage = event['posterImage'],
            location = event['location'],
            runNo = event['soldTicket'] + cou,
        )
        ticket_collection.insert_one( newTicket.dict() )

        #   Add transaction
        newTransaction = {
            'ticketID' : ticketID,
            'timestamp' : datetime.datetime.now(),
            'transactionType' : 'created'
        }
        transaction_collection.insert_one( newTransaction )

    #   Update Event ticketClass
    #       Loop find ticketClass
    for i in range( len( event['ticketClass'] ) ):
        ticketClass = event['ticketClass'][i]
        if ticketClass['className'] == new_ticket.className and new_ticket.seatNo[0] != '':
            for seatNo in new_ticket.seatNo:
                event_collection.update_one( { 'eventID' : new_ticket.eventID }, { '$set' : {
                    f'ticketClass.{i}.seatNo.{seatNo}' : 'available'
                } } )
            break

    #   Update ticket amount
    #       Loop find ticketClass
    totalPrice = 0
    for i in range( len( event['zoneRevenue'] ) ):
        ticketClass = event['zoneRevenue'][i]
        if ticketClass['className'] == new_ticket.className:
            event['zoneRevenue'][i]['ticketSold'] += len( new_ticket.seatNo )
            totalPrice = len( new_ticket.seatNo ) * ticketClass['price']
            break

    #   Update event ticket
    event_collection.update_one( { 'eventID' : new_ticket.eventID }, { '$set' : {
        'soldTicket' : event['soldTicket'] + len( new_ticket.seatNo ),
        'zoneRevenue' : event['zoneRevenue'],
        'totalRevenue' : event['totalRevenue'] + totalPrice
    } } )

    return { 'result' : 'success' }

#   Transfer Ticket to Another User by UserEmail
@app.post('/transfer_ticket/{srcUserID}/{ticketID}/{dstUserEmail}', tags=['Users'])
def transfer_ticket( srcUserID: str, ticketID: str, dstUserEmail: str ):
    '''
        Transfer ticket to another user by userEmail
        Input: srcUserID (str), ticketID (str), dstUserEmail (str)
        Output: result (dict)
    '''

    #   Connect to MongoDB
    user_collection = db['User']
    ticket_collection = db['Ticket']
    transaction_collection = db['TicketTransaction']

    #   Check if srcUserID exists
    srcUser = user_collection.find_one( { 'userID' : srcUserID }, { '_id' : 0 } )
    if not srcUser:
        raise HTTPException( status_code = 400, detail = 'User not found' )
    
    #   Check if dstUserEmail exists
    dstUser = user_collection.find_one( { 'email' : dstUserEmail }, { '_id' : 0 } )
    if not dstUser:
        raise HTTPException( status_code = 400, detail = 'User not found' )
    
    #   Check if ticketID exists
    ticket = ticket_collection.find_one( { 'ticketID' : ticketID }, { '_id' : 0 } )
    if not ticket:
        raise HTTPException( status_code = 400, detail = 'Ticket not found' )
    
    #   Check if ticket belongs to srcUserID
    if ticket['userID'] != srcUserID:
        raise HTTPException( status_code = 400, detail = 'Ticket does not belong to you' )
    
    #   Check if ticket can be transferred
    if ticket['status'] != 'available':
        raise HTTPException( status_code = 400, detail = 'Ticket cannot be transferred' )
    
    #   Check if ticket is expired
    if ticket['expiredDatetime'] < datetime.datetime.now():
        #   Update ticket status to expired
        ticket_collection.update_one( { 'ticketID' : ticketID }, { '$set' : {
            'status' : 'expired'
        } } )
        #   Add transaction
        newTransaction = {
            'ticketID' : ticketID,
            'timestamp' : datetime.datetime.now(),
            'transactionType' : 'expired'
        }
        transaction_collection.insert_one( newTransaction )
        raise HTTPException( status_code = 400, detail = 'Ticket is expired' )
    
    #   Create new ticket
    newTicketID = generate_ticketID( ticket['eventID'], dstUser['userID'], ticket['className'], ticket['seatNo'] )
    newTicket = Ticket(
        ticketID = newTicketID,
        validDatetime = ticket['validDatetime'],
        expiredDatetime = ticket['expiredDatetime'],
        status = 'available',
        seatNo = ticket['seatNo'],
        className = ticket['className'],
        eventID = ticket['eventID'],
        userID = dstUser['userID'],
        eventName = ticket['eventName'],
        eventImage = ticket['eventImage'],
        location = ticket['location'],
        runNo = ticket['runNo']
    )
    ticket_collection.insert_one( newTicket.dict() )

    #   Update ticket status to transferred
    ticket_collection.update_one( { 'ticketID' : ticketID }, { '$set' : {
        'status' : 'transferred'
    } } )

    #   Add transaction
    newTransaction1 = {
        'ticketID' : newTicketID,
        'timestamp' : datetime.datetime.now(),
        'transactionType' : 'received',
        'srcUserID' : srcUserID
    }
    newTransaction2 = {
        'ticketID' : ticketID,
        'timestamp' : datetime.datetime.now(),
        'transactionType' : 'transferred',
        'dstUserID' : dstUser['userID']
    }
    transaction_collection.insert_one( newTransaction1 )
    transaction_collection.insert_one( newTransaction2 )

    returnObj = {
        'ticketID' : newTicketID,
        'firstName' : dstUser['firstName'],
        'lastName' : dstUser['lastName'],
        'eventName' : ticket['eventName'],
        'location' : ticket['location'],
        'posterImage' : ticket['eventImage'],
        'date' : ticket['validDatetime'].strftime( '%d %B %Y' ),
        'zone' : ticket['className'],
        'row' : ticket['seatNo'].split( '-' )[0],
        'seat' : ticket['seatNo'].split( '-' )[-1],
        'gate' : '-',
    }
    return returnObj

#   Event Organizer Sign Up
@app.post('/eo_signup', tags=['Event Organizer'])
def eo_signup( eo_signup: EO_Signup ):
    ''' 
        Event Organizer Sign up
        Input: eo_signup (EO_Signup)
        Output: result (dict)
    '''

    #   Connect to MongoDB
    collection = db['EventOrganizer']

    #   Check if email already exists
    if collection.find_one( { 'email' : eo_signup.email }, { '_id' : 0 } ):
        raise HTTPException( status_code = 400, detail = 'Email already exists.' )
    
    #   Generate organizerID
    genOrganizerID = generate_organizerID( eo_signup.email )

    #   Hash password
    password_hash, password_salt = hash_password( eo_signup.password )
    
    #   Insert user to database
    newEO = EventOrganizer(
        organizerID = genOrganizerID,
        email = eo_signup.email,
        organizerName = eo_signup.organizerName,
        organizerPhone = eo_signup.organizerPhone,
        password_hash = password_hash,
        salt = password_salt,
    )
    collection.insert_one( newEO.dict() )
    
    return { 'result' : 'success' }

#   Event Organizer Signin
@app.post('/eo_signin', tags=['Event Organizer'])
def eo_signin( eo_signin: EO_Signin ):
    '''
        Event Organizer Signin
        Input: eo_signin (EO_Signin)
        Output: eoInfo (dict)
    '''

    #   Connect to MongoDB
    collection = db['EventOrganizer']

    #   Check if email exists
    eo = collection.find_one( { 'email' : eo_signin.email }, { '_id' : 0 } )
    if not eo:
        raise HTTPException( status_code = 400, detail = 'Email or Password incorrect' )
    
    #   Hash password
    password_hash, _ = hash_password( eo_signin.password, eo['salt'] )

    #   Check if password is correct
    if password_hash != eo['password_hash']:
        raise HTTPException( status_code = 400, detail = 'Email or Password incorrect' )
    
    eoInfo = {
        'organizerID' : eo['organizerID'],
        'email' : eo['email'],
        'name' : eo['organizerName'],
    }
    
    return eoInfo

#   Get All Events by Event Organizer
@app.get('/eo_event/{organizerID}', tags=['Event Organizer'])
def get_eo_event( organizerID: str ):
    '''
        Get all events by event organizer
        Input: organizerID (str)
        Output: events (list)
    '''

    #   Connect to MongoDB
    eo_collection = db['EventOrganizer']
    event_collection = db['Events']

    #   Check if organizerID exists
    eo = eo_collection.find_one( { 'organizerID' : organizerID }, { '_id' : 0 } )
    if not eo:
        raise HTTPException( status_code = 400, detail = 'Organizer not found' )
    
    eoName = eo['organizerName']

    #   Get all events
    events = list( event_collection.find( { 'organizerName' : eoName }, { '_id' : 0 } ) )

    status_order = { 'Draft' : 0, 'On-going' : 1, 'Expired' : 2 }

    #   Sort events by status
    sortedEvents = sorted( events, key = lambda i: (status_order[i['eventStatus']], i['startDateTime']) )

    #   Get current datetime
    currentDatetime = datetime.datetime.now()

    #   Loop for each event
    for event in sortedEvents:

        #   Check if event is expired
        if event['endDateTime'] < currentDatetime and event['eventStatus'] == 'On-going':
            #   Update event status to expired
            event_collection.update_one( { 'eventID' : event['eventID'] }, { '$set' : {
                'eventStatus' : 'Expired'
            } } )
            event['eventStatus'] = 'Expired'

    return sortedEvents

#   Get All Ticket Sold by Event Organizer and Event ID
@app.get('/eo_get_all_ticket_sold/{eventID}', tags=['Event Organizer'])
def get_all_ticket_sold( eventID: str ):
    '''
        Get all tickets sold by event organizer and eventID
        Input: eventID (str)
        Output: tickets (list)
    '''

    #   Connect to MongoDB
    event_collection = db['Events']
    
    #   Check if eventID exists
    event = event_collection.find_one( { 'eventID' : eventID }, { '_id' : 0 } )
    if not event:
        raise HTTPException( status_code = 400, detail = 'Event not found' )
    
    returnDict = {
        'totalRevenue' : event['totalRevenue'],
        'ticketSold' : event['soldTicket'],
        'ticketTotal' : event['totalTicket'],
    }

    return returnDict

#   Post Create Event by Event Organizer
@app.post('/eo_create_event/{organizerID}', tags=['Event Organizer'])
def post_create_event( organizerID: str ):
    '''
        Post create event by event organizer
        Input: organizerID (str)
        Output: result (dict)
    '''

    #   Connect to MongoDB
    eo_collection = db['EventOrganizer']
    event_collection = db['Events']

    #   Check if organizerID exists
    eo = eo_collection.find_one( { 'organizerID' : organizerID }, { '_id' : 0 } )
    if not eo:
        raise HTTPException( status_code = 400, detail = 'Organizer not found' )

    #   Generate eventID
    eventID = generate_eventID()

    #   Insert event to database
    newEvent = Event(
        eventID = eventID,
        eventName = '',
        startDateTime = datetime.datetime.now(),
        endDateTime = datetime.datetime.now(),
        onSaleDateTime = datetime.datetime.now(),
        endSaleDateTime = datetime.datetime.now(),
        location = '',
        info = '',
        featured = False,
        eventStatus = 'Draft',
        tagName = [],
        posterImage = '',
        seatImage = '',
        organizationName = eo['organizerName'],
        staff = [],
        ticketType = '',
        ticketClass = [],
        organizerName = eo['organizerName'],
        timeStamp = datetime.datetime.now(),
        totalTicket = 0,
        soldTicket = 0,
        totalTicketValue = 0,
        totalRevenue = 0,
        zoneRevenue = [],
        bankAccount = BankAccount(
            bank = '',
            accountName = '',
            accountType = '',
            accountNo = '',
            branch = ''
        ),
        organizerEmail = eo['email']
    )
    event_collection.insert_one( newEvent.dict() )

    return eventID

#   Delete Event by Event Organizer and Event ID
@app.delete('/eo_delete_event/{organizerID}/{eventID}', tags=['Event Organizer'])
def delete_event( organizerID: str, eventID: str ):
    '''
        Delete event by event organizer and eventID
        Input: organizerID (str), eventID (str)
        Output: result (dict)
    '''

    #   Connect to MongoDB
    eo_collection = db['EventOrganizer']
    event_collection = db['Events']

    #   Check if organizerID exists
    eo = eo_collection.find_one( { 'organizerID' : organizerID }, { '_id' : 0 } )
    if not eo:
        raise HTTPException( status_code = 400, detail = 'Organizer not found' )
    
    #   Check if eventID exists
    event = event_collection.find_one( { 'eventID' : eventID }, { '_id' : 0 } )
    if not event or event['organizerName'] != eo['organizerName']:
        raise HTTPException( status_code = 400, detail = 'Event not found' )

    #   Check if event is Draft
    if event['eventStatus'] != 'Draft':
        raise HTTPException( status_code = 400, detail = 'Event is not Draft' )
    
    #   Delete event
    event_collection.delete_one( { 'eventID' : eventID } )

    return { 'result' : 'success' }

#   Post Publish Event by Event Organizer and Event ID
@app.post('/eo_publish_event/{organizerID}/{eventID}', tags=['Event Organizer'])
def post_publish_event( organizerID: str, eventID: str ):
    '''
        Post publish event by event organizer and eventID
        Input: organizerID (str), eventID (str)
        Output: result (dict)
    '''

    #   Connect to MongoDB
    eo_collection = db['EventOrganizer']
    event_collection = db['Events']

    #   Check if organizerID exists
    eo = eo_collection.find_one( { 'organizerID' : organizerID }, { '_id' : 0 } )
    if not eo:
        raise HTTPException( status_code = 400, detail = 'Organizer not found' )
    
    #   Check if eventID exists
    event = event_collection.find_one( { 'eventID' : eventID }, { '_id' : 0 } )
    if not event or event['organizerName'] != eo['organizerName']:
        raise HTTPException( status_code = 400, detail = 'Event not found' )
    
    #   Check if event is Draft
    if event['eventStatus'] != 'Draft':
        raise HTTPException( status_code = 400, detail = 'Event is not Draft' )
    
    #   Check if event is ready to publish
    if event['eventName'] == '' or event['location'] == '' or event['info'] == '' or event['posterImage'] == '' or len( event['tagName'] ) == 0 or len( event['ticketClass'] ) == 0:
        raise HTTPException( status_code = 400, detail = 'Event is not ready to publish' )
    
    #   Check if event date is past
    if event['startDateTime'] < datetime.datetime.now():
        raise HTTPException( status_code = 400, detail = 'Event date is past' )

    #   Update event status to On-going
    event_collection.update_one( { 'eventID' : eventID }, { '$set' : {
        'eventStatus' : 'On-going'
    } } )

    return { 'result' : 'success' }

#   Post Event Setting
@app.post('/eo_event_setting/{organizerID}/{eventID}', tags=['Event Organizer'])
def post_event_setting( organizerID: str, eventID: str, eventSetting: EventSetting ):
    '''
        Post event setting by event organizer and eventID
        Input: organizerID (str), eventID (str), eventSetting (EventSetting)
        Output: result (dict)
    '''

    #   Connect to MongoDB
    eo_collection = db['EventOrganizer']
    event_collection = db['Events']

    #   Check if organizerID exists
    eo = eo_collection.find_one( { 'organizerID' : organizerID }, { '_id' : 0 } )
    if not eo:
        raise HTTPException( status_code = 400, detail = 'Organizer not found' )
    
    #   Check if eventID exists
    event = event_collection.find_one( { 'eventID' : eventID }, { '_id' : 0 } )
    if not event or event['organizerName'] != eo['organizerName']:
        raise HTTPException( status_code = 400, detail = 'Event not found' )
    
    #   Check if event is Draft
    if event['eventStatus'] != 'Draft':
        raise HTTPException( status_code = 400, detail = 'Event is not Draft' )
    
    #   Check if eventSetting is empty
    for key in eventSetting.dict():
        if key == 'tagName' and len( eventSetting.dict()[key] ) == 0:
            raise HTTPException( status_code = 400, detail = f'{key} is empty' )
        elif eventSetting.dict()[key] == '':
            raise HTTPException( status_code = 400, detail = f'{key} is empty' )
    
    #   Check if eventSetting is wrong
    if eventSetting.startDateTime > eventSetting.endDateTime or eventSetting.onSaleDateTime > eventSetting.endSaleDateTime:
        raise HTTPException( status_code = 400, detail = 'Start/Onsale Time After End/Endsale Time' )
    
    #   Check if eventSetting is wrong
    if eventSetting.endDateTime < eventSetting.endSaleDateTime:
        raise HTTPException( status_code = 400, detail = 'End Time Before Endsale Time' )
    
    #   Update event setting
    event_collection.update_one( { 'eventID' : eventID }, { '$set' : {
        'eventName' : eventSetting.eventName,
        'startDateTime' : eventSetting.startDateTime,
        'endDateTime' : eventSetting.endDateTime,
        'onSaleDateTime' : eventSetting.onSaleDateTime,
        'endSaleDateTime' : eventSetting.endSaleDateTime,
        'location' : eventSetting.location,
        'info' : eventSetting.info,
        'posterImage' : eventSetting.posterImage,
        'tagName' : eventSetting.tagName,
        'ticketType' : eventSetting.ticketType,
        'seatImage' : eventSetting.seatImage
    } } )

    return { 'result' : 'success' }

#   Post Create New Ticket Type by Event Organizer and Event ID
@app.post('/eo_create_ticket_type/{organizerID}/{eventID}', tags=['Event Organizer'])
def post_create_ticket_type( organizerID: str, eventID: str, ticketType: NewTicketClass ):
    '''
        Post create new ticket type by event organizer and eventID
        Input: organizerID (str), eventID (str)
        Output: result (dict)
    '''

    #   Connect to MongoDB
    eo_collection = db['EventOrganizer']
    event_collection = db['Events']

    #   Check if organizerID exists
    eo = eo_collection.find_one( { 'organizerID' : organizerID }, { '_id' : 0 } )
    if not eo:
        raise HTTPException( status_code = 400, detail = 'Organizer not found' )
    
    #   Check if eventID exists
    event = event_collection.find_one( { 'eventID' : eventID }, { '_id' : 0 } )
    if not event or event['organizerName'] != eo['organizerName']:
        raise HTTPException( status_code = 400, detail = 'Event not found' )
    
    #   Check if ticketType already exists
    for ticketClass in event['ticketClass']:
        if ticketClass['className'] == ticketType.className:
            raise HTTPException( status_code = 400, detail = 'Ticket type already exists' )
        
    #   Check if ticketType is empty
    if ticketType.amountOfSeat == 0:
        raise HTTPException( status_code = 400, detail = 'Ticket quntity is empty' )
    
    #   Check if ticketType is negative
    if ticketType.amountOfSeat < 0 or ticketType.pricePerSeat < 0:
        raise HTTPException( status_code = 400, detail = 'Ticket quntity is negative' )
    
    #   Check if ticketType is wrong
    if ticketType.rowNo * ticketType.columnNo != ticketType.amountOfSeat and ticketType.rowNo != 0 and ticketType.columnNo != 0:
        raise HTTPException( status_code = 400, detail = 'rowNo x columnNo not equal amountOfSeat' )
    
    #   Check if ticketType is wrong
    if (ticketType.rowNo == 0 and ticketType.columnNo != 0) or (ticketType.rowNo != 0 and ticketType.columnNo == 0):
        raise HTTPException( status_code = 400, detail = 'rowNo or columnNo = 0' )

    #   Check if ticketType is wrong
    if ticketType.validDatetime > ticketType.expiredDatetime:
        raise HTTPException( status_code = 400, detail = 'Valid Time After Expired Time' )
    
    #   Check if event is Draft
    if event['eventStatus'] != 'Draft':
        raise HTTPException( status_code = 400, detail = 'Event is not Draft' )
    
    #   Create seatNo
    seatNo = {}
    for i in range( ticketType.rowNo ):
        for j in range( ticketType.columnNo ):
            seatNo[f'{i+1}-{j+1}'] = 'vacant'
    
    #   Create ticketClass
    ticketType = TicketClass(
        className = ticketType.className,
        pricePerSeat = ticketType.pricePerSeat,
        amountOfSeat = ticketType.amountOfSeat,
        rowNo = ticketType.rowNo,
        columnNo = ticketType.columnNo,
        seatNo = seatNo,
        validDatetime = ticketType.validDatetime,
        expiredDatetime = ticketType.expiredDatetime,
        zoneSeatImage = ticketType.zoneSeatImage
    )

    #   Insert ticketType to database
    event_collection.update_one( { 'eventID' : eventID }, { '$push' : { 'ticketClass' : ticketType.dict() } } )
    event_collection.update_one( { 'eventID' : eventID }, { '$push' : { 'zoneRevenue' : ZoneRevenue(
        className = ticketType.className,
        price = ticketType.pricePerSeat,
        ticketSold = 0,
        quota = ticketType.amountOfSeat,
    ).dict() } } )

    #   Update totalTicket
    event_collection.update_one( { 'eventID' : eventID }, { '$set' : {
        'totalTicket' : event['totalTicket'] + ticketType.amountOfSeat
    } } )

    return { 'result' : 'success' }

#   Delete Ticket Type by Event Organizer and Event ID
@app.post('/eo_delete_ticket_type/{organizerID}/{eventID}/{className}', tags=['Event Organizer'])
def delete_ticket_type( organizerID: str, eventID: str, className: str ):
    '''
        Delete ticket type by event organizer and eventID
        Input: organizerID (str), eventID (str), className (str)
        Output: result (dict)
    '''

    #   Connect to MongoDB
    eo_collection = db['EventOrganizer']
    event_collection = db['Events']

    #   Check if organizerID exists
    eo = eo_collection.find_one( { 'organizerID' : organizerID }, { '_id' : 0 } )
    if not eo:
        raise HTTPException( status_code = 400, detail = 'Organizer not found' )
    
    #   Check if eventID exists
    event = event_collection.find_one( { 'eventID' : eventID }, { '_id' : 0 } )
    if not event or event['organizerName'] != eo['organizerName']:
        raise HTTPException( status_code = 400, detail = 'Event not found' )
    
    #   Check if className exists
    for ticketClass in event['ticketClass']:
        if ticketClass['className'] == className:
            break
        if ticketClass['className'] == event['ticketClass'][-1]['className']:
            raise HTTPException( status_code = 400, detail = 'Ticket type not found' )
        
    #   Check if event is Draft
    if event['eventStatus'] != 'Draft':
        raise HTTPException( status_code = 400, detail = 'Event is not Draft' )
        
    #   Delete ticketType
    event_collection.update_one( { 'eventID' : eventID }, { '$pull' : { 'ticketClass' : { 'className' : className } } } )
    event_collection.update_one( { 'eventID' : eventID }, { '$pull' : { 'zoneRevenue' : { 'className' : className } } } )

    #   Update totalTicket
    event_collection.update_one( { 'eventID' : eventID }, { '$set' : {
        'totalTicket' : event['totalTicket'] - ticketClass['amountOfSeat']
    } } )

    #   Update totalTicketValue
    event_collection.update_one( { 'eventID' : eventID }, { '$set' : {
        'totalTicketValue' : event['totalTicketValue'] - ticketClass['amountOfSeat'] * ticketClass['pricePerSeat']
    } } )

    return { 'result' : 'success' }

#   Get All Staff by Event Organizer and Event ID
@app.get('/eo_get_all_staff/{organizerID}/{eventID}', tags=['Event Organizer'])
def get_all_staff( organizerID: str, eventID: str ):
    '''
        Get all staff by event organizer and eventID
        Input: organizerID (str), eventID (str)
        Output: staffs (list)
    '''

    #   Connect to MongoDB
    eo_collection = db['EventOrganizer']
    event_collection = db['Events']
    user_collection = db['User']

    #   Check if organizerID exists
    eo = eo_collection.find_one( { 'organizerID' : organizerID }, { '_id' : 0 } )
    if not eo:
        raise HTTPException( status_code = 400, detail = 'Organizer not found' )
    
    #   Check if eventID exists
    event = event_collection.find_one( { 'eventID' : eventID }, { '_id' : 0 } )
    if not event or event['organizerName'] != eo['organizerName']:
        raise HTTPException( status_code = 400, detail = 'Event not found' )
    
    staffs = []
    for staff in event['staff']:
        user = user_collection.find_one( { 'userID' : staff }, { '_id' : 0 } )
        staffs.append( user )

    return staffs

#   Add Staff to Event by Event Organizer and Event ID
@app.post('/eo_add_staff/{organizerID}/{eventID}/{staffEmail}', tags=['Event Organizer'])
def add_staff( organizerID: str, eventID: str, staffEmail: str ):
    '''
        Add staff to event by event organizer and eventID
        Input: organizerID (str), eventID (str), staffEmail (str)
        Output: result (dict)
    '''

    #   Connect to MongoDB
    eo_collection = db['EventOrganizer']
    event_collection = db['Events']
    user_collection = db['User']

    #   Check if organizerID exists
    eo = eo_collection.find_one( { 'organizerID' : organizerID }, { '_id' : 0 } )
    if not eo:
        raise HTTPException( status_code = 400, detail = 'Organizer not found' )
    
    #   Check if eventID exists
    event = event_collection.find_one( { 'eventID' : eventID }, { '_id' : 0 } )
    if not event or event['organizerName'] != eo['organizerName']:
        raise HTTPException( status_code = 400, detail = 'Event not found' )
    
    #   Check if staffEmail exists
    user = user_collection.find_one( { 'email' : staffEmail }, { '_id' : 0 } )
    if not user:
        raise HTTPException( status_code = 400, detail = 'Staff not found' )
    
    #   Check if staff already in event
    if user['userID'] in event['staff']:
        raise HTTPException( status_code = 400, detail = 'Staff already in event' )
    
    #   Add staff to event
    event_collection.update_one( { 'eventID' : eventID }, { '$push' : { 'staff' : user['userID'] } } )

    #   Add event to staff
    user_collection.update_one( { 'email' : staffEmail }, { '$push' : { 'event' : eventID } } )

    return { 'result' : 'success' }

#   Remove Staff from Event by Event Organizer and Event ID
@app.post('/eo_remove_staff/{organizerID}/{eventID}/{staffEmail}', tags=['Event Organizer'])
def remove_staff( organizerID: str, eventID: str, staffEmail: str ):
    '''
        Remove staff from event by event organizer and eventID
        Input: organizerID (str), eventID (str), staffEmail (str)
        Output: result (dict)
    '''

    #   Connect to MongoDB
    eo_collection = db['EventOrganizer']
    event_collection = db['Events']
    user_collection = db['User']

    #   Check if organizerID exists
    eo = eo_collection.find_one( { 'organizerID' : organizerID }, { '_id' : 0 } )
    if not eo:
        raise HTTPException( status_code = 400, detail = 'Organizer not found' )
    
    #   Check if eventID exists
    event = event_collection.find_one( { 'eventID' : eventID }, { '_id' : 0 } )
    if not event or event['organizerName'] != eo['organizerName']:
        raise HTTPException( status_code = 400, detail = 'Event not found' )
    
    #   Check if staffID exists
    user = user_collection.find_one( { 'email' : staffEmail }, { '_id' : 0 } )
    if not user:
        raise HTTPException( status_code = 400, detail = 'Staff not found' )
    
    #   Check if staff not in event
    if user['userID'] not in event['staff']:
        raise HTTPException( status_code = 400, detail = 'Staff not in event' )
    
    #   Remove staff from event
    event_collection.update_one( { 'eventID' : eventID }, { '$pull' : { 'staff' : user['userID'] } } )

    #   Remove event from staff
    user_collection.update_one( { 'email' : staffEmail }, { '$pull' : { 'event' : eventID } } )

    return { 'result' : 'success' }

#   Post Bank Account by Event Organizer and Event ID
@app.post('/eo_post_bank_account/{organizerID}/{eventID}', tags=['Event Organizer'])
def post_bank_account( organizerID: str, eventID: str, bankAccount: BankAccount ):
    '''
        Post bank account by event organizer and eventID
        Input: organizerID (str), eventID (str), bankAccount (BankAccount)
        Output: result (dict)
    '''

    #   Connect to MongoDB
    eo_collection = db['EventOrganizer']
    event_collection = db['Events']

    #   Check if organizerID exists
    eo = eo_collection.find_one( { 'organizerID' : organizerID }, { '_id' : 0 } )
    if not eo:
        raise HTTPException( status_code = 400, detail = 'Organizer not found' )
    
    #   Check if eventID exists
    event = event_collection.find_one( { 'eventID' : eventID }, { '_id' : 0 } )
    if not event or event['organizerName'] != eo['organizerName']:
        raise HTTPException( status_code = 400, detail = 'Event not found' )
    
    #   Update bank account
    event_collection.update_one( { 'eventID' : eventID }, { '$set' : { 'bankAccount' : bankAccount.dict() } } )

    return { 'result' : 'success' }

#   Scan Ticket
@app.post('/scanner/{eventID}/{ticketID}', tags=['Staff'])
def scan_ticket( eventID: str, ticketID: str ):
    '''
        Scan ticket
        Input: eventID (str), ticketID (str)
        Output: result (dict)
    '''

    #   Connect to MongoDB
    collection = db['Ticket']
    transaction_collection = db['TicketTransaction']

    #   Check if ticketID exists
    ticket = collection.find_one( { 'ticketID' : ticketID }, { '_id' : 0 } )
    if not ticket:
        raise HTTPException( status_code = 400, detail = 'Ticket not found' )
    
    #   Check if wrong event
    if ticket['eventID'] != eventID:
        raise HTTPException( status_code = 400, detail = 'Wrong event' )
    
    #   Check if ticket is already scanned
    if ticket['status'] == 'scanned':
        raise HTTPException( status_code = 400, detail = 'Ticket already scanned' )
    
    #   Check if ticket is expired
    if ticket['status'] == 'expired':
        raise HTTPException( status_code = 400, detail = 'Ticket expired' )
    
    #   Check if ticket is transferred
    if ticket['status'] == 'transferred':
        raise HTTPException( status_code = 400, detail = 'Ticket transferred' )
    
    #   Check validDatetime
    if ticket['validDatetime'] > datetime.datetime.now():
        raise HTTPException( status_code = 400, detail = 'Ticket not valid yet' )
    
    #   Check expiredDatetime
    if ticket['expiredDatetime'] < datetime.datetime.now():
        #   Update ticket status to expired
        collection.update_one( { 'ticketID' : ticketID }, { '$set' : {
            'status' : 'expired'
        } } )
        raise HTTPException( status_code = 400, detail = 'Ticket expired' )
    
    #   Update ticket status
    if ticket['status'] == 'available':
        collection.update_one( { 'ticketID' : ticketID }, { '$set' : { 'status' : 'scanned' } } )

    #   Add transaction
    newTransaction = {
        'ticketID' : ticketID,
        'timestamp' : datetime.datetime.now(),
        'transactionType' : 'scanned',
    }
    transaction_collection.insert_one( newTransaction )

    return ticket

#   Get Ticket by Ticket ID
@app.get('/ticket/{ticketID}', tags=['Staff'])
def get_ticket( ticketID: str ):
    '''
        Get ticket by ticketID
        Input: ticketID (str)
        Output: ticket (dict)
    '''

    #   Connect to MongoDB
    collection = db['Ticket']

    #   Check if ticketID exists
    ticket = collection.find_one( { 'ticketID' : ticketID }, { '_id' : 0 } )
    if not ticket:
        raise HTTPException( status_code = 400, detail = 'Ticket not found' )
    
    return ticket

#   Get Schedule
@app.get('/staff_event/{userID}', tags=['Staff'])
def get_staff_event( userID: str ):
    '''
        Get staff events
        Input: userID (str)
        Output: events (list)
    '''

    #   Connect to MongoDB
    userCollection = db['User']
    eventCollection = db['Events']

    #   Get user events
    user = userCollection.find_one( { 'userID' : userID }, { '_id' : 0 } )
    if not user:
        raise HTTPException( status_code = 400, detail = 'User not found' )
    
    eventID = user['event']

    events = []
    for event in eventID:
        currentEvent = eventCollection.find_one( { 'eventID' : event }, { '_id' : 0 } )
        #   Check if event is Expired
        if currentEvent['eventStatus'] == 'Expired':
            #   Remove event from staff
            userCollection.update_one( { 'userID' : userID }, { '$pull' : { 'event' : event } } )
            continue

        events.append( currentEvent )

    sortedEvents = sorted( events, key = lambda i: i['startDateTime'] )

    return sortedEvents