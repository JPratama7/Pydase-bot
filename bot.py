import random

import telebot
import mysql.connector
import configparser
import datetime

#configparser
config = configparser.ConfigParser()
config.read("setting.ini")

#config token
API_TOKEN = config["bot"]["token"]
bot = telebot.TeleBot(API_TOKEN)

#config database
user = config["db"]["user"]
password = ""
database = config["db"]["database"]

#Setting SQL
try:
    db = mysql.connector.connect(user=user, password=password, database=database, autocommit=True)
    sql = db.cursor()
except:
    with open("logbot.txt", "a") as log:
        log.write("DB ERROR")


def checkuser(telegramid):
    sql.execute(f"SELECT tele_id FROM user WHERE tele_id ={telegramid}")
    user = sql.fetchall()
    if len(user) == 1:
        return True
    else:
        return False

def checkbarang(idbarang):
    barang_id = int(idbarang)
    sql.execute("SELECT id_barang FROM barang WHERE id_barang ='%s'" % (barang_id))
    barang = sql.fetchall()
    if len(barang) == 1:
           return True
    return False

def idorder(idbarang,idorang):
    now = datetime.datetime.now()
    seq = now.strftime("%Y%m%d%H%M")
    stridorang = str(idorang)
    stridbarang = str(idbarang)
    idorder = int(seq+stridorang+stridbarang)
    return idorder
    
def isadmin(idtelegram):
    sql.execute("SELECT tele_id FROM admin WHERE tele_id ='%s'" % (idtelegram))
    admin = sql.fetchall()
    if len(admin) == 1:
        return True
    else:
        return False
    
def log(message):
    perintah = message.text
    tanggal = datetime.datetime.now()
    tanggal = tanggal.strftime('%d-%B-%Y')
    nama_awal = message.chat.first_name
    nama_akhir = message.chat.last_name
    id_user = message.chat.id
    text_log = f"{tanggal}, {id_user}, {nama_awal}, {nama_akhir}, {perintah}"
    log_bot = open('logbot.txt','a')
    log_bot.write(text_log)
    log_bot.close()

# welcome message handler
@bot.message_handler(commands=["start"])
def send_welcome(message):
    log(message)
    bot.reply_to(message, "  Halo Selamat Datang. Silahkan ketik /help untuk menemukan perintah")

# @bot.message_handler(
#     func=lambda message: message.text is not None
# )
# def message_list(message):
#     bot.reply_to(message, "Tolong Ikuti Perintah")

#Handler Perintah order
@bot.message_handler(commands=["order"])
def order(message):
    log(message)
    no_id = int(message.chat.id)
    if checkuser(no_id):
        bot.send_message(no_id, "ANDA TERDAFTAR, OK LANJUT")
        #try expect to fix value and index error
        try:
            text = message.text.split(" ")
            barang = int(text[1])
            if checkbarang(barang):
                sql.execute(f"SELECT harga FROM barang WHERE id_barang ={barang}")
                hargabarang = sql.fetchall()
                harga = int(hargabarang[0][0])
                jmlh = int(text[2])
                kode = idorder(barang,no_id)
                waktu = datetime.datetime.now()
                total = jmlh*harga
                insert = "INSERT INTO list_order(id_order,tele_id,barang,jmlh, total, created_at, status) VALUES (%s,%s,%s,%s,%s,%s,%s)"
                val = (kode, no_id, barang, jmlh, total, waktu,"pending")
                sql.execute(insert, val)
                db.commit()
                bot.send_message(no_id, "OK BARANG BERHASIL DIPESAN")
            else:
                bot.send_message(no_id, "Barang tidak tersedia")
        except IndexError:
            bot.send_message(no_id, "FORMAT SALAH")
        except ValueError:
            bot.send_message(no_id, "SALAH ANGKA KAO BODAT")
    else:
        bot.send_message(
            no_id, "DAFTAR DULU BOUSS. KETIK /daftar untuk melakukan pendaftaran"
        )
    

