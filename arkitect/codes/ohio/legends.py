"""The words a Columbus set puts beside a symbol.

These were inside arkitect/lib/symbols/, which meant the engine named Ohio and NEC sections it
could not possibly know applied. The drawing of a smoke alarm is the same everywhere;
the sentence next to it is not.
"""

# Device legend, E-101 and E-102. Kind to the description printed beside its symbol.
DEVICE_KINDS = {
    'dup':    'DUPLEX RECEPTACLE, 120 V, 20 A',
    'gfci':   'DUPLEX RECEPTACLE, GFCI PROTECTED (AT THE DEVICE OR ITS BREAKER)',
    'wp':     'EXTERIOR RECEPTACLE, WEATHER RESISTANT, GFCI, IN-USE COVER, NEC 406.9',
    'range':  'RANGE RECEPTACLE, 50 A 240 V',
    'dryer':  'DRYER RECEPTACLE, 30 A 240 V',
    'dw':     'DISHWASHER RECEPTACLE, INDIVIDUAL CIRCUIT',
    'fridge': 'REFRIGERATOR RECEPTACLE, INDIVIDUAL CIRCUIT',
    'wh':     'WATER HEATER, 30 A 2-POLE INDIVIDUAL CIRCUIT',
    'head':   'HEAT-PUMP INDOOR WALL HEAD, ON THE HEAT-PUMP CIRCUIT',
    'ahu':    'HEAT-PUMP AIR HANDLER, CONCEALED IN A SOFFIT, ON THE HEAT-PUMP CIRCUIT',
    'tstat':  'THERMOSTAT OR WALL CONTROL, 48" TO THE TOP; LOW VOLTAGE TO ITS UNIT',
    'sw':     'SINGLE-POLE SWITCH; THE LETTER IS WHAT IT CONTROLS',
    'sw3':    'THREE-WAY SWITCH',
    'lt':     'SURFACE LUMINAIRE, CEILING',
    'rec':    'RECESSED LUMINAIRE',
    'fanc':   'BATH FAN, CONTINUOUS DUTY; ITS SWITCH BOOSTS IT — M-101 NOTE 4',
    'fan':    'BATH EXHAUST FAN, SWITCHED',
    'ext':    'EXTERIOR WALL LUMINAIRE',
    'sd':     'SMOKE ALARM, HARDWIRED, INTERCONNECTED, BATTERY BACKUP — RCO 314',
    'co':     'CARBON MONOXIDE ALARM, HARDWIRED, INTERCONNECTED — RCO 315',
    'panel':  'PANELBOARD — SEE THE SCHEDULE',
    'jbox':   'JUNCTION BOX, 120 V, FOR FUTURE EQUIPMENT AS NOTED',
}

# The two caption lines a clearance rectangle carries on a plan.
CLEARANCE_CAPTIONS = {
    'clear':   ('36" PANEL CLR', 'NEC 110.26(A)'),
    'whclear': ('30" x 30" WH CLR', 'RCO M1305.1'),
}
