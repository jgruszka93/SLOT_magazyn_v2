import hashlib
import sys
import datetime

from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QFont, QLinearGradient, QColor, QPolygonF, QBrush, QPen
from PyQt5.QtWidgets import QApplication

import slotbaza
from gui import UI_widget, LoginDialog, Dialog, InputDialog, QuestionDialog

settings = {}
with open('data/settings.cfg') as settingsfile:
    for line in settingsfile:
        try:
            (key, val) = line.split('=')
            key = key.strip()
            val = val.strip()
            settings[key] = val
        except ValueError:
            pass


def hashpassword(password):
    code = hashlib.md5(password.encode('utf-8')).hexdigest()
    return code


def barcodetoid(barcode, typ):
    codetxt = barcode[-3:]
    try:
        code = int(codetxt)
        if typ == 'int':
            return code
        elif typ == 'string':
            codetxt2 = str(code)
            return codetxt2
        else:
            pass
    except:
        pass


def idtobarcode(code, typ):
    year = settings['year']
    if typ == 'area':
        typcode = '10'
    elif typ == 'item':
        typcode = '20'
    elif typ == 'orch':
        typcode = '30'
    elif typ == 'user':
        typcode = '40'
    else:
        pass
    try:
        stringid = str(code)
    except:
        try:
            int(code)
            stringid = code
        except:
            pass
    elementcode = stringid.zfill(3)
    barcode = year + typcode + elementcode
    return barcode
    pass


def barcodevalcheck(code, typ):
    year = settings['year']
    if typ == 'area':
        typcode = '10'
    elif typ == 'item':
        typcode = '20'
    elif typ == 'orch':
        typcode = '30'
    elif typ == 'user':
        typcode = '40'
    else:
        pass
    if code == '':
        status = 1
        statustxt = 'Nie wprowadzono żadnego kodu!'
    else:
        if len(code) == 9:
            if code[0:4] == year:
                if code[4:6] == typcode:
                    status = 0
                    statustxt = 'Wprowadzono właściwy kod'
                else:
                    status = 4
                    statustxt = 'Wprowadzono kod niewłaściwego typu!'
            else:
                status = 3
                statustxt = "Wprowadzono kod z innego roku!"
        else:
            status = 2
            statustxt = 'Wprowadzono niewłaściwy kod!'
    return (status, statustxt)