#Handler Perintah list
@bot.message_handler(commands=["list"])
def product_list(message):
    log(message)
    chat_id = message.chat.id
    sql.execute("SELECT id_barang, nama, harga FROM barang")
    barang = sql.fetchall()
    for x in barang:
        id_barang = x[0]
        nama = x[1]
        harga = x[2]
        pesan = "ID BARANG : %s\nNAMA BARANG : %s\nHARGA BARANG : Rp.%s\n" % (id_barang, nama, harga)
        bot.send_message(chat_id, pesan)
    
#Handler Perintah daftar
@bot.message_handler(commands=["daftar"])
def daftar(message):
    log(message)
    chat_id = message.chat.id
    if checkuser(chat_id):
        bot.send_message(chat_id,"BLOK KAN LU DAH DAFTAR")
    else:
        try:
            text = str(message.text)
            identitas = text.split(",")
            nama = identitas[1]
            alamat = identitas[2]
            insert = "INSERT INTO user (tele_id,nama,alamat) VALUES (%s,%s,%s)"
            val = (chat_id, nama, alamat)
            sql.execute(insert, val)
            db.commit()
            bot.send_message(chat_id,"OK COCOTE ANDA SUDAH TERDAFTAR")
        except IndexError:
            bot.send_message(chat_id, "SALAH FORMAT PAOK")
        
#handler help
@bot.message_handler(commands=["help"])
def help(message):
    log(message)
    bot.reply_to(message,"SELAMAT DATANG KE BOT KAMI\n\n"
                         "Untuk melakukan pendaftaran silakan ketik sesuai format /daftar, nama, alamat\n\n"
                         "Untuk mengecek list kode barang barang silakan ketik /list\n\n"
                         "untuk melakukan pengorderan silahkan ketik sesuai format /order barang banyak barang\n\n")


#handler  orderlist
@bot.message_handler(commands=["orderlist"])
def orderlist(message):
    log(message)
    tele_id = int(message.chat.id)
    sql.execute("SELECT list_order.id_order,user.nama,barang.nama,list_order.total,list_order.jmlh,list_order.created_at FROM list_order INNER JOIN user ON list_order.tele_id = user.tele_id INNER JOIN barang ON list_order.barang = barang.id_barang WHERE list_order.tele_id = %s" % (tele_id))
    data = sql.fetchall()
    for datauser in data:
        id_order = datauser[0]
        nama_user = datauser[1]
        nama_barang = datauser[2]
        total = datauser[3]
        jmlah = datauser[4]
        tanggal = datauser[5]
        pesan = "ID ORDER = %s\nNama User = %s\nNama Barang = %s\nTotal Pembelian = %s\nJumlah Pembelian = %s\nTanggal Pemesanan = %s\n" % (id_order,nama_user,nama_barang,total,jmlah,tanggal)
        bot.send_message(tele_id,pesan)
    

#handler  cancel
@bot.message_handler(commands=["cancel"])
def cancel(message):
    log(message)
    tele_id = int(message.chat.id)
    try:
        text = str(message.text)
        split = text.split(" ")
        id_cancel = split[1]
        sql.execute("SELECT list_order.id_order,user.nama,barang.nama,list_order.total,list_order.jmlh,list_order.created_at FROM list_order INNER JOIN user ON list_order.tele_id = user.tele_id INNER JOIN barang ON list_order.barang = barang.id_barang WHERE list_order.tele_id = %s AND list_order.id_order = %s" % (tele_id, id_cancel))
        data = sql.fetchall()
        datauser = data[0]
        id_order = datauser[0]
        nama_user = datauser[1]
        nama_barang = datauser[2]
        total = datauser[3]
        jmlah = datauser[4]
        tanggal = datauser[5]
        pesan = "ID ORDER = %s\nNama User = %s\nNama Barang = %s\nTotal Pembelian = %s\nJumlah Pembelian = %s\nTanggal Pemesanan = %s\n" % (
        id_order, nama_user, nama_barang, total, jmlah, tanggal)
        bot.send_message(tele_id, pesan)
        sql.execute(f"DELETE FROM list_order WHERE id_order = {id_cancel} AND tele_id = {tele_id}")
    except IndexError:
        bot.send_message(tele_id, "Hayolow Mau ngapain :|")
    
