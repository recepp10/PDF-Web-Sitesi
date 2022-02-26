from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import SubmitField
from pdfminer.converter import TextConverter
import io 

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage

class RegisterForm(Form):
    name=StringField("Ad Soayd")
    username=StringField("Kullanıcı Adı")
    email=StringField("Email")
    password=PasswordField ("Parola",validators=[
        validators.DataRequired(message = "Lütfen parola belirleyiniz.."),
        validators.EqualTo(fieldname="confirm",message="Parolanız uyuşmuyor")
    ])
    confirm=PasswordField("Parola Doğrula")

class LoginForm(Form):
    username=StringField("Kullanıcı Adı:")
    password=PasswordField("Parola:")

class AdminForm(Form):
    ausername=StringField("Kullanıcı Adı:")
    apassword=PasswordField("Parola:")    


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_admin" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için yönetici girişi yapınız.","danger")
            return redirect(url_for("admin"))

    return decorated_function



app=Flask(__name__)
app.secret_key="pdfblog"

app.config["MYSQL_HOST"]="localhost"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="pdfblog"
app.config["MYSQL_CURSORCLASS"]="DictCursor"



mysql=MySQL(app)

@app.route("/")
def index():
    return render_template("index.html")
@app.route("/about")
def about():
    return render_template("about.html")
@app.route("/dashboard")
@login_required
def dashboard():
    cursor=mysql.connection.cursor()
    sorgu="Select * From pdfs "
    result=cursor.execute(sorgu)

    if result > 0:
        pdfs=cursor.fetchall()
        return render_template("dashboard.html",pdfs=pdfs)
    else:
        return render_template("dashboard.html") 

@app.route("/userview")
@login_required
def userview():
    cursor=mysql.connection.cursor()
    sorgu="Select * From users"
    result=cursor.execute(sorgu)

    if result > 0:
        users=cursor.fetchall()
        return render_template("userview.html",users=users)
    else:
        
     return render_template("userview.html")  

@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor=mysql.connection.cursor()
    sorgu="Select * From admins "
    result=cursor.execute(sorgu)

    if result > 0:
        sorgu2="Delete from users where id=%s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for("userview"))
        
    else:
        
     flash("Bu işleme yetkiniz yok..","danger")
     return redirect(url_for("index"))




    

    
      


   
#KAYIT İŞLEMİ
@app.route("/register",methods=["GET","POST"])
def register():
    form=RegisterForm(request.form)

    if request.method=="POST" and form.validate():
        name=form.name.data
        username=form.username.data
        email=form.email.data
        password=sha256_crypt.encrypt(form.password.data)

        cursor=mysql.connection.cursor()
        sorgu="Insert into users(name,username,email,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,username,email,password))
        mysql.connection.commit()
        cursor.close()
        flash("Kullanıcı başarıyla eklendi..","success") 

        return redirect(url_for("index"))

    else:
        return render_template("register.html",form=form) 


#KULLANICI GİRİŞİ
@app.route("/login",methods=["GET","POST"])
def login():
    form=LoginForm(request.form)
    if request.method=="POST":
        username=form.username.data
        password_enter=form.password.data

        cursor=mysql.connection.cursor()
        sorgu="SELECT * from users where username=%s"
        result=cursor.execute(sorgu,(username,))

        if result > 0:
            data=cursor.fetchone()
            real_password=data["password"]
            if sha256_crypt.verify(password_enter,real_password):
                flash("Başarıyla giriş yaptınız..","success")
                session["logged_in"]=True
                session["username"]=username

                return redirect(url_for("index"))
            else:
                flash("Parolanızı yanlış girdiniz..","danger")

        else:
            flash("Böyle bir kullanıcı bulunmuyor..","danger")
            return redirect(url_for("login"))
           

    return render_template("login.html",form=form)



#YÖNETİCİ GİRİŞİ
@app.route("/admin",methods=["GET","POST"])
def admin():
    form=AdminForm(request.form)
    if request.method=="POST":
        ausername=form.ausername.data
        apassword_enter=form.apassword.data  

        cursor=mysql.connection.cursor()
        sorgu="SELECT * from admins where ausername=%s"
        result=cursor.execute(sorgu,(ausername,))

        if result > 0:
            data=cursor.fetchone()
            areal_password=data["apassword"]
            if form.validate ():
                apassword_enter=areal_password
                session["logged_admin"]=True
                session["ausername"]=ausername

                flash("Başarıyla giriş yaptınız..","success")
                return redirect(url_for("index"))
            else:
                flash("Parolanızı yanlış girdiniz..","danger")

        else:
            flash("Böyle bir yönetici bulunmuyor..","danger")
            return redirect(url_for("admin"))
           

    return render_template("admin.html",form=form)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/adminlogout")
def adminlogout():
    session.clear()
    return redirect(url_for("index"))  

