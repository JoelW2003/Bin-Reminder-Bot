# bot.py

import discord # IMPORT DISCORD.PY. ALLOWS ACCESS TO DISCORD'S API.
import os # IMPORT THE OS MODULE.
import sqlite3
import time
from datetime import datetime, date
from dotenv import load_dotenv # IMPORT LOAD_DOTENV FUNCTION FROM DOTENV MODULE.
from discord.ext import commands, tasks # IMPORT COMMANDS FROM THE DISCORD.EXT MODULE.


load_dotenv() # LOADS THE .ENV FILE THAT RESIDES ON THE SAME LEVEL AS THE SCRIPT.
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN") # GRAB THE API TOKEN FROM THE .ENV FILE.

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents = intents) # CREATES A NEW BOT OBJECT WITH A SPECIFIED PREFIX. 

conn = None
conn = sqlite3.connect('rent.db') # Connect to rent database
cur = conn.cursor() 

@bot.event
async def on_ready():
    print(bot.user.name + " is here!")
    binLoop.start()

reminder_channel_id = 1086391871439384686

monthDays = {
    "01":31,
    "02":28,  # Assumes not a leap year for February
    "03":31,
    "04":30,
    "05":31,
    "06":30,
    "07":31,
    "08":31,
    "09":30,
    "10":31,
    "11":30,
    "12":31
}


#?##############################  UTILITY FUNCTIONS  ###############################


def format_date(date):
    """
    Formats the given date to dd-mm-yyyy.

    Args:
        date (str): date of rent payment due (yyyy-mm-dd)

    Returns:
        formated_date (str): Formatted date using (dd-mm-yyyy) 
    """    
    str_as_date = datetime.strptime(date, "%Y-%m-%d")
    formated_date = str_as_date.strftime("%d-%m-%Y")
    return (formated_date)


def get_next_rent():
    """
    Returns the details of the next rent payment due.

    Returns:
        next_rent (list): Date and amount due for next rent payment
    """    
    today = date.today()
    cur.execute("SELECT * FROM rent_payments")
    entries = cur.fetchall()
    next_rent = nextEntry(entries, today, 0)
    return (next_rent)


def get_next_bin():
    """
    Returns the next bin collection.

    Returns:
        next_rent (list): Date and type for next bin collection
    """    
    today = date.today()
    cur.execute("SELECT * FROM bin_collections")
    collectionEntries = cur.fetchall()
    next_bin = nextEntry(collectionEntries, today, 0)
    return (next_bin)


def nextEntry(entries, dateToday, format):
    """
    Iterates through entries, retrieves those with dates later than
    today. Sorts this list to return the first (and therefore next due)
    entry.

    Args:
        entries (list): list of entries ~ (date, info) from bin / rent db
        td (date): todays' date ~ YYYY-MM-DD
        form (int): desired return format (0 == next due entry, 1 == 
                    all future entries)
        
    Returns:
        next (list): Next upcoming entry (bin/rent) from date
    """    
    upcomingEntries = []
    for entry in entries:
        entryDate = datetime.strptime(entry[0], '%Y-%m-%d')
        if entryDate.date() > dateToday:
            upcomingEntries.append(entry)
    sortedUpcoming = sorted(upcomingEntries)
    
    if format == 0:
        next = sortedUpcoming[0]
        return(next) 
    elif format == 1:
        return(sortedUpcoming)
    return("Invalid type input!")


#?##############################  BOT LOOPS  ###############################


