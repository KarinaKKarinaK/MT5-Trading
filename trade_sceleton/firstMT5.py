import warnings
from datetime import datetime
import pandas as pd
import MetaTrader5 as mt5

warnings.filterwarnings("ignore")
mt5.initialize()
login = 5002528742
password = "rrh4ddlp"
server = "MetaQuotes-Demo"

mt5.login(login, password, server)

account_info = mt5.account_info()
print(account_info)

login_number = account_info.login
balance = account_info.balance
equity = account_info.equity

print()
print('login: ', login_number)
print('balance: ', balance)
print('equity: ', equity)

class MT5:

    def get_data(symbol, n, timeframe=mt5.TIMEFRAME_D1):
        """Function to import te data of the chosen symbol"""

        #Initialize the connection if teher is not
        mt5.initialize()

        #Current date extract
        utc_from = datetime.now()

        #Import the data into a touple
        rates = mt5.copy_rates_from(symbol, timeframe, utc_from, n)

        #Touple to dataframe
        rates_frame = pd.DataFrame(rates)

        #Convert time in seconds into teh datetime format
        rates_frame['time'] = pd.to_datetime(rates_frame['time'], unit='s')

        #Convert the column 'time' in the right format
        rates_frame['time'] = pd.to_datetime(rates_frame['time'], format='%Y-%m-%d')

        #Set column time as the index of teh dataframe
        rates_frame = rates_frame.set_index('time')
        return rates_frame

    def orders(symbol, lot, buy=True, id_position=None):
        """Send teh orders"""

        #Initialize the connection if there is not
        if mt5.initialize() == False:
            mt5.initialize()
        
        #Get filling mode
        filling_mode = mt5.symbol_info(symbol).filling_mode - 1

        #Take ask price
        ask_price = mt5.symbol_info_tick(symbol).ask

        #Take bid price
        bid_price = mt5.symbol_info_tick(symbol).bid

        #Take the point of the asset
        point = mt5.symbol_info(symbol).point

        deviation = 20 #mt5.getSlippage(symbol)

        #**************************Open a trade*******************************************
        if id_position == None:

            #Buy order parameters
            if buy:
                type_trade = mt5.ORDER_TYPE_BUY
                sl = ask_price*(1-0.01)
                tp = ask_price*(1+0.01)
                price = ask_price

            #Sell order parameters
            else:
                type_trade = mt5.ORDER_TYPE_SELL
                sl = bid_price*(1+0.01)
                tp = bid_price*(1-0.01)
                price = bid_price

            #Open the trade
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot,
                "type": type_trade,
                "price": price,
                "deviation": deviation,
                "sl": sl,
                "tp": tp,
                "magic": 234000,
                "comment": "python script order",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": filling_mode,
            }

            #Send a trading request
            result = mt5.order_send(request)
            result_comment = result.comment


        #********************Close a trade*******************************
        else:
            #Buy order Parameters
            if buy:
                type_trade = mt5.ORDER_TYPE_SELL
                price = bid_price
            
            #Sell order parameters
            else:
                type_trade = mt5.ORDER_TYPE_BUY
                price = ask_price

            #Close the trade
            request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": type_trade,
            "position": id_position,
            "price": price,
            "deviation": deviation,
            "magic": 234000,
            "comment": "python script order",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling_mode,
            }

            #Send a trading request
            result = mt5.order_send(request)
            result_comment = result.comment

        return result.comment

    def resume():
        """Return the current positions. Position = 0 --> Buy """
        #Initizalize the connection if theere is not
        mt5.initialize()

        #Define the name of teh columns that we will create
        colonnes = ["ticket", "position", "symbol", "volume"]

        current = mt5.positions_get()

        summary = pd.DataFrame()

        #Loop to add each row in dataframe
        #(Can be amiliorate using of list of list.)
        for element in current: 
            element_pandas = pd.Dataframe([element.ticket,  element.type, element.symbol, element.volume], index=colonnes).transpose()
            summary = pd.concat((summary, element_pandas), axis = 0)

        return summary

    def run(symbol, long, short, lot):
        #Initialize the connection if there is not 
        if mt5.initialize() == False:
            mt5.initialize()
        
        #*****************************Chose a symbol**********************
        print("--------------------------------------------------------------------")
        print("Date: ", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("SYMBOL: ", symbol)

        #Initialize the device
        current_open_positions = MT5.resume()

        #Buy or sell
        print(f"BUY: {long} \t SHORT: {short}")

        """Close trade eventually"""
        #Extraction type trade
        try:
            position = current_open_positions.loc[current_open_positions["symbol"]==symbol].values[0][1]
            identifier = current_open_positions.loc[current_open_positions["symbol"]==symbol].values[0][0]

        except:
            position = None
            identifier = None

        print(f"POSITION: {position} \t ID: {identifier}")

        #Close trades
        if long==True and position==0:
            long=False

        elif long==False and position==0:
            res = MT5.orders(symbol, lot, buy=True, id_position=identifier)
            print(f"CLOSE LONG TRADE: {res}")

        elif short==True and position == 1:
            short = False
        
        elif short == False and position == 1:
            res = MT5.orders(symbol, lot, buy=False, id_position=identifier)
            print(f"CLOSE SHORT TRADE: {res}")

        else:
            pass

        """Buy or short"""
        if long ==True:

            res = MT5.orders(symbol, lot, buy=True, id_position=None)
            print(f"OPEN LONG TRADE: {res}")

        if short ==True:

            res = MT5.orders(symbol, lot, buy=False, id_position=None)
            print(f"OPEN SHORT TRADE: {res}")

        
        print("___________________________________________________________________________________")

    def close_all_night():
        result = MT5.resume()
        for i in range(len(result)):
            before = mt5.account_info().balance
            row = result.iloc[0+i:1+i, :]
            if row["position"][0]==0:
                res = MT5.orders(row["symbol"][0], row["volume"][0], buy=True, id_position=row["ticket"][0])

            else:
                res = MT5.orders(row["symbol"][0], row["volume"][0], buy=False, id_position=row["ticket"][0])
