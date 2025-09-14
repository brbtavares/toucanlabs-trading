//+------------------------------------------------------------------+
//|                                              MA_ATR_EA.mq5       |
//|  Strategy: Fast/Slow MA crossover                                 |
//|  Stops/Targets: SL/TP in Money (R$), Percent, Points, or ATR      |
//|  Entries on bar close (no repaint). One position at a time.       |
//|  © ToucanLabs - Educational use only. Not financial advice.       |
//+------------------------------------------------------------------+
#property strict

#include <Trade/Trade.mqh>
CTrade trade;

//----------------------------- Inputs: Symbol/Trading --------------------------
input double   InpLots              = 1.0;         // Lots
input bool     InpAllowLongs        = true;        // Allow Longs
input bool     InpAllowShorts       = true;        // Allow Shorts
input bool     InpAllowReverse      = true;        // Close & reverse if opposite signal
input ulong    InpMagic             = 26092025;    // Magic number

//----------------------------- Inputs: MA/ATR ----------------------------------
input ENUM_MA_METHOD      InpMAMethod   = MODE_EMA;         // MA Method
input ENUM_APPLIED_PRICE  InpPrice      = PRICE_CLOSE;      // Applied price
input int      InpFastLen             = 9;                  // Fast MA length
input int      InpSlowLen             = 21;                 // Slow MA length
input int      InpATRLen              = 14;                 // ATR length
input double   InpMinATRPct           = 0.0;                // Min ATR% to allow entry (0 = disabled)

//----------------------------- Inputs: SL/TP Modes -----------------------------
enum StopMode { SM_NONE=0, SM_MONEY=1, SM_PERCENT=2, SM_POINTS=3, SM_ATR=4 };

input StopMode InpSLMode   = SM_ATR;     // Stop Loss Mode
input StopMode InpTPMode   = SM_ATR;     // Take Profit Mode

//--- Money (account currency, e.g., BRL)
input double   InpSL_Money = 150.0;      // SL in account currency (per position)
input double   InpTP_Money = 300.0;      // TP in account currency (per position)

//--- Percent (of entry price)
input double   InpSL_Pct   = 0.5;        // SL percent (e.g., 0.5 = 0.5%)
input double   InpTP_Pct   = 1.0;        // TP percent

//--- Points (price points)
input double   InpSL_Points= 100.0;      // SL points
input double   InpTP_Points= 200.0;      // TP points

//--- ATR (multipliers)
input double   InpSL_ATR_K = 1.5;        // SL = K * ATR
input double   InpTP_ATR_K = 2.0;        // TP = K * ATR

//----------------------------- Misc/Exec ---------------------------------------
input bool     InpProcessOnClose = true; // Process only once per bar (recommended)
input bool     InpVerbose        = true; // Print diagnostics

//----------------------------- Handles/Buffers ---------------------------------
int hFast=-1, hSlow=-1, hATR=-1;
double bufFast[3], bufSlow[3], bufATR[3];
datetime lastBarTime=0;

//----------------------------- Helpers: Symbol info ----------------------------
int      g_digits;
double   g_point;
double   g_ticksize;
double   g_tickvalue; // per 1 lot, per tick

//+------------------------------------------------------------------+
//| Utility: log                                                     |
//+------------------------------------------------------------------+
void log(string s){ if(InpVerbose) Print(s); }

//+------------------------------------------------------------------+
//| Utility: new bar check                                           |
//+------------------------------------------------------------------+
bool IsNewBar()
{
   datetime t = iTime(_Symbol,_Period,0);
   if(t != lastBarTime)
   {
      lastBarTime = t;
      return true;
   }
   return false;
}

//+------------------------------------------------------------------+
//| Utility: normalize price                                         |
//+------------------------------------------------------------------+
double Np(double price){ return NormalizeDouble(price, g_digits); }

//+------------------------------------------------------------------+
//| Convert MONEY (account ccy) -> price distance                    |
//| distance_price = (money / (tickvalue * lots)) * ticksize         |
//+------------------------------------------------------------------+
double MoneyToPriceDist(double money, double lots)
{
   if(g_tickvalue<=0.0 || g_ticksize<=0.0 || lots<=0.0) return 0.0;
   double ticks = money / (g_tickvalue * lots);
   return ticks * g_ticksize;
}

//+------------------------------------------------------------------+
//| Compute distance in price units for chosen mode                  |
//+------------------------------------------------------------------+
double DistFromMode(StopMode mode, double entry_price, double atr, double lots, bool isTP)
{
   switch(mode)
   {
      case SM_MONEY:   return MoneyToPriceDist(isTP?InpTP_Money:InpSL_Money, lots);
      case SM_PERCENT: return entry_price * ((isTP?InpTP_Pct:InpSL_Pct) / 100.0);
      case SM_POINTS:  return (isTP?InpTP_Points:InpSL_Points) * g_point;
      case SM_ATR:     return atr * (isTP?InpTP_ATR_K:InpSL_ATR_K);
      default:         return 0.0; // NONE
   }
}