@app.route("/addpdf",methods=["GET","POST"])
def addpdf():
    form=PdfForm(request.form)
    if request.method=="POST" and form.validate() :
        file = request.files['file']
        file.save((file.filename))
        title=form.title.data
        text=form.text.data
        projeozeti=form.projeozeti.data
        anahtar=form.anahtar.data
        öğrencino=form.öğrencino.data
        öğrencino2=form.öğrencino2.data
        dersadi=form.dersadi.data
        tarih=form.tarih.data
        öğretimtürü=form.öğretimtürü.data
        öğretimtürü2=form.öğretimtürü2.data
        baslik=form.baslik.data
        öğrenciad=form.öğrenciad.data
        öğrenciad2=form.öğrenciad2.data
        
        
        dönem=form.dönem.data
        

        inPDFfile=file.filename
        outTXTFile='denemePDF.txt'  
        pdf2txt(inPDFfile,outTXTFile)
        fihrist = open("denemePDF.txt", 'r', encoding='utf-8')
        text = fihrist.read()
        #text = text.strip()  
        #print(text)

        x = text.index("ÖZET")+4 
        y = text.index("Anahtar")

        projeozeti=text[x:y]
        projeozeti = projeozeti.strip()

        x = text.index("Anahtar  kelimeler:")
        y = text.find("ix")

        anahtar = text[x:y]
        anahtar = anahtar.strip()

        x = text.index("Öğrenci No")
        y = text.index("Adı")
        öğrencino=text[x:y]
        

        x=text.rfind("Öğrenci No")
        y=text. rfind("Adı")
        öğrencino2=text[x:y]

        x = text.index("Adı")
        y = text.index("İmza")
        öğrenciad=text[x:y]
        

        x=text.rfind("Adı")
        y=text. rfind("İmza")
        öğrenciad2=text[x:y]

        

      

        x=text.index("Tarih:")+5
        y=text. rfind("GİRİŞ")
        tarih=text[x:y]

        x=text.index("Tarih:")+10
        y=text. index("Tarih")+12
        dönem=text[x:y]

        if dönem=="09" or dönem=="10" or dönem=="11" or dönem=="12" or dönem=="01":
            dönem="Güz Dönemi"
        else:
            dönem="Bahar Dönemi"    

        

        x=text.index("Öğrenci No")+17
        y=text. index("Öğrenci No")+18
        öğretimtürü=text[x:y]

        x=text.rfind("İmza:")+35
        y=text.rfind("ÖZET")
        baslik=text[x:y]
        


          

        x=text.rfind("Öğrenci No:")+17
        y=text.rfind("Öğrenci No:")+18
        öğretimtürü2=text[x:y]

        if "BİTİRME PROJESİ" in text:
            dersadi="BİTİRME PROJESİ"
        else:
            dersadi="ARAŞTIRMA PROBLEMLERİ"    


        
        



        

        
      
        cursor=mysql.connection.cursor()
        sorgu = "Insert into pdfs (gonderici,title,projeozeti,anahtar,öğrencino,öğrencino2,dersadi,tarih,öğretimtürü,öğretimtürü2,baslik,öğrenciad,öğrenciad2,dönem) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        
        cursor.execute(sorgu,(session["username"],title,projeozeti,anahtar,öğrencino,öğrencino2,dersadi,tarih,öğretimtürü,öğretimtürü2,baslik,öğrenciad,öğrenciad2,dönem))
       
        mysql.connection.commit()
        cursor.close()
        flash("PDF başarıyla eklendi","success")
        


    return render_template("addpdf.html",form=form)

class PdfForm(Form):
    title=StringField("Başlık")
    text=TextAreaField("İçerik")
    projeozeti=TextAreaField("Özet")
    anahtar=TextAreaField("Anahtar Kelimeler")  
    öğrencino=TextAreaField("Öğrenci No")
    öğrencino2=TextAreaField("Öğrenci No")
    dersadi=TextAreaField("Ders Adı")
    tarih=TextAreaField("Tarih")
    öğretimtürü=TextAreaField("Öğretim Türü")
    öğretimtürü2=TextAreaField("Öğretim Türü")
    baslik=TextAreaField("Başlık")
    öğrenciad=TextAreaField("Öğrenci Adı")
    öğrenciad2=TextAreaField("Öğrenci Adı")
    
    
    dönem=TextAreaField("Dönem")
    
     

@app.route("/pdfs")
def pdfs():
    cursor=mysql.connection.cursor()
    sorgu="Select * From pdfs where gonderici=%s"
    result=cursor.execute(sorgu,(session["username"],))

    if result > 0:
        pdfs=cursor.fetchall()
        return render_template("pdfs.html",pdfs=pdfs)
    else:
        return render_template("pdfs.html")

@app.route("/pdf/<string:id>")
def pdf(id):
    cursor=mysql.connection.cursor()
    sorgu="Select * From pdfs where id=%s"
    result=cursor.execute(sorgu,(id,))

    if result > 0:
        pdf=cursor.fetchone()
        return render_template("pdf.html",pdf=pdf)
    else:
        return render_template("pdf.html")  




@app.route("/search",methods=["GET","POST"])
def search():
    if request.method=="GET":
        return redirect(url_for("index"))
    else:
        keyword=request.form.get("keyword")  
        cursor=mysql.connection.cursor()
        sorgu="Select * From pdfs where title like '%"+keyword+"%'"
        result=cursor.execute(sorgu)
        if result ==0:
            flash("Aranan kelimeye uygun pdf bulunumadı","danger")
            return redirect(url_for("pdfs"))
        else:
            pdfs=cursor.fetchall()
            return render_template("pdfs.html",pdfs=pdfs)    

      

def pdf2txt(inPDFfile,outTXTFile):
    i=0
    infile=open(inPDFfile,'rb')
    resMgr=PDFResourceManager()
    retData=io.StringIO()
    TxtConverter=TextConverter(resMgr,retData,laparams=LAParams())
    interpreter=PDFPageInterpreter(resMgr,TxtConverter)
    for page in PDFPage.get_pages(infile):
      if i==2 or i==11 or i==9 or i==12:  
        interpreter.process_page(page)
      i+=1
    txt=retData.getvalue()

    with open(outTXTFile,'w',encoding=" utf-8") as f:
        f.write(txt)
    
    
      


    




if __name__=="__main__":
    app.run(debug=True)
    