class Magazyn(UI_widget):

    def __init__(self):
        super().__init__()
        self.setupUI()
        self.loginstatus = False
        self.username = 'user'
        self.usertype = 'user'
        self.logstatus.setText("<FONT COLOR=\'#FF4444\'> Niezalogowany")
        self.rysujobszary()

        # Połączenie przycisków z odpowiednimi funkcjami
        self.btn_login.clicked.connect(self.logowanie)
        self.btn_logout.clicked.connect(self.logowanie)
        self.btn_addarea.clicked.connect(self.rysujobszary)
        self.btn_areaedit.clicked.connect(self.wyczyscscene)
        self.btn_comein.clicked.connect(self.comein)
        self.btn_comeout.clicked.connect(self.comeout)

    # Moduł logowania do programu
    def logowanie(self):
        sender = self.sender()
        # jeśli wysyłającym jest przycisk ZALOGUJ
        if sender.objectName() == 'btn_login':
            login, haslo, ok = LoginDialog.getloginhaslo(self)
            if ok:
                if slotbaza.isuserexist(login):
                    if slotbaza.loginvalidate(login, hashpassword(haslo))['login']:
                        self.loginstatus = True
                        # self.usertype = slotbaza.loginvalidate(login, hashpassword(haslo))['usertype']
                        self.logstatus.setText("<FONT COLOR=\'#44FF44\'> Zalogowany")
                        Dialog.komunikat('ok', 'Pomyślnie zalogowano do systemu', self)
                    else:
                        Dialog.komunikat('warn', 'Logowanie nieudane! Niepoprawne hasło.', self)
                else:
                    Dialog.komunikat('warn', 'Użytkownik o podanym loginie nie istnieje.', self)
            else:
                pass
        # jeśli wysyłającym jest przycisk WYLOGUJ
        elif sender.objectName() == 'btn_logout':
            if self.loginstatus:
                self.loginstatus = False
                self.usertype = 'user'
                self.logstatus.setText("<FONT COLOR=\'#FF4444\'> Niezalogowany")
                Dialog.komunikat('ok', 'Pomyślnie wylogowano z systemu', self)
            else:
                Dialog.komunikat('warn', 'Nie można się wylogować nie będąc wcześniej zalogowanym', self)

    def comein(self):
        areabarcode, areaok = InputDialog.komunikat('barcode', 'Wczytaj kod obszaru:', self)
        if areaok:
            areastatus, areastatustxt = barcodevalcheck(areabarcode, 'area')
            if areastatus == 0:
                areaid = barcodetoid(areabarcode, 'int')
                if slotbaza.isareaexist(areaid):
                    kolejnyprzedmiot = True
                    while kolejnyprzedmiot:
                        kolejnyprzedmiot = False
                        itembarcode, itemok = InputDialog.komunikat('barcode', 'Wczytaj kod przedmiotu:', self)
                        if itemok:
                            itemstatus, itemstatustxt = barcodevalcheck(itembarcode, 'item')
                            if itemstatus == 0:
                                itemid = barcodetoid(itembarcode, 'int')
                                if slotbaza.isitemexist(itemid):
                                    przedmiot = slotbaza.loaditem(itemid)
                                    if przedmiot['itemstate']:
                                        Dialog.komunikat('error', 'Ten przedmiot jest już przyjęty na stan magazynu! '
                                                                  'Jeśli nie wiesz dlaczego, wezwij szefa ekipy!', self)
                                    else:
                                        istniejacyprzedmiotok = QuestionDialog.pytanie('Ten przedmiot znajduje się '
                                                                                       'w bazie:\nNazwa przedmiotu: '
                                                                                       + przedmiot['itemname']
                                                                                       + '\nStan: Wydany\nUwagi: '
                                                                                       + przedmiot['itemcomments']
                                                                                       + '\n\nCzy chcesz przyjąć '
                                                                                         'przedmiot?', self)
                                        if istniejacyprzedmiotok:
                                            przedmiot['itemstate'] = True
                                            przedmiot['dateoflastincome'] = datetime.datetime.now()
                                            przedmiot['useroflastincome'] = self.username
                                            slotbaza.saveitem(przedmiot)
                                            Dialog.komunikat('ok', 'Przedmiot został przyjęty na stan magazynu', self)
                                            kolejnyprzedmiot = QuestionDialog.pytanie('Czy chcesz przyjąć '
                                                                                      'kolejny przedmiot do obszaru'
                                                                                      ' ' + str(areaid) + '?', self)
                                        else:
                                            Dialog.komunikat('warn', 'Przerwano proces przyjmowania przedmiotu.'
                                                                     '\nPrzedmiot nie został przyjęty', self)
                                else:
                                    nowyprzedmiotok = QuestionDialog.pytanie(
                                        'Wprowadzony przedmiot nie znajduje się na żadnym obszarze. '
                                        'Czy chcesz go dodać do obszaru ' + str(
                                            areaid) + '?', self)
                                    if nowyprzedmiotok:
                                        nazwaprzedmiotu, nazwaprzedmiotuok = InputDialog.komunikat('txt',
                                                                                                   'Podaj nazwę '
                                                                                                   'nowego przedmiotu:',
                                                                                                   self)
                                        if nazwaprzedmiotuok:
                                            slotbaza.createitem(itemid, idtobarcode(itemid, 'item'), nazwaprzedmiotu,
                                                                areaid)
                                            przedmiot = slotbaza.loaditem(itemid)
                                            przedmiot['itemstate'] = True;
                                            przedmiot['dateoffirstincome'] = datetime.datetime.now()
                                            przedmiot['useroffirstincome'] = self.username
                                            przedmiot['useroflastincome'] = self.username
                                            przedmiot['dateoflastincome'] = datetime.datetime.now()
                                            slotbaza.saveitem(przedmiot)
                                            Dialog.komunikat('ok',
                                                             'Poprawnie dodano przedmiot.'
                                                             '\nPredmiot został przyjęty na stan magazynu.',
                                                             self)
                                            kolejnyprzedmiot = QuestionDialog.pytanie(
                                                'Czy chcesz przyjąć kolejny przedmiot do obszaru ' + str(areaid) + '?',
                                                self)
                                        else:
                                            Dialog.komunikat('warn',
                                                             'Przerwano proces dodawania przedmiotu. '
                                                             'Przedmiot nie został dodany.',
                                                             self)
                                        pass
                                    else:
                                        Dialog.komunikat('error',
                                                         'W takim razie albo zeskanowałeś zły kod, '
                                                         'albo coś się popsuło...\nWezwij szefa ekipy.',
                                                         self)
                            else:
                                Dialog.komunikat('warn', itemstatustxt, self)
                        else:
                            pass
                else:
                    Dialog.komunikat('warn', 'Wskazany obszar nie istnieje!\nDodaj najpierw obszar, aby móc przyjmować '
                                             'do niego przedmioty.', self)
            else:
                Dialog.komunikat('warn', areastatustxt, self)
        else:
            pass

    def comeout(self):
        areabarcode, areaok = InputDialog.komunikat('barcode', 'Wczytaj kod obszaru:', self)
        if areaok:
            areastatus, areastatustxt = barcodevalcheck(areabarcode, 'area')
            if areastatus == 0:
                areaid = barcodetoid(areabarcode, 'int')
                if slotbaza.isareaexist(areaid):
                    kolejnyprzedmiot = True
                    while kolejnyprzedmiot:
                        kolejnyprzedmiot = False
                        itembarcode, itemok = InputDialog.komunikat('barcode', 'Wczytaj kod przedmiotu:', self)
                        if itemok:
                            itemstatus, itemstatustxt = barcodevalcheck(itembarcode, 'item')
                            if itemstatus == 0:
                                itemid = barcodetoid(itembarcode, 'int')
                                if slotbaza.isitemexist(itemid):
                                    przedmiot = slotbaza.loaditem(itemid)
                                    if przedmiot['itemstate']:
                                        istniejacyprzedmiotok = QuestionDialog.pytanie(
                                            'Ten przedmiot znajduje się w bazie:\nNazwa przedmiotu: ' + przedmiot[
                                                'itemname'] + '\nStan: Przyjęty\nUwagi: ' + przedmiot[
                                                'itemcomments'] + '\n\nCzy chcesz wydać przedmiot?', self)
                                        if istniejacyprzedmiotok:
                                            przedmiot['itemstate'] = False
                                            przedmiot['dateoflastoutcome'] = datetime.datetime.now()
                                            przedmiot['useroflastoutcome'] = self.username
                                            slotbaza.saveitem(przedmiot)
                                            Dialog.komunikat('ok', 'Przedmiot został wydany z magazynu', self)
                                            kolejnyprzedmiot = QuestionDialog.pytanie(
                                                'Czy chcesz wydać kolejny przedmiot z obszaru ' + str(areaid) + '?',
                                                self)
                                        else:
                                            Dialog.komunikat('warn',
                                                             'Przerwano proces wydawania przedmiotu.'
                                                             '\nPrzedmiot nie został wydany',
                                                             self)
                                    else:
                                        Dialog.komunikat('error',
                                                         'Ten przedmiot jest już wydany z magazynu! '
                                                         'Jeśli nie wiesz dlaczego, wezwij szefa ekipy!',
                                                         self)
                                else:
                                    Dialog.komunikat('error',
                                                     'Próbujesz wydać przedmiot, który nie znajduje się w bazie! '
                                                     'Jeśli nie wiesz dlaczego, wezwij szefa ekipy!',
                                                     self)
                            else:
                                Dialog.komunikat('warn', itemstatustxt, self)
                        else:
                            pass
                else:
                    Dialog.komunikat('warn', 'Wskazany obszar nie istnieje!\nDodaj najpierw obszar, aby móc przyjmować '
                                             'do niego przedmioty.', self)
            else:
                Dialog.komunikat('warn', areastatustxt, self)
        else:
            pass

    def rysujobszary(self):
        self.wyczyscscene()
        obszary = slotbaza.getareageometries()
        font = QFont()
        font.setPixelSize(18)
        font.setBold(True)
        for obszar in obszary:
            a = self.scena.addRect(obszar['posx'], obszar['posy'], obszar['sizex'], obszar['sizey'])
            b = self.scena.addText(str(obszar['areaid']))
            b.setDefaultTextColor(Qt.white)
            b.setFont(font)
            br = b.boundingRect()
            b.setPos(obszar['posx'] + obszar['sizex'] / 2 - br.width() / 2,
                     obszar['posy'] + obszar['sizey'] / 2 - br.height() / 2)
            gradient = QLinearGradient(QPoint(obszar['posx'], obszar['posy']),
                                       QPoint(obszar['posx'], obszar['posy'] + obszar['sizey']))
            gradient.setColorAt(0, QColor('#AA0087FF'))
            gradient.setColorAt(1, QColor('#CC0048FF'))
            a.setBrush(gradient)

    def wyczyscscene(self):
        self.scena.clear()
        self.pomieszczeniedosceny()

    def pomieszczeniedosceny(self):
        # self.scena.setBackgroundBrush(Qt.darkGray)
        pomieszczenie_poly = QPolygonF(
            [QPoint(0, 100), QPoint(700, 100), QPoint(700, 0), QPoint(900, 0), QPoint(900, 100), QPoint(1000, 100),
             QPoint(1000, 850), QPoint(880, 850), QPoint(880, 950), QPoint(630, 950), QPoint(630, 850),
             QPoint(370, 850), QPoint(370, 950), QPoint(120, 950), QPoint(120, 850), QPoint(0, 850)])
        pomieszczenie = self.scena.addPolygon(pomieszczenie_poly)
        pomieszczenie.setBrush(QBrush(Qt.white))
        pen = QPen()
        pen.setWidth(4)
        pomieszczenie.setPen(pen)


if __name__ == '__main__':
    app = QApplication([])
    magazyn = Magazyn()
    sys.exit(app.exec_())