#handler laporan
@bot.message_handler(commands="laporan")
def laporan(message):
    log(message)
    tele_id = int(message.chat.id)
    text = message.text.split(" ")
    tanggal = text[1]
    gabungan = f"{tanggal} 00:00"
    if isadmin(tele_id):
        sql.execute(f"SELECT list_order.id_order,user.nama,barang.nama,list_order.total,list_order.jmlh,list_order.created_at, list_order.status FROM list_order INNER JOIN user ON list_order.tele_id = user.tele_id INNER JOIN barang ON list_order.barang = barang.id_barang WHERE list_order.created_at > '{gabungan}' ")
        data = sql.fetchall()
        if data != 0:
            for datauser in data:
                id_order = int(datauser[0])
                nama_user = datauser[1]
                nama_barang = datauser[2]
                total = datauser[3]
                jmlah = datauser[4]
                tanggal = datauser[5]
                status = str(datauser[6])
                pesan = f"ID ORDER = {id_order}\nNama User = {nama_user}\nNama Barang = {nama_barang}\nTotal Pembelian = {total}\nJumlah Pembelian = {jmlah}\nTanggal Pemesanan = {tanggal}\nStatus = {status}\n"
                bot.send_message(tele_id,pesan)
        else:
            bot.send_message(tele_id, "belum ada pesanan")
    else:
        bot.reply_to(message,"Not Authorize")
    
#handler verify
@bot.message_handler(commands="verif")
def verif(message):
    log(message)
    tele_id = int(message.chat.id)
    if isadmin(tele_id):
        try:
            text = message.text.split(" ")
            id_order = int(text[1])
            kondisi = str(text[2]).lower()
            sql.execute(f"SELECT * FROM list_order WHERE id_order={id_order}")
            check = sql.fetchall()
            if check != None:
                if kondisi == "lunas":
                    sql.execute(f"UPDATE list_order SET status = 'lunas' WHERE id_order = {id_order}")
                    bot.send_message(tele_id,"OKEH, DONE")

                elif kondisi == "pending":
                    sql.execute(f"UPDATE list_order SET status = 'pending' WHERE id_order = {id_order}")
                    bot.send_message(tele_id,"OKEH, DONE")

                elif kondisi == "terkirim":
                    sql.execute(f"UPDATE list_order SET status = 'terkirim' WHERE id_order = {tele_id}")
                    bot.send_message(tele_id,"OKEH, DONE")
                else:
                    bot.send_message(tele_id,"Ndak Paham bos")
            else:
                bot.send_message(tele_id, "Order Tidak ditemukan")
        except IndexError:
            bot.send_message(tele_id, "Salah Format")
        except ValueError:
            bot.send_message(tele_id, "Salah Isi itu oe")
    else:
        bot.send_message(tele_id,"SAPA LU ANJER")
    
@bot.message_handler(content_types=['photo'])
def image(message):
    tele_id = message.chat.id
    fileID = message.photo[-1].file_id
    fileInfo = bot.get_file(fileID)
    downloaded_file = bot.download_file(fileInfo.file_path)
    try:
        text = str(message.caption).lower()
        pesan = text.split(" ")
        if pesan[0] == "pembayaran":
            query = f"(INSERT INTO pembayaran VALUES({tele_id},{downloaded_file})"
            sql.execute(query)
            bot.send_message(tele_id,"Done Uploaded")
        else:
            bot.send_message(tele_id,"OK :|")
    except ValueError:
        bot.send_message(tele_id, "Isi Captionya pack :|")

@bot.message_handler(commands=["foto"])
def photo(message):
    tele_id = message.chat.id
    sql.execute(f"SELECT * FROM pembayaran")
    data = sql.fetchall()
    for datauser in data:
        id_pembayaran = datauser[0]
        gambar = datauser[1]
        bot.send_photo(tele_id,gambar,id_pembayaran)

print("bot is berlari")
bot.polling()