@tasks.loop(seconds=30)
async def binLoop():
    """
    Checks next bin collection due every loop, sending a reminder at 7PM evening before
    a bin collection is due.
    """    
    channel = bot.get_channel(reminder_channel_id)  
    currentDate = datetime.now()  # FORMAT: YYYY-MM-DD HH:MM:SS 
    currentDay = currentDate.strftime("%d")  
    currentMonth = currentDate.strftime("%m") 
    
    nextBin = get_next_bin()  # Format (String date, String type)
    binDate = nextBin[0]
    binType = nextBin[1]
    
    binDayT = datetime.strptime(format_date(binDate), '%d-%m-%Y')  # Get day of next bin collection
    dayOfNextCollection = binDayT.strftime("%d")
    
    if(int(currentDay) == (int(dayOfNextCollection)-1) or 
       (dayOfNextCollection == "01" and currentDay == monthDays[currentMonth] )): 
        currentTime = currentDate.strftime("%H:%M")
        if (currentTime == '19:00'):  
            await channel.send("@everyone Reminder, **" + binType + "** is being collected tomorrow on **" 
                               + format_date(binDate) + "**")
            time.sleep(70)  # Sleep to avoid multiple reminders
        
        
#?##############################  BOT COMMANDS  ###############################


# Command !next_rent. This takes 0 arguments from the user and prints the next due rent into the channel.
@bot.command(
	help  = "Prints the next rent payment due back to the channel.",  # Adds to '!help next_rent' message
	brief = "Prints the next rent payment due back to the channel."   # Adds to '!help' message
)
async def next_rent(ctx):
    """
    Prints the next rent payment due.

    Args:
        ctx (Class): Represents the context in which a command is being invoked under.
    """    
    rent_details = get_next_rent()
    await ctx.channel.send("The next rent is due on: **" + format_date(rent_details[0]) + 
                           "** (dd-mm-yyyy) for **£" + str(rent_details[1]) + "**")


# Command !all_rent. This takes 0 arguments from the user and prints all future rent payments into the channel.
@bot.command(
	help="Prints all remaining rent payment due back to the channel.",  # Adds to '!help all_rent' message
	brief="Prints all remaining rent payment due back to the channel."  # Adds to '!help' message
)
async def all_rent(ctx):
    """
    Prints all remaining rent payments.

    Args:
        ctx (Class): Represents the context in which a command is being invoked under.
    """    
    today = date.today()
    cur.execute("SELECT * FROM rent_payments WHERE date_due > " + str(today))
    rows = cur.fetchall()
    rents = nextEntry(rows, today, 1)  # 1 == all future entries
    for rent in rents:
        await ctx.channel.send("Rent due: **" + format_date(rent[0]) + "** (dd-mm-yyyy) for **£" + str(rent[1]) + "**")


# Command !next_bin. This takes 0 arguments from the user and prints the next due bin collection into the channel.
@bot.command(
	help  = "Prints the next rent bin collection back to the channel.",  # Adds to '!help next_bin' message
	brief = "Prints the next rent bin collection back to the channel."   # Adds to '!help' message
)
async def next_bin(ctx):
    """
    Prints the next bin collection due.

    Args:
        ctx (Class): Represents the context in which a command is being invoked under.
    """    
    bin_details = get_next_bin()
    await ctx.channel.send("The next bin collection is **" + str(bin_details[1])  + "** collected on **" 
                           + format_date(bin_details[0]) + "** (dd-mm-yyyy)")
    
    
# Command !all_bins. This takes 0 arguments from the user and prints all future bin collections into the channel.
@bot.command(
	help="Prints all future bin collections back to the channel.",  # Adds to '!help all_bin' message
	brief="Prints all future bin collections back to the channel."  # Adds to '!help' message
)
async def all_bins(ctx):
    """
    Prints all bin collections.

    Args:
        ctx (Class): Represents the context in which a command is being invoked under.
    """    
    today = date.today()
    cur.execute("SELECT * FROM bin_collections WHERE collection_day > " + str(today))
    rows = cur.fetchall()
    bins = nextEntry(rows, today, 1)  # 1 == all future entries
    for bin in bins:
        await ctx.channel.send(str(bin[1] + " collected on " + format_date(bin[0])))


bot.run(DISCORD_TOKEN)  # Executes the bot with the specified token.