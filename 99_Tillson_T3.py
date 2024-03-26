#!pip install yfinance yapılmalı
import pandas as pd
import pandas_ta as ta
import ssl
from urllib import request
import yfinance as yf
import matplotlib.pyplot as plt
import mplcyberpunk
import vectorbt as vbt

def Hisse_Temel_Veriler():
    url1="https://www.isyatirim.com.tr/tr-tr/analiz/hisse/Sayfalar/Temel-Degerler-Ve-Oranlar.aspx#page-1"
    context = ssl._create_unverified_context()
    response = request.urlopen(url1, context=context)
    url1 = response.read()

    df = pd.read_html(url1,decimal=',', thousands='.')                         #Tüm Hisselerin Tablolarını Aktar
    df2=df[6]
    return df2

def TillsonT3(data,Length=21,vf=0.618):
    Tillson=data.copy()
    
    ema_first_input = (Tillson['High'] + Tillson['Low'] + 2 * Tillson['Adj Close']) / 4
    e1 = ta.ema(ema_first_input, Length)
    e2 = ta.ema(e1, Length)
    e3 = ta.ema(e2, Length)
    e4 = ta.ema(e3, Length)
    e5 = ta.ema(e4, Length)
    e6 = ta.ema(e5, Length)

    c1 = -1 * vf * vf * vf
    c2 = 3 * vf * vf + 3 * vf * vf * vf
    c3 = -6 * vf * vf - 3 * vf - 3 * vf * vf * vf
    c4 = 1 + 3 * vf + vf * vf * vf + 3 * vf * vf
    Tillson['TillsonT3'] = c1 * e6 + c2 * e5 + c3 * e4 + c4 * e3
    Tillson = Tillson.dropna()
    Tillson = Tillson.reset_index()
    Tillson['Entry']=False
    Tillson['Exit']=False
    for i in range(1, len(Tillson)):
        if Tillson.loc[i,'TillsonT3']>Tillson.loc[i-1,'TillsonT3']:
            Tillson.loc[i,'Entry']=True
        if Tillson.loc[i,'TillsonT3']<Tillson.loc[i-1,'TillsonT3']:
            Tillson.loc[i,'Exit']=True            
    return Tillson

Hisse_Ozet=Hisse_Temel_Veriler()
Hisseler=Hisse_Ozet['Kod'].values.tolist()

Titles=['Hisse Adı','Kazanma Oranı[%]','Sharpe Oranı','Ort. Kazanma Oranı [%]','Ort Kazanma Süresi','Ort. Kayıp Oranı [%]','Ort Kayıp Süresi','Giriş Sinyali','Çıkış Sinyali']
df_signals=pd.DataFrame(columns=Titles)

for i in range(0,len(Hisseler)):
    print(Hisseler[i])
    try:
        L=8
        v = 0.7
        data=yf.download(Hisseler[i]+'.IS',period='2y', interval='1d',progress=False)
        Tillson=TillsonT3(data,Length=L,vf=v)
        psettings = {'init_cash': 100,'freq': 'H', 'direction': 'longonly', 'accumulate': True}
        pf = vbt.Portfolio.from_signals(Tillson['Adj Close'], entries=Tillson['Entry'], exits=Tillson['Exit'],**psettings)
        Stats=pf.stats()

        Buy=False
        Sell=False
        Signals = Tillson.tail(1)
        Signals = Signals.reset_index()
        all_entry = Signals['Entry'].all()
        all_exit = Signals['Exit'].all()

        Buy = all_entry
        Sell = all_exit

        L1=[Hisseler[i],round(Stats.loc['Win Rate [%]'],2),round(Stats.loc['Sharpe Ratio'],2),
            round(Stats.loc['Avg Winning Trade [%]'],2),str(Stats.loc['Avg Winning Trade Duration']),
            round(Stats.loc['Avg Losing Trade [%]'],2),str(Stats.loc['Avg Losing Trade Duration']),
            str(Buy),str(Sell)]
        
        print(L1)
        df_signals.loc[len(df_signals)] = L1
        
        if Buy==True:
            pf.plot(subplots = ['orders','trades','drawdowns','trade_pnl','cum_returns']).write_image((Hisseler[i]+"_Backtest.png"))
    except:
        pass

df_True = df_signals[(df_signals['Entry'] == 'True')]
print(df_True)