//+------------------------------------------------------------------+
//| Build SL/TP prices given mode & side                             |
//+------------------------------------------------------------------+
void BuildSLTP(bool isLong, double entry_price, double atr, double lots, double &sl, double &tp)
{
   sl = 0.0; tp = 0.0;

   // Distances (absolute, price units)
   double dSL = DistFromMode(InpSLMode, entry_price, atr, lots, false);
   double dTP = DistFromMode(InpTPMode, entry_price, atr, lots, true);

   // Respect broker minimum stops
   int    stops_level = (int)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double minDist     = MathMax(stops_level * g_point, 0.0);

   if(dSL>0 && dSL<minDist) dSL = minDist;
   if(dTP>0 && dTP<minDist) dTP = minDist;

   if(isLong)
   {
      if(dSL>0) sl = Np(entry_price - dSL);
      if(dTP>0) tp = Np(entry_price + dTP);
   }
   else
   {
      if(dSL>0) sl = Np(entry_price + dSL);
      if(dTP>0) tp = Np(entry_price - dTP);
   }
}

//+------------------------------------------------------------------+
//| Init                                                             |
//+------------------------------------------------------------------+
int OnInit()
{
   g_digits   = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   g_point    = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   g_ticksize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   g_tickvalue= SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);

   hFast = iMA(_Symbol, _Period, InpFastLen, 0, InpMAMethod, InpPrice);
   hSlow = iMA(_Symbol, _Period, InpSlowLen, 0, InpMAMethod, InpPrice);
   hATR  = iATR(_Symbol, _Period, InpATRLen);

   if(hFast==INVALID_HANDLE || hSlow==INVALID_HANDLE || hATR==INVALID_HANDLE)
   {
      Print("Handle error: hFast=",hFast," hSlow=",hSlow," hATR=",hATR);
      return(INIT_FAILED);
   }

   trade.SetExpertMagicNumber(InpMagic);
   log(StringFormat("Init: point=%.10f ticksize=%.10f tickvalue=%.2f digits=%d",
                    g_point, g_ticksize, g_tickvalue, g_digits));
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Deinit                                                           |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(hFast!=INVALID_HANDLE) IndicatorRelease(hFast);
   if(hSlow!=INVALID_HANDLE) IndicatorRelease(hSlow);
   if(hATR !=INVALID_HANDLE) IndicatorRelease(hATR);
}

//+------------------------------------------------------------------+
//| Tick                                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   if(InpProcessOnClose && !IsNewBar()) return;

   // Pull 3 bars to read [1] and [2]
   if(CopyBuffer(hFast,0,0,3,bufFast)<3) return;
   if(CopyBuffer(hSlow,0,0,3,bufSlow)<3) return;
   if(CopyBuffer(hATR, 0,0,3,bufATR) <3) return;

   double fast1 = bufFast[1], fast2 = bufFast[2];
   double slow1 = bufSlow[1], slow2 = bufSlow[2];
   double atr1  = bufATR[1];

   // Optional ATR% filter for entries
   double close1 = iClose(_Symbol,_Period,1);
   double atrPct = (close1>0 ? (atr1/close1*100.0) : 0.0);
   bool   volOK  = (InpMinATRPct<=0.0) || (atrPct >= InpMinATRPct);

   bool crossUp   = (fast1>slow1 && fast2<=slow2);
   bool crossDown = (fast1<slow1 && fast2>=slow2);

   // Current book
   double ask=0, bid=0;
   if(!SymbolInfoDouble(_Symbol, SYMBOL_ASK, ask)) ask=NormalizeDouble( SymbolInfoDouble(_Symbol,SYMBOL_BID) + 2*g_point, g_digits);
   if(!SymbolInfoDouble(_Symbol, SYMBOL_BID, bid)) bid=NormalizeDouble( SymbolInfoDouble(_Symbol,SYMBOL_ASK) - 2*g_point, g_digits);

   // Position state
   bool hasPos = PositionSelect(_Symbol);
   long posType = hasPos ? PositionGetInteger(POSITION_TYPE) : -1; // POSITION_TYPE_BUY/SELL
   double posPrice = hasPos ? PositionGetDouble(POSITION_PRICE_OPEN) : 0.0;

   //--- Entry/Reverse logic
   if(volOK)
   {
      // Short Entry
      if(crossDown && InpAllowShorts)
      {
         if(hasPos)
         {
            if(posType==POSITION_TYPE_BUY && InpAllowReverse)
            {
               trade.PositionClose(_Symbol);
               hasPos=false;
            }
         }
         if(!hasPos)
         {
            double sl=0,tp=0;
            BuildSLTP(false /*short*/, bid, atr1, InpLots, sl, tp);
            trade.Sell(InpLots, _Symbol, bid, sl, tp, "MAxATR Short");
            if(InpVerbose) log(StringFormat("Sell @ %.5f SL=%.5f TP=%.5f (ATR%%=%.2f)", bid, sl, tp, atrPct));
            return;
         }
      }

      // Long Entry
      if(crossUp && InpAllowLongs)
      {
         if(hasPos)
         {
            if(posType==POSITION_TYPE_SELL && InpAllowReverse)
            {
               trade.PositionClose(_Symbol);
               hasPos=false;
            }
         }
         if(!hasPos)
         {
            double sl=0,tp=0;
            BuildSLTP(true /*long*/, ask, atr1, InpLots, sl, tp);
            trade.Buy(InpLots, _Symbol, ask, sl, tp, "MAxATR Long");
            if(InpVerbose) log(StringFormat("Buy  @ %.5f SL=%.5f TP=%.5f (ATR%%=%.2f)", ask, sl, tp, atrPct));
            return;
         }
      }
   }

   //--- (Optional) Manage nothing else; SL/TP handled by server
}
