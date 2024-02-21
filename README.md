# bbk_quant

The version 0.1.1 is  trend based quant trading model:
* Signal: using 30 day return as momentum
* Risk: 30 day positive/negative 90th percentile loss for position sizing
* Exit: using drawdown for passive profit taking
* Other features: support both long/short, use daily data (no intreday trading),

# to run it: 
* Poetry Install
* use main.ipynb

# Code Components:
* Book, Order, Alpha, Risk, Performance

# Future work:
* Statistical Arb
* Mean reversion
